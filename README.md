# FutureBuilders2025_GreenU_Tensors

This is a small FastAPI demo that sends an uploaded image + prompt to a local Ollama vision model.

**Prereqs**
- Ollama installed and running (`ollama serve`)
- A vision model pulled in Ollama (default: `qwen3-vl:2b`)

**Install**
- `pip install -r requirements.txt`

**Run**
- Start Ollama: `ollama serve`
- Pull the model once (if needed): `ollama run qwen3-vl:2b`
- Start API: `uvicorn app:app --host 0.0.0.0 --port 8000`

**Config (optional)**
- `OLLAMA_HOST` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `qwen3-vl:2b`)
