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
from models import User, Consultation, MedicalHistory, Doctor, Hospital, NGO, PriorityLevel, ConsultationStatus
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)


def detect_language(text: str) -> str:
    """Detect whether user text is Bengali or English.

    Returns:
        "bn" for Bengali, "en" otherwise.
    """
    s = (text or "").strip()
    if not s:
        return "en"

    bengali_chars = len(re.findall(r"[\u0980-\u09FF]", s))
    latin_chars = len(re.findall(r"[A-Za-z]", s))

    # If Bengali script is present and is not trivially small, treat as Bengali.
    if bengali_chars >= 3 and bengali_chars >= latin_chars:
        return "bn"
    return "en"


def bengali_ratio(text: str) -> float:
    s = text or ""
    bn = len(re.findall(r"[\u0980-\u09FF]", s))
    total_letters = bn + len(re.findall(r"[A-Za-z]", s))
    return (bn / total_letters) if total_letters else 0.0


BN_SPECIALIZATION_TO_EN = {
    "সাধারণ চিকিৎসা": "General Medicine",
    "শিশুরোগ": "Pediatrics",
    "স্ত্রীরোগ": "Gynecology",
    "চর্মরোগ": "Dermatology",
    "হৃদরোগ": "Cardiology",
    "অর্থোপেডিক্স": "Orthopedics",
    "কান-নাক-গলা": "ENT",
    "স্নায়ুরোগ": "Neurology",
    "গ্যাস্ট্রোএন্টারোলজি": "Gastroenterology",
}

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
    blood_group: Optional[str] = None

    def validate_blood_group(self):
        if self.blood_group:
            valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if self.blood_group not in valid_groups:
                raise ValueError(f"Invalid blood group. Must be one of: {', '.join(valid_groups)}")


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
    return FileResponse("landing.html")


@app.get("/app")
def app_page():
    return FileResponse("index.html")


@app.get("/index.html")
def index_page():
    return FileResponse("index.html")


@app.get("/admin.html")
def admin_page():
    return FileResponse("admin.html")


@app.get("/landing.html")
def landing_page():
    return FileResponse("landing.html")


@app.get("/manifest.json")
def manifest():
    return FileResponse("manifest.json")


@app.get("/service-worker.js")
def service_worker():
    return FileResponse("service-worker.js")


