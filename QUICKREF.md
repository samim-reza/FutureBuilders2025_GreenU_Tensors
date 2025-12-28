# 🚀 WeCare - Quick Reference

## Start the App (Every Time)

### Terminal 1: Ollama
```bash
ollama serve
```

### Terminal 2: WeCare
```bash
cd /home/samim01/Code/FutureBuilders2025_GreenU_Tensors
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Browser
```
http://localhost:8000
```

---

## First Time Setup Only

```bash
# Run the setup script
cd /home/samim01/Code/FutureBuilders2025_GreenU_Tensors
./setup.sh
```

This will:
- ✓ Install Python packages
- ✓ Create MySQL database
- ✓ Seed dummy data (doctors, hospitals, NGOs)
- ✓ Check Ollama installation

---

## Common Commands

### Check if Ollama is running
```bash
curl http://localhost:11434
```

### Check if WeCare API is running
```bash
curl http://localhost:8000/api/doctors
```

### View MySQL data
```bash
mysql -u wecare_user -pwecare_password wecare_db
```

### Reset database
```bash
python seed_data.py
```

### View logs
```bash
# WeCare logs in terminal
# Ollama logs in terminal
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Ollama not found | Install from https://ollama.ai |
| MySQL error | `sudo systemctl restart mysql` |
| Module not found | `pip install -r requirements.txt` |
| Offline not working | Clear browser cache, reload |

---

## Test the App

1. **Register**: Create account at http://localhost:8000
2. **Login**: Sign in with credentials
3. **Consult**: 
   - Symptoms: "fever and headache"
   - Upload image (optional)
   - Click "Get Medical Advice"
4. **Test Offline**:
   - Open DevTools (F12)
   - Network tab → Offline checkbox
   - Try another consultation
   - Go back online → auto-syncs

---

## File Structure

```
.
├── app.py              ← Main backend
├── models.py           ← Database models
├── auth.py             ← Authentication
├── seed_data.py        ← Setup database
├── index.html          ← Main UI
├── static/
│   ├── db.js          ← IndexedDB
│   ├── api.js         ← API calls
│   └── app.js         ← UI logic
├── README.md           ← Full docs
├── SETUP.md            ← Setup guide
└── setup.sh            ← Auto-setup
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Login user |
| `/api/consultation` | POST | Create consultation |
| `/api/doctors` | GET | List doctors |
| `/api/hospitals` | GET | List hospitals |
| `/api/ngos` | GET | List NGOs |
| `/api/sync/consultations` | POST | Sync offline data |

---

## Environment Variables

Create `.env` file (optional):
```bash
DATABASE_URL=mysql+pymysql://wecare_user:wecare_password@localhost:3306/wecare_db
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:2b
SECRET_KEY=change-this-in-production
```

---

**Made with ❤️ for FutureBuilders2025**
