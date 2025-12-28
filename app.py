from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

import base64
import os
import httpx
import re
import io

try:
    from PIL import Image
except Exception:  # Pillow not installed
    Image = None

from database import get_db, init_db
from models import User, Consultation, MedicalHistory, Doctor, Hospital, NGO, PriorityLevel
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)

app = FastAPI(title="WeCare - Medical Assistant")

# Allow requests from any origin (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:2b")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)


# Pydantic schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class ConsultationRequest(BaseModel):
    symptoms: str
    use_history: bool = True


class SyncConsultation(BaseModel):
    symptoms: str
    ai_response: str
    priority: str
    first_aid_suggestions: str
    recommended_specialization: Optional[str] = None
    created_at: str
    use_history: bool = True


# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return FileResponse("index.html")


@app.get("/manifest.json")
def manifest():
    return FileResponse("manifest.json")


@app.get("/service-worker.js")
def service_worker():
    return FileResponse("service-worker.js")


@app.post("/api/auth/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@app.post("/api/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "blood_group": current_user.blood_group
    }


def analyze_priority(symptoms: str, ai_response: str) -> PriorityLevel:
    """Analyze symptoms and AI response to determine priority"""
    critical_keywords = [
        "chest pain", "heart attack", "stroke", "severe bleeding", "unconscious",
        "breathing difficulty", "severe pain", "emergency", "critical", "urgent care needed"
    ]
    high_keywords = [
        "high fever", "severe", "infection", "fracture", "injury", "wound",
        "urgent", "immediate", "consult immediately"
    ]
    medium_keywords = [
        "fever", "pain", "rash", "cough", "headache", "medical attention"
    ]
    
    text = (symptoms + " " + ai_response).lower()
    
    for keyword in critical_keywords:
        if keyword in text:
            return PriorityLevel.CRITICAL
    
    for keyword in high_keywords:
        if keyword in text:
            return PriorityLevel.HIGH
    
    for keyword in medium_keywords:
        if keyword in text:
            return PriorityLevel.MEDIUM
    
    return PriorityLevel.LOW


def extract_specialization(ai_response: str) -> Optional[str]:
    """Extract recommended doctor specialization from AI response"""
    specializations = [
        "General Medicine", "Pediatrics", "Gynecology", "Dermatology",
        "Cardiology", "Orthopedics", "ENT", "Neurology", "Gastroenterology"
    ]
    
    text = ai_response.lower()
    for spec in specializations:
        if spec.lower() in text:
            return spec
    
    return None