@app.post("/api/auth/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Validate blood group
    try:
        user_data.validate_blood_group()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
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
        blood_group=user_data.blood_group,
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
    critical_keywords_bn = [
        "বুকে ব্যথা", "হার্ট অ্যাটাক", "স্ট্রোক", "অতিরিক্ত রক্তপাত", "অজ্ঞান",
        "শ্বাসকষ্ট", "তীব্র ব্যথা", "জরুরি", "ইমার্জেন্সি"
    ]
    high_keywords = [
        "high fever", "severe", "infection", "fracture", "injury", "wound",
        "urgent", "immediate", "consult immediately"
    ]
    high_keywords_bn = [
        "উচ্চ জ্বর", "তীব্র", "সংক্রমণ", "হাড় ভাঙা", "আঘাত", "ক্ষত",
        "দ্রুত", "অবিলম্বে", "তাৎক্ষণিক"
    ]
    medium_keywords = [
        "fever", "pain", "rash", "cough", "headache", "medical attention"
    ]
    medium_keywords_bn = [
        "জ্বর", "ব্যথা", "র‍্যাশ", "কাশি", "মাথাব্যথা", "ডাক্তার"
    ]
    
    text = (symptoms + " " + ai_response).lower()
    
    for keyword in critical_keywords:
        if keyword in text:
            return PriorityLevel.CRITICAL

    for keyword in critical_keywords_bn:
        if keyword in text:
            return PriorityLevel.CRITICAL
    
    for keyword in high_keywords:
        if keyword in text:
            return PriorityLevel.HIGH

    for keyword in high_keywords_bn:
        if keyword in text:
            return PriorityLevel.HIGH
    
    for keyword in medium_keywords:
        if keyword in text:
            return PriorityLevel.MEDIUM

    for keyword in medium_keywords_bn:
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

    # Bengali labels → English DB values
    for bn_label, en_value in BN_SPECIALIZATION_TO_EN.items():
        if bn_label in ai_response:
            return en_value
    
    return None

def build_consultation_prompt(*, language: str, context: str, conversation_history: str, user_part: str) -> str:
    if language == "bn":
        specialization_choices_bn = " / ".join(BN_SPECIALIZATION_TO_EN.keys())
        return f"""আপনি ডা. উইকেয়ার, বাংলাদেশের গ্রামীণ এলাকায় প্রাথমিক চিকিৎসা ও জরুরি চিকিৎসায় অভিজ্ঞ একজন চিকিৎসক।

ভাষা নির্দেশনা (অত্যন্ত গুরুত্বপূর্ণ): আপনার উত্তর ১০০% বাংলা ভাষায় হবে। কোনো ইংরেজি বাক্য/শব্দ ব্যবহার করবেন না।

গুরুত্বপূর্ণ: আপনি শুধুমাত্র স্বাস্থ্য ও চিকিৎসা সংক্রান্ত পরামর্শ দেবেন। প্রশ্নটি যদি স্বাস্থ্য/লক্ষণ/চিকিৎসা সম্পর্কিত না হয়, তাহলে বিনয়ের সাথে ঠিক এই বাক্যটি লিখবেন:
"আমি ডা. উইকেয়ার, একজন মেডিকেল সহায়ক। আমি শুধুমাত্র স্বাস্থ্য সংক্রান্ত প্রশ্নে সাহায্য করতে পারি। অনুগ্রহ করে আপনার চিকিৎসা লক্ষণ বা স্বাস্থ্য উদ্বেগ বর্ণনা করুন, এবং আমি আপনাকে সাহায্য করতে পেরে খুশি হব।"

{context}{conversation_history}{user_part}

সর্বোচ্চ ৩০০ শব্দে সংক্ষিপ্ত উত্তর দিন এবং নিচের শিরোনামগুলো ঠিক রেখে লিখুন:

**1. দ্রুত মূল্যায়ন**
- সম্ভাব্য সমস্যা ও তীব্রতা (১-২ বাক্য)
- জরুরি/ইমার্জেন্সি কি? (হ্যাঁ/না + ছোট কারণ)

**2. প্রাথমিক চিকিৎসা — এখনই কী করবেন (ডাক্তার/হাসপাতালে যাওয়ার আগে)**
- বাড়িতে করা যায় এমন ৩-৪টি সহজ পদক্ষেপ

**3. কখন ডাক্তার দেখাবেন**
- যেতে হবে কি? (হ্যাঁ/না/সম্ভবত)
- কোন ধরণের ডাক্তার/বিশেষজ্ঞ লাগতে পারে? (শুধু এই তালিকা থেকে ১টি বেছে লিখুন: {specialization_choices_bn})
- কোন সতর্ক লক্ষণ হলে সাথে সাথে হাসপাতালে যেতে হবে

**4. প্রতিরোধের পরামর্শ**
- ২-৩টি সংক্ষিপ্ত পরামর্শ

শেষে ডা. উইকেয়ারের পক্ষ থেকে ১ লাইনের আশ্বস্তকারী কথা লিখুন।"""

    return f"""You are Dr. WeCare, an experienced medical doctor specializing in primary care and emergency medicine in rural Bangladesh. You have 15 years of experience treating patients with limited access to healthcare facilities.

CRITICAL LANGUAGE INSTRUCTION: Your answer must be 100% English. Do not use Bengali.

IMPORTANT: You ONLY provide medical and healthcare advice. If the patient's query is not related to health, medicine, symptoms, or medical concerns, politely respond with exactly:
"I'm Dr. WeCare, a medical assistant. I can only help with health-related questions. Please describe your medical symptoms or health concerns, and I'll be happy to assist you."

{context}{conversation_history}{user_part}

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


async def generate_summary(full_response: str, *, language: str) -> str:
    """Generate a concise summary of the AI response using Ollama in the same language."""
    if language == "bn":
        summary_prompt = f"""নিচের চিকিৎসা পরামর্শটি ২-৩টি বাক্যে সংক্ষেপ করুন।
শুধু রোগের ধারণা/জরুরি অবস্থা/করণীয়—এই মূল তথ্যগুলো রাখুন।

মূল উত্তর:
{full_response}

শুধু সারসংক্ষেপ লিখুন, অতিরিক্ত কিছু নয়।"""
    else:
        summary_prompt = f"""Summarize the following medical consultation response in 2-3 sentences.
Keep only the most critical information about diagnosis, urgency, and recommended action.

Original response:
{full_response}

Provide ONLY the summary, no additional text:"""
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": summary_prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            res = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            summary = data.get("response", "").strip()
            
            # Limit summary length
            if len(summary) > 500:
                summary = summary[:497] + "..."
            
            return summary if summary else full_response[:200] + "..."
    except Exception as e:
        print(f"Summary generation failed: {e}")
        # Fallback: return first 200 chars
        return full_response[:200] + "..."


async def enforce_response_language(*, expected_language: str, user_text: str, response_text: str) -> str:
    """If model responded in the wrong language, ask it once to rewrite in the expected language."""
    if not response_text:
        return response_text

    bn_r = bengali_ratio(response_text)
    looks_bengali = bn_r >= 0.2
    if expected_language == "bn" and looks_bengali:
        return response_text
    if expected_language == "en" and not looks_bengali:
        return response_text

    if expected_language == "bn":
        rewrite_prompt = f"""আপনার আগের উত্তরটি পুরোপুরি বাংলায় আবার লিখুন। কোনো ইংরেজি শব্দ/বাক্য ব্যবহার করবেন না। অর্থ ও চিকিৎসা পরামর্শ যেন একই থাকে।

রোগীর প্রশ্ন:
{user_text}

আগের উত্তর:
{response_text}

শুধু সংশোধিত বাংলা উত্তর লিখুন।"""
    else:
        rewrite_prompt = f"""Rewrite your previous answer entirely in English. Do not use Bengali. Keep the medical meaning and advice the same.

User question:
{user_text}

Previous answer:
{response_text}

Provide ONLY the rewritten English answer."""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": rewrite_prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            res = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            rewritten = (data.get("response", "") or "").strip()
            return rewritten if rewritten else response_text
    except Exception:
        return response_text

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
    language = detect_language(symptoms_text) if symptoms_text else "bn"  # Bangladesh default for image-only
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
    
    # Add conversation context from last k consultations
    k = 5  # Number of previous consultations to include as context
    previous_consultations = db.query(Consultation).filter(
        Consultation.user_id == current_user.id
    ).order_by(Consultation.created_at.desc()).limit(k).all()
    
    conversation_history = ""
    if previous_consultations:
        conversation_history = "Previous conversation history (for context):\n\n"
        for i, prev in enumerate(reversed(previous_consultations), 1):
            conversation_history += f"[Session {i}]\n"
            conversation_history += f"Patient: {prev.symptoms}\n"
            conversation_history += f"Dr. WeCare: {prev.ai_response[:200]}...\n\n"
        conversation_history += "---\n\n"
    
    # Prepare AI prompt (support text-only, image-only, or both)
    if symptoms_text:
        user_part = f"Patient query: {symptoms_text}\n"
    else:
        user_part = "Patient provided an image. Analyze the image for any visible medical issue and give advice.\n"

    prompt = build_consultation_prompt(
        language=language,
        context=context,
        conversation_history=conversation_history,
        user_part=user_part,
    )

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
    ai_response = (data.get("response", "") or "").strip()

    # If model disobeys language instruction, rewrite once.
    ai_response = await enforce_response_language(
        expected_language=language,
        user_text=symptoms_text or "(image-only)",
        response_text=ai_response,
    )
    
    # Analyze priority and extract specialization
    priority = analyze_priority(symptoms_text, ai_response)
    specialization = extract_specialization(ai_response)
    
    # Extract first aid from response (simple heuristic)
    first_aid = ""
    if "first aid" in ai_response.lower():
        parts = ai_response.split("First aid")
        if len(parts) > 1:
            first_aid = "First aid" + parts[1].split("\n\n")[0]
    
    # Generate summary for storage (keep full response for returning to user)
    ai_summary = await generate_summary(ai_response, language=language)
    
    # Save consultation with summary
    consultation = Consultation(
        user_id=current_user.id,
        symptoms=symptoms_text,
        image_path=image_path,
        ai_response=ai_summary,  # Store summary instead of full response
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
                "status": c.status.value,
                "recommended_specialization": c.recommended_specialization,
                "created_at": c.created_at.isoformat()
            }
            for c in consultations
        ]
    }


@app.delete("/api/consultations/{consultation_id}")
def delete_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific consultation (user can only delete their own)"""
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.user_id == current_user.id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    db.delete(consultation)
    db.commit()
    return {"message": "Consultation deleted successfully"}


@app.post("/api/consultations/delete-multiple")
def delete_multiple_consultations(
    consultation_ids: list[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple consultations at once"""
    deleted_count = db.query(Consultation).filter(
        Consultation.id.in_(consultation_ids),
        Consultation.user_id == current_user.id
    ).delete(synchronize_session=False)
    
    db.commit()
    return {"message": f"Deleted {deleted_count} consultations"}


# Admin helper function
def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Admin Case Management Endpoints

@app.post("/api/admin/consultations/{consultation_id}/take-case")
def take_case(
    consultation_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin takes a case under supervision"""
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if consultation.status != ConsultationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Case is already {consultation.status.value}. Cannot take case."
        )
    
    consultation.status = ConsultationStatus.UNDER_SUPERVISION
    consultation.supervising_admin_id = current_admin.id
    db.commit()
    
    return {
        "message": "Case taken successfully",
        "status": consultation.status.value,
        "supervising_admin": current_admin.username
    }


@app.post("/api/admin/consultations/{consultation_id}/mark-solved")
def mark_case_solved(
    consultation_id: int,
    notes: str = Form(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a case as solved"""
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if consultation.status == ConsultationStatus.SOLVED:
        raise HTTPException(status_code=400, detail="Case is already marked as solved")
    
    # Allow marking as solved if supervising admin or if taking over
    if consultation.status == ConsultationStatus.PENDING:
        consultation.supervising_admin_id = current_admin.id
    
    consultation.status = ConsultationStatus.SOLVED
    if notes:
        consultation.supervision_notes = notes
    db.commit()
    
    return {
        "message": "Case marked as solved",
        "status": consultation.status.value
    }


@app.post("/api/admin/consultations/{consultation_id}/release-case")
def release_case(
    consultation_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Release a case back to pending status"""
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if consultation.status == ConsultationStatus.SOLVED:
        raise HTTPException(status_code=400, detail="Cannot release a solved case")
    
    # Only supervising admin can release
    if consultation.supervising_admin_id != current_admin.id:
        raise HTTPException(status_code=403, detail="Only supervising admin can release this case")
    
    consultation.status = ConsultationStatus.PENDING
    consultation.supervising_admin_id = None
    db.commit()
    
    return {
        "message": "Case released successfully",
        "status": consultation.status.value
    }


# Admin Data Access Endpoints


@app.get("/api/admin/patients")
def get_all_patients(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all registered patients"""
    patients = db.query(User).filter(User.is_admin == False).all()
    return {
        "patients": [
            {
                "id": p.id,
                "username": p.username,
                "full_name": p.full_name,
                "email": p.email,
                "phone": p.phone,
                "blood_group": p.blood_group,
                "created_at": p.created_at.isoformat(),
                "total_consultations": len(p.consultations)
            }
            for p in patients
        ]
    }


@app.get("/api/admin/consultations")
def get_all_consultations(
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all consultations with patient info"""
    consultations = db.query(Consultation).order_by(
        Consultation.created_at.desc()
    ).limit(limit).all()
    
    return {
        "consultations": [
            {
                "id": c.id,
                "patient_id": c.user_id,
                "patient_name": c.user.full_name or c.user.username,
                "patient_phone": c.user.phone,
                "patient_blood_group": c.user.blood_group,
                "symptoms": c.symptoms,
                "ai_response": c.ai_response,
                "priority": c.priority.value,
                "status": c.status.value,
                "supervising_admin": db.query(User).get(c.supervising_admin_id).username if c.supervising_admin_id else None,
                "supervision_notes": c.supervision_notes,
                "recommended_specialization": c.recommended_specialization,
                "created_at": c.created_at.isoformat(),
                "is_synced": c.is_synced
            }
            for c in consultations
        ]
    }


@app.get("/api/admin/patient/{patient_id}")
def get_patient_detail(
    patient_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get detailed info about a specific patient"""
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consultations = db.query(Consultation).filter(
        Consultation.user_id == patient_id
    ).order_by(Consultation.created_at.desc()).all()
    
    medical_history = db.query(MedicalHistory).filter(
        MedicalHistory.user_id == patient_id
    ).all()
    
    return {
        "patient": {
            "id": patient.id,
            "username": patient.username,
            "full_name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone,
            "blood_group": patient.blood_group,
            "address": patient.address,
            "created_at": patient.created_at.isoformat()
        },
        "consultations": [
            {
                "id": c.id,
                "symptoms": c.symptoms,
                "ai_response": c.ai_response,
                "priority": c.priority.value,
                "recommended_specialization": c.recommended_specialization,
                "created_at": c.created_at.isoformat()
            }
            for c in consultations
        ],
        "medical_history": [
            {
                "condition": h.condition,
                "is_chronic": h.is_chronic,
                "notes": h.notes
            }
            for h in medical_history
        ]
    }


@app.get("/api/admin/stats")
def get_admin_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get dashboard statistics"""
    total_patients = db.query(User).filter(User.is_admin == False).count()
    total_consultations = db.query(Consultation).count()
    critical_cases = db.query(Consultation).filter(
        Consultation.priority == PriorityLevel.CRITICAL
    ).count()
    high_cases = db.query(Consultation).filter(
        Consultation.priority == PriorityLevel.HIGH
    ).count()
    
    # Case status counts
    pending_cases = db.query(Consultation).filter(
        Consultation.status == ConsultationStatus.PENDING
    ).count()
    under_supervision = db.query(Consultation).filter(
        Consultation.status == ConsultationStatus.UNDER_SUPERVISION
    ).count()
    solved_cases = db.query(Consultation).filter(
        Consultation.status == ConsultationStatus.SOLVED
    ).count()
    
    return {
        "total_patients": total_patients,
        "total_consultations": total_consultations,
        "critical_cases": critical_cases,
        "high_priority_cases": high_cases,
        "pending_cases": pending_cases,
        "under_supervision": under_supervision,
        "solved_cases": solved_cases
    }
