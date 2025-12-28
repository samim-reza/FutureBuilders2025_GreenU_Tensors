// API Client for WeCare
class WeCareAPI {
    constructor() {
        this.baseURL = window.location.origin;
        this.token = localStorage.getItem('wecare_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('wecare_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('wecare_token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        // Don't set Content-Type for FormData (browser will set it with boundary)
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async register(userData) {
        const data = await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
        this.setToken(data.access_token);
        return data;
    }

    async login(credentials) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
        this.setToken(data.access_token);
        return data;
    }

    async getMe() {
        return this.request('/api/auth/me');
    }

    async createConsultation(formData) {
        return this.request('/api/consultation', {
            method: 'POST',
            body: formData,
        });
    }

    async syncConsultations(consultations) {
        return this.request('/api/sync/consultations', {
            method: 'POST',
            body: JSON.stringify(consultations),
        });
    }

    async getDoctors(specialization = null) {
        const params = specialization ? `?specialization=${encodeURIComponent(specialization)}` : '';
        return this.request(`/api/doctors${params}`);
    }

    async getHospitals() {
        return this.request('/api/hospitals');
    }

    async getNGOs() {
        return this.request('/api/ngos');
    }

    async getConsultationHistory() {
        return this.request('/api/consultations/history');
    }

    isOnline() {
        return navigator.onLine;
    }
}

// Initialize API client
const api = new WeCareAPI();

// Network status management
let isOnline = navigator.onLine;

window.addEventListener('online', async () => {
    console.log('✅ Back online');
    isOnline = true;
    document.getElementById('offline-indicator')?.classList.add('hidden');
    
    // Auto-sync when back online
    await syncOfflineData();
    await loadCacheData();
});

window.addEventListener('offline', () => {
    console.log('📴 Went offline');
    isOnline = false;
    document.getElementById('offline-indicator')?.classList.remove('hidden');
});

// Sync offline consultations
async function syncOfflineData() {
    try {
        const unsyncedConsultations = await db.getUnsyncedConsultations();
        if (unsyncedConsultations.length === 0) return;

        console.log(`Syncing ${unsyncedConsultations.length} offline consultations...`);
        
        const payload = unsyncedConsultations.map(c => ({
            symptoms: c.symptoms,
            ai_response: c.ai_response,
            priority: c.priority,
            first_aid_suggestions: c.first_aid_suggestions,
            recommended_specialization: c.recommended_specialization,
            created_at: c.created_at,
            use_history: c.use_history
        }));

        await api.syncConsultations(payload);

        // Mark as synced
        for (const consultation of unsyncedConsultations) {
            await db.markConsultationSynced(consultation.id);
        }

        console.log('✅ Sync complete');
        showNotification('Offline data synced successfully', 'success');
    } catch (error) {
        console.error('Sync error:', error);
    }
}

// Load and cache data when online
async function loadCacheData() {
    if (!isOnline) return;

    try {
        // Cache doctors
        const { doctors } = await api.getDoctors();
        await db.saveDoctors(doctors);
        console.log(`✅ Cached ${doctors.length} doctors`);

        // Cache hospitals
        const { hospitals } = await api.getHospitals();
        await db.saveHospitals(hospitals);
        console.log(`✅ Cached ${hospitals.length} hospitals`);

        // Cache NGOs
        const { ngos } = await api.getNGOs();
        await db.saveNGOs(ngos);
        console.log(`✅ Cached ${ngos.length} NGOs`);

    } catch (error) {
        console.error('Cache loading error:', error);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
