# 🧪 WeCare Testing Checklist

## ✅ Pre-Launch Checks

### 1. Services Running
- [ ] Ollama server: `curl http://localhost:11434` returns response
- [ ] MySQL server: `sudo systemctl status mysql` shows active
- [ ] WeCare API: http://localhost:8000 loads page

### 2. Database Initialized
- [ ] Run `python seed_data.py` without errors
- [ ] Verify data: `mysql -u wecare_user -pwecare_password -e "SELECT COUNT(*) FROM wecare_db.doctors;"`
- [ ] Should show 7 doctors

---

## 🧪 Feature Testing

### Authentication Tests

#### Register New User
- [ ] Go to http://localhost:8000
- [ ] Click "Register"
- [ ] Fill form:
  - Full Name: Test User
  - Username: testuser
  - Email: test@wecare.bd
  - Phone: 01700000000
  - Password: test123
- [ ] Click "Register"
- [ ] ✅ Should see "Account created successfully!"
- [ ] ✅ Should redirect to main app

#### Login
- [ ] Logout if logged in
- [ ] Click "Login"
- [ ] Enter:
  - Username: testuser
  - Password: test123
- [ ] Click "Login"
- [ ] ✅ Should see "Welcome back!"
- [ ] ✅ Username displayed in header

---

### Consultation Tests

#### Test 1: Text-Only Consultation (Online)
- [ ] Ensure you're online (no offline indicator)
- [ ] In "New Consultation" tab:
  - Symptoms: "I have high fever (39°C) and severe headache for 2 days"
  - Image: (leave empty)
  - Use history: ✓ checked
- [ ] Click "Get Medical Advice"
- [ ] ✅ Should show "Analyzing..." button
- [ ] ✅ After ~5-10 seconds, should show:
  - Priority badge (likely "HIGH" or "MEDIUM")
  - AI response with analysis
  - First aid suggestions
  - Recommended doctors

#### Test 2: With Image (Online)
- [ ] Take/find a photo (any medical-related image)
- [ ] In "New Consultation" tab:
  - Symptoms: "Rash on arm, red and itchy"
  - Image: Upload photo
  - Use history: ✓ checked
- [ ] Click "Get Medical Advice"
- [ ] ✅ Should get response with image analysis
- [ ] ✅ May recommend Dermatology specialist

#### Test 3: Without History
- [ ] New consultation:
  - Symptoms: "Mild cold and runny nose"
  - Use history: ✗ unchecked
- [ ] Click "Get Medical Advice"
- [ ] ✅ Should work without using past history
- [ ] ✅ Priority likely "LOW"

#### Test 4: Critical Symptoms
- [ ] New consultation:
  - Symptoms: "Severe chest pain and difficulty breathing"
- [ ] Click "Get Medical Advice"
- [ ] ✅ Priority should be "CRITICAL"
- [ ] ✅ Should recommend emergency care
- [ ] ✅ May recommend Cardiology

---

### Offline Mode Tests

#### Test 5: Go Offline
- [ ] Open DevTools (F12)
- [ ] Go to "Network" tab
- [ ] Check "Offline" checkbox
- [ ] ✅ Orange badge appears: "📴 Offline Mode"

#### Test 6: Offline Consultation
- [ ] While offline, new consultation:
  - Symptoms: "Headache and fever"
- [ ] Click "Get Medical Advice"
- [ ] ✅ Should show "[Offline Mode - Basic Assessment]"
- [ ] ✅ Shows notification: "Saved offline - will sync when online"
- [ ] ✅ Basic triage works without Ollama

#### Test 7: View Cached Resources
- [ ] While offline, click "Doctors & Hospitals" tab
- [ ] ✅ Should show 7 doctors (cached)
- [ ] ✅ Should show 5 hospitals (cached)
- [ ] ✅ Should show 5 NGOs (cached)

#### Test 8: Auto-Sync
- [ ] Stay on "Doctors & Hospitals" tab
- [ ] Uncheck "Offline" in DevTools (go back online)
- [ ] ✅ Orange badge disappears
- [ ] ✅ Notification: "Offline data synced successfully"
- [ ] ✅ Check browser console: should show sync logs

---

### Resources Tab Tests

#### Test 9: View Doctors
- [ ] Online mode
- [ ] Click "Doctors & Hospitals" tab
- [ ] ✅ Should show 7 doctors with:
  - Name, specialization, qualification
  - Hospital, phone, fee
  - Available days, address

