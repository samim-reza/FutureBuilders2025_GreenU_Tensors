# 🔧 Common Issues & Solutions

## Database Connection Errors

### Error: "Access denied for user 'wecare_user'@'localhost'"
**Problem**: Using default credentials instead of your MySQL credentials.

**Solution**: Update `.env` file with your MySQL username and password:
```bash
# If your password contains special characters like @, :, /, etc.
# You MUST URL-encode them:
# @ becomes %40
# : becomes %3A
# / becomes %2F
# % becomes %25

# Example: Password "S@mim101" becomes "S%40mim101"
DATABASE_URL=mysql+pymysql://root:S%40mim101@localhost:3306/wecare_db
```

### Error: "Can't connect to MySQL server"
**Problem**: MySQL is not running or wrong host/port.

**Solution**:
```bash
# Check MySQL status
sudo systemctl status mysql

# Start MySQL
sudo systemctl start mysql

# Check if MySQL is listening
sudo netstat -tlnp | grep 3306
```

### Error: "Unknown database 'wecare_db'"
**Problem**: Database doesn't exist.

**Solution**:
```bash
# Create database manually
mysql -u root -p
```
```sql
CREATE DATABASE wecare_db;
EXIT;
```

Then run: `python seed_data.py`

---

## Ollama Errors

### Error: "Could not connect to Ollama"
**Problem**: Ollama server not running.

**Solution**:
```bash
# Start Ollama in a terminal
ollama serve
```

### Error: "model 'qwen3-vl:2b' not found"
**Problem**: Model not downloaded.

**Solution**:
```bash
# Pull the model (one-time, ~4GB download)
ollama pull qwen3-vl:2b

# Verify it's downloaded
ollama list
```

---

## Port Already in Use

### Error: "Address already in use"
**Problem**: Port 8000 is occupied.

**Solution**:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app:app --host 0.0.0.0 --port 8080
```

---

## Module Import Errors

### Error: "ModuleNotFoundError: No module named 'X'"
**Problem**: Package not installed in venv.

**Solution**:
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall all dependencies
pip install -r requirements.txt
```

---

## Frontend Errors

### Browser shows blank page
**Problem**: JavaScript error or wrong URL.

**Solution**:
1. Check browser console (F12) for errors
2. Verify you're at `http://localhost:8000` not `http://localhost:8000/api/...`
3. Hard refresh: Ctrl+Shift+R

### "Failed to fetch" errors
**Problem**: Backend not running or CORS issue.

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/doctors`
2. Check backend terminal for errors

### IndexedDB errors
**Problem**: Browser blocking IndexedDB.

**Solution**:
- Don't use Incognito/Private mode
- Clear browser data and try again
- Check browser permissions

---

## Authentication Errors

### "Could not validate credentials"
**Problem**: Expired or invalid token.

**Solution**: Logout and login again.

### "Username or email already registered"
**Problem**: Trying to register with existing account.

**Solution**: Use login instead or choose different username/email.

---

## File Permission Errors

### Error: "Permission denied" when running setup.sh
**Problem**: Script not executable.

**Solution**:
```bash
chmod +x setup.sh
./setup.sh
```

### Error: "Permission denied" writing to uploads/
**Problem**: No write permission.

**Solution**:
```bash
mkdir -p uploads
chmod 755 uploads
```

---

## Performance Issues

### Consultation takes too long (>30 seconds)
**Problem**: Ollama model not loaded in memory.

**Possible causes**:
1. First request always slower (loading model)
2. CPU mode (no GPU) - very slow
3. Large image upload

**Solutions**:
- Wait for first request to complete (loads model)
- Use GPU if available
- Resize large images before upload
- Use smaller model: `ollama pull qwen2-vl:1.5b`

---

## URL Encoding Reference

If your MySQL password contains special characters, encode them:

| Character | URL Encoded |
|-----------|-------------|
| @ | %40 |
| : | %3A |
| / | %2F |
| # | %23 |
| ? | %3F |
| & | %26 |
| = | %3D |
| + | %2B |
| $ | %24 |
| % | %25 |
| space | %20 |

Example:
- Original: `P@ss:word/123`
- Encoded: `P%40ss%3Aword%2F123`

---

## Getting Help

If none of these solutions work:

1. **Check logs**:
   - Backend: Terminal running uvicorn
   - Frontend: Browser console (F12)
   - MySQL: `sudo tail -f /var/log/mysql/error.log`

2. **Verify versions**:
   ```bash
   python --version  # Should be 3.10+
   mysql --version
   ollama --version
   ```

3. **Test components individually**:
   ```bash
   # Test MySQL connection
   mysql -u root -p -e "SHOW DATABASES;"
   
   # Test Ollama
   curl http://localhost:11434/api/tags
   
   # Test backend
   curl http://localhost:8000/api/doctors
   ```

4. **Clean restart**:
   ```bash
   # Stop everything
   pkill ollama
   pkill uvicorn
   
   # Start fresh
   ollama serve &
   source venv/bin/activate
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
