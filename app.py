from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import FileResponse

import base64
import os

import httpx

app = FastAPI()

# Allow requests from any origin (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:2b")


@app.get("/")
def root():
    return FileResponse("index.html")

@app.post("/generate")
async def generate(prompt: str = Form(...), image: UploadFile = File(...)):
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
    }

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
    return {"response": data.get("response", "")}