#### Test 10: View Hospitals
- [ ] Scroll down in Resources tab
- [ ] ✅ Should show 5 hospitals:
  - Government and Private types
  - Emergency availability marked
  - Facilities listed
  - Contact info

#### Test 11: View NGOs
- [ ] Scroll down further
- [ ] ✅ Should show 5 NGOs:
  - Services description
  - Contact info (phone, email)
  - Working areas

---

## 🔄 Sync Testing

### Test 12: Multiple Offline Consultations
- [ ] Go offline (DevTools)
- [ ] Create 3 consultations with different symptoms
- [ ] ✅ All saved with "Saved offline" message
- [ ] Go back online
- [ ] ✅ All 3 should sync
- [ ] ✅ Check MySQL: `SELECT COUNT(*) FROM consultations WHERE created_offline = 1;`

---

## 📱 PWA Testing

### Test 13: Install as PWA
- [ ] Chrome: Click ⊕ in address bar
- [ ] Or: Menu → Install WeCare
- [ ] ✅ Should install as standalone app
- [ ] ✅ Opens in separate window
- [ ] ✅ No browser UI

### Test 14: Offline After Install
- [ ] Close all browser tabs
- [ ] Turn off WiFi
- [ ] Open installed PWA
- [ ] ✅ Should load (service worker cached)
- [ ] ✅ Can still view cached resources

---

## 🔐 Security Testing

### Test 15: Protected Routes
- [ ] Logout
- [ ] Try to access: http://localhost:8000/api/consultations/history
- [ ] ✅ Should get 401 Unauthorized (no token)

### Test 16: Invalid Credentials
- [ ] Login with:
  - Username: wronguser
  - Password: wrongpass
- [ ] ✅ Should show error: "Incorrect username or password"

### Test 17: Duplicate Registration
- [ ] Try to register with existing username/email
- [ ] ✅ Should show: "Username or email already registered"

---

## 🚨 Error Handling

### Test 18: Ollama Down
- [ ] Stop Ollama: `pkill ollama`
- [ ] Try online consultation
- [ ] ✅ Should show error: "Could not connect to Ollama"
- [ ] Restart: `ollama serve`

### Test 19: Database Down
- [ ] Stop MySQL: `sudo systemctl stop mysql`
- [ ] Try to login
- [ ] ✅ Should show database error
- [ ] Restart: `sudo systemctl start mysql`

### Test 20: Network Transition
- [ ] Start consultation while online
- [ ] Go offline mid-request
- [ ] ✅ Should handle gracefully (timeout/retry)

---

## 📊 Performance Testing

### Test 21: Page Load Speed
- [ ] Hard refresh (Ctrl+Shift+R)
- [ ] ✅ Should load in < 2 seconds (first time)
- [ ] ✅ Should load in < 500ms (cached)

### Test 22: Consultation Response Time
- [ ] Online consultation
- [ ] ✅ Should respond in 5-15 seconds (depends on Ollama)
- [ ] Offline consultation
- [ ] ✅ Should respond instantly (< 1 second)

### Test 23: Large Image Upload
- [ ] Upload 5MB image
- [ ] ✅ Should work (may be slower)
- [ ] ✅ Check `uploads/` folder for saved image

---

## ✅ Final Checklist

- [ ] All authentication flows work
- [ ] Online consultations get AI responses
- [ ] Offline consultations save locally
- [ ] Auto-sync works when back online
- [ ] Resources cached and viewable offline
- [ ] PWA installs correctly
- [ ] Error messages are clear
- [ ] No console errors in browser
- [ ] Database has seeded data
- [ ] All buttons/forms work

---

## 📝 Test Results Log

| Test | Status | Notes |
|------|--------|-------|
| Authentication | ☐ Pass ☐ Fail | |
| Online Consultation | ☐ Pass ☐ Fail | |
| Offline Consultation | ☐ Pass ☐ Fail | |
| Auto-Sync | ☐ Pass ☐ Fail | |
| Resources Tab | ☐ Pass ☐ Fail | |
| PWA Install | ☐ Pass ☐ Fail | |
| Error Handling | ☐ Pass ☐ Fail | |

---

**Test Date**: __________
**Tester**: __________
**Environment**: Ubuntu / Browser: __________

