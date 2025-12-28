# Setup Instructions - Quick Start

## 🚀 Quick Setup (5 minutes)

### Step 1: Start Ollama
```bash
# Terminal 1
ollama serve
```

### Step 2: Setup Database (First Time Only)
```bash
# Create MySQL database
sudo mysql -e "CREATE DATABASE IF NOT EXISTS wecare_db;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'wecare_user'@'localhost' IDENTIFIED BY 'wecare_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON wecare_db.* TO 'wecare_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### Step 3: Install Python Dependencies & Seed Data
```bash
# Terminal 2
cd /home/samim01/Code/FutureBuilders2025_GreenU_Tensors
source venv/bin/activate
pip install -r requirements.txt

# Initialize database and add dummy data
python seed_data.py
```

### Step 4: Run the App
```bash
# Same terminal (Terminal 2)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Open in Browser
```
http://localhost:8000
```

## ✅ Verify Everything Works

1. **Register a new account**
2. **Create a consultation** with sample symptoms
3. **Toggle offline mode** in DevTools (Network → Offline) and test
4. **View doctors/hospitals** in the Resources tab

## 📝 Sample Test Data

### Test User
- Username: `testuser`
- Email: `test@wecare.bd`
- Password: `test123`

### Sample Consultation
- Symptoms: "I have fever and headache for 2 days, feeling weak"
- Use History: ✓ checked
- Image: (optional)

Expected: Should get AI analysis, priority level, first aid steps, and doctor recommendations.

## 🔍 Troubleshooting

### Port 8000 already in use?
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app:app --host 0.0.0.0 --port 8080
```

### Ollama not responding?
```bash
# Check if running
ps aux | grep ollama

# Restart
pkill ollama
ollama serve
```

### Database errors?
```bash
# Check MySQL status
sudo systemctl status mysql

# Restart MySQL
sudo systemctl restart mysql
```

---

**Ready to go!** 🎉
