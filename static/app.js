// Main Application Logic
let currentUser = null;

// Check auth on page load
window.addEventListener('DOMContentLoaded', async () => {
    await db.init();
    
    const token = localStorage.getItem('wecare_token');
    if (token) {
        try {
            const userData = await api.getMe();
            currentUser = userData;
            showMainApp();
            await loadCacheData();
        } catch (error) {
            console.error('Auth error:', error);
            // Clear both localStorage and API client token
            localStorage.removeItem('wecare_token');
            api.clearToken();
        }
    }

    // Update offline indicator
    if (!navigator.onLine) {
        document.getElementById('offline-indicator').classList.remove('hidden');
    }
});

// Auth functions
function showLogin() {
    hideAuthForms();
    document.getElementById('login-form').classList.remove('hidden');
}

function showRegister() {
    hideAuthForms();
    document.getElementById('register-form').classList.remove('hidden');
}

function hideAuthForms() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.add('hidden');
}

async function handleLogin(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    try {
        const data = await api.login({
            username: formData.get('username'),
            password: formData.get('password')
        });
        
        currentUser = data.user;
        showMainApp();
        event.target.reset();
        showNotification('Welcome back!', 'success');
        await loadCacheData();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    try {
        const data = await api.register({
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            full_name: formData.get('full_name') || undefined,
            phone: formData.get('phone') || undefined
        });
        
        currentUser = data.user;
        showMainApp();
        event.target.reset();
        showNotification('Account created successfully!', 'success');
        await loadCacheData();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function logout() {
    api.clearToken();
    currentUser = null;
    document.getElementById('main-app').classList.add('hidden');
    document.getElementById('user-section').classList.add('hidden');
    document.getElementById('auth-buttons').classList.remove('hidden');
    showNotification('Logged out', 'info');
}

function showMainApp() {
    hideAuthForms();
    document.getElementById('main-app').classList.remove('hidden');
    document.getElementById('user-section').classList.remove('hidden');
    document.getElementById('auth-buttons').classList.add('hidden');
    document.getElementById('username-display').textContent = currentUser.full_name || currentUser.username;
}

// Tab management
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Show/hide tab content
    document.getElementById('consultation-tab').classList.add('hidden');
    document.getElementById('resources-tab').classList.add('hidden');
    
    if (tabName === 'consultation') {
        document.getElementById('consultation-tab').classList.remove('hidden');
    } else if (tabName === 'resources') {
        document.getElementById('resources-tab').classList.remove('hidden');
        loadResourcesTab();
    }
}

// Consultation handling
async function handleConsultation(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Analyzing...';
    
    try {
        if (api.isOnline()) {
            // Online mode - send to server
            const result = await api.createConsultation(formData);
            displayConsultationResult(result);
            showNotification('Consultation complete!', 'success');
        } else {
            // Offline mode - save locally
            const symptoms = formData.get('symptoms');
            const useHistory = formData.get('use_history') === 'on';
            
            // Generate basic offline response
            const offlineResponse = generateOfflineResponse(symptoms);
            
            // Save to IndexedDB
            await db.addConsultation({
                symptoms,
                ai_response: offlineResponse.response,
                priority: offlineResponse.priority,
                first_aid_suggestions: offlineResponse.firstAid,
                recommended_specialization: offlineResponse.specialization,
                use_history: useHistory,
                synced: false,
                created_at: new Date().toISOString()
            });
            
            displayConsultationResult(offlineResponse);
            showNotification('Saved offline - will sync when online', 'info');
        }
        
        form.reset();
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Get Medical Advice';
    }
}

function generateOfflineResponse(symptoms) {
    // Basic offline triage based on keywords
    const text = symptoms.toLowerCase();
    let priority = 'low';
    let specialization = 'General Medicine';
    let firstAid = '';
    
    if (text.includes('chest pain') || text.includes('heart') || text.includes('breathing')) {
        priority = 'critical';
        specialization = 'Cardiology';
        firstAid = 'Seek emergency care immediately. Call ambulance if available.';
    } else if (text.includes('fever') && text.includes('severe')) {
        priority = 'high';
        firstAid = 'Rest, drink plenty of fluids, take paracetamol if available.';
    } else if (text.includes('fever') || text.includes('headache') || text.includes('cold')) {
        priority = 'medium';
        firstAid = 'Rest well, stay hydrated, monitor temperature.';
    }
    
    const response = `[Offline Mode - Basic Assessment]

Your symptoms have been recorded. Priority level: ${priority.toUpperCase()}

${firstAid}

This is a basic offline assessment. For accurate diagnosis and treatment, please consult with a healthcare professional as soon as possible.

Recommended: ${specialization} specialist`;
    
    return {
        consultation_id: null,
        ai_response: response,
        priority,
        first_aid_suggestions: firstAid,
        recommended_specialization: specialization,
        recommended_doctors: []
    };
}

function displayConsultationResult(result) {
    document.getElementById('consultation-result').classList.remove('hidden');
    
    // Priority badge
    const priorityBadge = document.getElementById('priority-badge');
    priorityBadge.className = `priority priority-${result.priority}`;
    priorityBadge.textContent = `Priority: ${result.priority.toUpperCase()}`;
    
    // AI Response
    document.getElementById('ai-response').textContent = result.ai_response;
    
    // First Aid
    if (result.first_aid_suggestions) {
        document.getElementById('first-aid-section').classList.remove('hidden');
        document.getElementById('first-aid-text').textContent = result.first_aid_suggestions;
    } else {
        document.getElementById('first-aid-section').classList.add('hidden');
    }
    
    // Recommended Doctors
    if (result.recommended_doctors && result.recommended_doctors.length > 0) {
        document.getElementById('doctors-section').classList.remove('hidden');
        const doctorsList = document.getElementById('doctors-list');
        doctorsList.innerHTML = result.recommended_doctors.map(doctor => `
            <div class="doctor-card">
                <h4>${doctor.name}</h4>
                <p><strong>${doctor.specialization}</strong></p>
                <p>Hospital: ${doctor.hospital}</p>
                <p>Available: ${doctor.available_days}</p>
                <p>Fee: ৳${doctor.fee}</p>
                <p>Phone: ${doctor.phone}</p>
                <p>Address: ${doctor.address}</p>
            </div>
        `).join('');
    } else {
        document.getElementById('doctors-section').classList.add('hidden');
    }
    
    // Scroll to result
    document.getElementById('consultation-result').scrollIntoView({ behavior: 'smooth' });
}

// Resources tab
async function loadResourcesTab() {
    try {
        // Load doctors
        let doctors;
        if (api.isOnline()) {
            const data = await api.getDoctors();
            doctors = data.doctors;
            await db.saveDoctors(doctors);
        } else {
            doctors = await db.getDoctors();
        }
        
        const doctorsList = document.getElementById('doctors-resource-list');
        if (doctors.length > 0) {
            doctorsList.innerHTML = doctors.map(doctor => `
                <div class="doctor-card">
                    <h4>${doctor.name}</h4>
                    <p><strong>${doctor.specialization}</strong> - ${doctor.qualification}</p>
                    <p>Hospital: ${doctor.hospital}</p>
                    <p>Available: ${doctor.available_days}</p>
                    <p>Fee: ৳${doctor.fee}</p>
                    <p>Phone: ${doctor.phone}</p>
                    <p>Address: ${doctor.address}</p>
                </div>
            `).join('');
        } else {
            doctorsList.innerHTML = '<p>No doctors cached. Connect to internet to load.</p>';
        }
        
        // Load hospitals
        let hospitals;
        if (api.isOnline()) {
            const data = await api.getHospitals();
            hospitals = data.hospitals;
            await db.saveHospitals(hospitals);
        } else {
            hospitals = await db.getHospitals();
        }
        
        const hospitalsList = document.getElementById('hospitals-list');
        if (hospitals.length > 0) {
            hospitalsList.innerHTML = hospitals.map(hospital => `
                <div class="doctor-card">
                    <h4>${hospital.name}</h4>
                    <p><strong>${hospital.type}</strong></p>
                    <p>${hospital.address}</p>
                    <p>Phone: ${hospital.phone}</p>
                    ${hospital.emergency_available ? '<p style="color: #f44336;"><strong>24/7 Emergency Available</strong></p>' : ''}
                    <p>Facilities: ${hospital.facilities}</p>
                </div>
            `).join('');
        } else {
            hospitalsList.innerHTML = '<p>No hospitals cached. Connect to internet to load.</p>';
        }
        
        // Load NGOs
        let ngos;
        if (api.isOnline()) {
            const data = await api.getNGOs();
            ngos = data.ngos;
            await db.saveNGOs(ngos);
        } else {
            ngos = await db.getNGOs();
        }
        
        const ngosList = document.getElementById('ngos-list');
        if (ngos.length > 0) {
            ngosList.innerHTML = ngos.map(ngo => `
                <div class="doctor-card">
                    <h4>${ngo.name}</h4>
                    <p>${ngo.services}</p>
                    <p>${ngo.address}</p>
                    <p>Phone: ${ngo.phone}</p>
                    <p>Email: ${ngo.email}</p>
                    <p>Working Areas: ${ngo.working_areas}</p>
                </div>
            `).join('');
        } else {
            ngosList.innerHTML = '<p>No NGOs cached. Connect to internet to load.</p>';
        }
        
    } catch (error) {
        console.error('Error loading resources:', error);
        showNotification('Error loading resources', 'error');
    }
}
