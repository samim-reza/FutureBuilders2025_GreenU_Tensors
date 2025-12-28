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
    
    const bloodGroup = formData.get('blood_group');
    
    try {
        const data = await api.register({
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            full_name: formData.get('full_name') || undefined,
            phone: formData.get('phone') || undefined,
            blood_group: bloodGroup || undefined
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
    document.getElementById('history-tab').classList.add('hidden');
    document.getElementById('resources-tab').classList.add('hidden');
    
    if (tabName === 'consultation') {
        document.getElementById('consultation-tab').classList.remove('hidden');
    } else if (tabName === 'history') {
        document.getElementById('history-tab').classList.remove('hidden');
        loadConsultationHistory();
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

    const symptoms = (formData.get('symptoms') || '').toString().trim();
    const imageFile = formData.get('image');
    const hasImage = imageFile instanceof File && imageFile.size > 0;

    // If no file selected, remove the field so backend receives image=None.
    if (!hasImage) {
        formData.delete('image');
    }

    // If symptoms is blank, remove it so backend receives symptoms=None.
    if (!symptoms) {
        formData.delete('symptoms');
    }

    if (!symptoms && !hasImage) {
        showNotification('Please enter symptoms or upload an image.', 'error');
        return;
    }
    if (!api.isOnline() && hasImage && !symptoms) {
        showNotification('Image-only consultation needs internet. Add symptoms text or go online.', 'error');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Analyzing...';
    
    // Show encouraging messages while waiting
    const encouragingMessages = [
        '💚 Stay calm, help is on the way...',
        '✨ Analyzing your symptoms carefully...',
        '🌟 You\'re taking the right step for your health...',
        '💪 Recovery starts with understanding...',
        '🏥 Getting the best medical advice for you...',
        '🌈 Your health matters, we\'re here to help...',
        '❤️ Hang in there, expert guidance coming...',
        '🌸 Every symptom has a solution...'
    ];
    
    let messageIndex = 0;
    const messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % encouragingMessages.length;
        submitBtn.textContent = encouragingMessages[messageIndex];
    }, 2000);
    
    try {
        if (api.isOnline()) {
            // Online mode - send to server
            const result = await api.createConsultation(formData);
            clearInterval(messageInterval);
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
        clearInterval(messageInterval);
        showNotification(error.message, 'error');
    } finally {
        clearInterval(messageInterval);
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
    
    // AI Response - render markdown as HTML
    const aiResponseEl = document.getElementById('ai-response');
    if (typeof marked !== 'undefined') {
        aiResponseEl.innerHTML = marked.parse(result.ai_response);
    } else {
        aiResponseEl.textContent = result.ai_response;
    }
    
    // First Aid
    if (result.first_aid_suggestions) {
        document.getElementById('first-aid-section').classList.remove('hidden');
        const firstAidEl = document.getElementById('first-aid-text');
        if (typeof marked !== 'undefined') {
            firstAidEl.innerHTML = marked.parse(result.first_aid_suggestions);
        } else {
            firstAidEl.textContent = result.first_aid_suggestions;
        }
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

// Consultation History Management
async function loadConsultationHistory() {
    const historyList = document.getElementById('history-list');
    
    try {
        const data = await api.getConsultationHistory();
        
        if (data.consultations.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No consultation history yet. Start your first consultation!</p>';
            return;
        }

        historyList.innerHTML = data.consultations.map(c => `
            <div class="history-item" id="history-${c.id}">
                <input type="checkbox" class="history-checkbox" data-id="${c.id}">
                <h4>
                    ${new Date(c.created_at).toLocaleString()}
                    <span class="priority priority-${c.priority}">${c.priority.toUpperCase()}</span>
                    <span class="status-badge status-${c.status}">${formatStatus(c.status)}</span>
                </h4>
                <p><strong>Symptoms:</strong> ${c.symptoms || 'Image consultation'}</p>
                ${c.recommended_specialization ? `<p><strong>Recommended:</strong> ${c.recommended_specialization}</p>` : ''}
                <button class="expand-btn" onclick="toggleHistoryDetails(${c.id})">▼ View Full Response</button>
                <button class="delete-single-btn" onclick="deleteSingleHistory(${c.id})">Delete</button>
                <div class="history-details" id="details-${c.id}">
                    ${marked.parse(c.ai_response)}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        historyList.innerHTML = `<p style="text-align: center; padding: 40px; color: #f44336;">Error loading history: ${error.message}</p>`;
    }
}

function formatStatus(status) {
    return status.replace('_', ' ').toUpperCase();
}

function toggleHistoryDetails(id) {
    const details = document.getElementById(`details-${id}`);
    details.classList.toggle('expanded');
    event.target.textContent = details.classList.contains('expanded') ? '▲ Hide Response' : '▼ View Full Response';
}

async function deleteSingleHistory(id) {
    if (!confirm('Are you sure you want to delete this consultation?')) return;
    
    try {
        await api.deleteConsultation(id);
        document.getElementById(`history-${id}`).remove();
        showNotification('Consultation deleted', 'success');
        
        // Reload if no items left
        const remaining = document.querySelectorAll('.history-item').length;
        if (remaining === 0) {
            loadConsultationHistory();
        }
    } catch (error) {
        showNotification('Failed to delete: ' + error.message, 'error');
    }
}

function selectAllHistory() {
    const checkboxes = document.querySelectorAll('.history-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => cb.checked = !allChecked);
    event.target.textContent = allChecked ? 'Select All' : 'Deselect All';
}

async function deleteSelectedHistory() {
    const selected = Array.from(document.querySelectorAll('.history-checkbox:checked'))
        .map(cb => parseInt(cb.dataset.id));
    
    if (selected.length === 0) {
        showNotification('No consultations selected', 'error');
        return;
    }

    if (!confirm(`Delete ${selected.length} consultation(s)?`)) return;
    
    try {
        await api.deleteMultipleConsultations(selected);
        showNotification(`Deleted ${selected.length} consultation(s)`, 'success');
        loadConsultationHistory();
    } catch (error) {
        showNotification('Failed to delete: ' + error.message, 'error');
    }
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