@app.post("/api/consultation")
async def create_consultation(
    symptoms: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    use_history: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main consultation endpoint - works with or without image"""

    symptoms_text = (symptoms or "").strip()
    if not symptoms_text and image is None:
        raise HTTPException(status_code=400, detail="Provide symptoms text or upload an image")
    
    # Build context with medical history if enabled
    context = ""
    if use_history:
        histories = db.query(MedicalHistory).filter(
            MedicalHistory.user_id == current_user.id
        ).all()
        if histories:
            context = "Patient's medical history:\n"
            for h in histories:
                context += f"- {h.condition}"
                if h.is_chronic:
                    context += " (chronic)"
                context += "\n"
            context += "\n"
    
    # Prepare AI prompt (support text-only, image-only, or both)
    if symptoms_text:
        user_part = f"Patient query: {symptoms_text}\n"
    else:
        user_part = "Patient provided an image. Analyze the image for any visible medical issue and give advice.\n"

    prompt = f"""You are Dr. WeCare, an experienced medical doctor specializing in primary care and emergency medicine in rural Bangladesh. You have 15 years of experience treating patients with limited access to healthcare facilities.

IMPORTANT: You ONLY provide medical and healthcare advice. If the patient's query is not related to health, medicine, symptoms, or medical concerns, politely respond: "I'm Dr. WeCare, a medical assistant. I can only help with health-related questions. Please describe your medical symptoms or health concerns, and I'll be happy to assist you."

{context}{user_part}

Provide a CONCISE response (maximum 300 words) with these sections:

**1. Quick Assessment**
- Brief diagnosis and severity (1-2 sentences)
- Is it urgent/emergency? (Yes/No with brief reason)

**2. First Aid - What To Do NOW (Before Doctor/Hospital)**
- 3-4 immediate steps the patient can take at home
- Keep it simple and practical

**3. When to See a Doctor**
- Should they go? (Yes/No/Maybe)
- What type of doctor/specialist?
- Warning signs that need immediate attention

**4. Prevention Tips**
- 2-3 quick preventive measures

Keep responses SHORT, practical, and compassionate. Focus on immediate actionable advice. End with a brief encouraging note from Dr. WeCare."""

    # Call Ollama
    image_path = None
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    
    if image:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")

        # Normalize to PNG so Ollama gets a known format.
        if Image is None:
            raise HTTPException(
                status_code=503,
                detail="Image upload support is not installed on the server (missing Pillow). Install Pillow or submit text-only.",
            )
        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                im = im.convert("RGB")
                out = io.BytesIO()
                im.save(out, format="PNG")
                normalized_bytes = out.getvalue()
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Unsupported image format. Please upload a PNG or JPG image.",
            ) from exc

        image_b64 = base64.b64encode(normalized_bytes).decode("utf-8")
        payload["images"] = [image_b64]

        # Save image (normalized)
        filename = f"{current_user.id}_{datetime.utcnow().timestamp()}.png"
        image_path = os.path.join(UPLOAD_DIR, filename)
        with open(image_path, "wb") as f:
            f.write(normalized_bytes)
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            res = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama at {OLLAMA_HOST}. Is 'ollama serve' running?",
        ) from exc
    
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    
    data = res.json()
    ai_response = data.get("response", "")
    
    # Analyze priority and extract specialization
    priority = analyze_priority(symptoms, ai_response)
    specialization = extract_specialization(ai_response)
    
    # Extract first aid from response (simple heuristic)
    first_aid = ""
    if "first aid" in ai_response.lower():
        parts = ai_response.split("First aid")
        if len(parts) > 1:
            first_aid = "First aid" + parts[1].split("\n\n")[0]
    
    # Save consultation
    consultation = Consultation(
        user_id=current_user.id,
        symptoms=symptoms_text,
        image_path=image_path,
        ai_response=ai_response,
        priority=priority,
        first_aid_suggestions=first_aid,
        recommended_specialization=specialization,
        use_history=use_history,
        is_synced=True
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    
    # Get recommended doctors
    doctors = []
    if specialization:
        doctors = db.query(Doctor).filter(
            Doctor.specialization == specialization
        ).limit(3).all()
    
    if not doctors:
        doctors = db.query(Doctor).filter(
            Doctor.specialization == "General Medicine"
        ).limit(3).all()
    
    return {
        "consultation_id": consultation.id,
        "ai_response": ai_response,
        "priority": priority.value,
        "first_aid_suggestions": first_aid,
        "recommended_specialization": specialization,
        "recommended_doctors": [
            {
                "id": d.id,
                "name": d.name,
                "specialization": d.specialization,
                "hospital": d.hospital,
                "phone": d.phone,
                "available_days": d.available_days,
                "fee": d.fee,
                "address": d.address
            }
            for d in doctors
        ]
    }


@app.post("/api/sync/consultations")
def sync_consultations(
    consultations: list[SyncConsultation],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync offline consultations to database"""
    synced_count = 0
    for consult_data in consultations:
        consultation = Consultation(
            user_id=current_user.id,
            symptoms=consult_data.symptoms,
            ai_response=consult_data.ai_response,
            priority=PriorityLevel[consult_data.priority.upper()],
            first_aid_suggestions=consult_data.first_aid_suggestions,
            recommended_specialization=consult_data.recommended_specialization,
            use_history=consult_data.use_history,
            is_synced=True,
            created_offline=True,
            created_at=datetime.fromisoformat(consult_data.created_at)
        )
        db.add(consultation)
        synced_count += 1
    
    db.commit()
    return {"synced": synced_count}


@app.get("/api/doctors")
def get_doctors(
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization == specialization)
    doctors = query.all()
    return {"doctors": doctors}


@app.get("/api/hospitals")
def get_hospitals(db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).all()
    return {"hospitals": hospitals}


@app.get("/api/ngos")
def get_ngos(db: Session = Depends(get_db)):
    ngos = db.query(NGO).all()
    return {"ngos": ngos}


@app.get("/api/consultations/history")
def get_consultation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultations = db.query(Consultation).filter(
        Consultation.user_id == current_user.id
    ).order_by(Consultation.created_at.desc()).limit(20).all()
    
    return {
        "consultations": [
            {
                "id": c.id,
                "symptoms": c.symptoms,
                "ai_response": c.ai_response,
                "priority": c.priority.value,
                "created_at": c.created_at.isoformat()
            }
            for c in consultations
        ]
    }
