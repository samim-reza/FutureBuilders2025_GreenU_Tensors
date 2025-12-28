# 🏥 WeCare - Medical Assistant for Rural Bangladesh

An offline-first Progressive Web App (PWA) providing medical consultation, first aid guidance, and healthcare resource discovery for rural areas with limited internet connectivity.

## ✨ Features

- **🤖 AI-Powered Medical Consultation**: Get medical advice using vision-language models (Ollama Qwen)
- **📴 Offline-First Architecture**: Works without internet using IndexedDB for local storage
- **🔄 Auto-Sync**: Automatically syncs data when connection is restored
- **🏥 Healthcare Resources**: Find doctors, hospitals, and NGOs with cached local data
- **👤 User Accounts**: Track medical history for better recommendations (toggle on/off)
- **🚨 AI Triage**: Automatically determines priority (Critical/High/Medium/Low)
- **💊 First Aid Suggestions**: Get immediate treatment steps
- **📱 Progressive Web App**: Install on mobile devices like a native app

## 🏗️ Architecture

- **Backend**: FastAPI with Ollama integration
- **Database**: MySQL for cloud sync
- **Local Storage**: IndexedDB for offline data
- **AI Model**: Qwen3-VL-2B (via Ollama)
- **Auth**: JWT-based authentication

## 📋 Prerequisites

### 1. Ollama
```bash
# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the vision model
ollama pull qwen3-vl:2b
```

### 2. MySQL
```bash
# Install MySQL
sudo apt install mysql-server

# Create database and user
sudo mysql
```

```sql
CREATE DATABASE wecare_db;
CREATE USER 'wecare_user'@'localhost' IDENTIFIED BY 'wecare_password';
GRANT ALL PRIVILEGES ON wecare_db.* TO 'wecare_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Python 3.10+
```bash
python3 --version  # Should be 3.10 or higher
```

## 🚀 Installation

### 1. Clone & Setup Python Environment
```bash
cd /home/samim01/Code/FutureBuilders2025_GreenU_Tensors

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Create a `.env` file:
```bash
# Database
DATABASE_URL=mysql+pymysql://wecare_user:wecare_password@localhost:3306/wecare_db

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:2b

# Auth (change in production!)
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Initialize Database & Seed Data
```bash
# Run seed script to create tables and insert dummy data
python seed_data.py
```

This will create:
- 7 doctors across different specializations
- 5 hospitals (government & private)
- 5 NGOs and support organizations

## 🏃 Running the Application

### Terminal 1: Start Ollama Server
```bash
ollama serve
```

### Terminal 2: Start FastAPI Server
```bash
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Access the Application
Open your browser and go to:
```
http://localhost:8000
```

## 📱 Usage Guide

### First Time Setup
1. **Register**: Create an account with username, email, and password
2. **Login**: Sign in to access the consultation service

### Medical Consultation
1. Navigate to **"New Consultation"** tab
2. Describe your symptoms in the text area
3. (Optional) Upload an image if you have visible symptoms
4. Toggle **"Use my medical history"** if you want personalized recommendations
5. Click **"Get Medical Advice"**

The AI will provide:
- Analysis of symptoms
- Priority level (Critical/High/Medium/Low)
- First aid steps
- Recommended doctor specialization
- List of available doctors

### Finding Healthcare Resources
1. Navigate to **"Doctors & Hospitals"** tab
2. Browse:
   - **Doctors**: Specializations, contact info, fees, availability
   - **Hospitals**: Locations, facilities, emergency availability
   - **NGOs**: Support services, contact information

### Offline Mode
When **offline** (no internet):
- ✅ Basic symptom triage still works
- ✅ View cached doctors, hospitals, NGOs
- ✅ Consultations saved locally
- 🔄 Data automatically syncs when back online

## 🗂️ Project Structure

```
FutureBuilders2025_GreenU_Tensors/
├── app.py                 # Main FastAPI application
├── models.py              # Database models (SQLAlchemy)
├── database.py            # Database connection & session
├── auth.py                # JWT authentication logic
├── seed_data.py           # Database seeding script
├── requirements.txt       # Python dependencies
├── index.html             # Main HTML interface
├── manifest.json          # PWA manifest
├── service-worker.js      # Service worker for offline support
├── static/
│   ├── db.js              # IndexedDB manager
│   ├── api.js             # API client & sync logic
│   └── app.js             # Frontend application logic
└── uploads/               # User-uploaded images
```

## 🔧 Configuration

### Change Ollama Model
```bash
# Use a different model
export OLLAMA_MODEL=llava:7b
ollama pull llava:7b
```

### Change Database
Edit `database.py` or set `DATABASE_URL` environment variable:
```python
DATABASE_URL = "mysql+pymysql://user:password@host:port/database"
```

### Adjust AI Triage Keywords
Edit priority detection in `app.py` → `analyze_priority()` function

## 🛠️ API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Consultation
- `POST /api/consultation` - Create consultation (with/without image)
- `POST /api/sync/consultations` - Sync offline consultations
- `GET /api/consultations/history` - Get user's consultation history

### Resources
- `GET /api/doctors?specialization=X` - Get doctors
- `GET /api/hospitals` - Get hospitals
- `GET /api/ngos` - Get NGOs

## 🐛 Troubleshooting

### "Could not connect to Ollama"
- Ensure `ollama serve` is running
- Check `OLLAMA_HOST` points to correct address

### Database connection errors
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `database.py` or `.env`
- Ensure database and user exist

### Module import errors
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Offline mode not working
- Check browser console for IndexedDB errors
- Ensure service worker is registered (check DevTools → Application)

## 🔒 Security Notes

⚠️ **Production Deployment**:
- Change `SECRET_KEY` in `auth.py`
- Use HTTPS
- Set proper CORS origins
- Use environment variables for secrets
- Enable rate limiting

## 📄 License

MIT License - Feel free to use for humanitarian purposes

## 🙏 Acknowledgments

Built for **FutureBuilders2025** to address healthcare accessibility challenges in Bangladesh's Chittagong Hill Tracts and rural regions.

---

**Made with ❤️ for rural Bangladesh**
