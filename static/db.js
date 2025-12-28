// IndexedDB Manager for WeCare
class WeCareDB {
    constructor() {
        this.dbName = 'WeCareDB';
        this.version = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Consultations store
                if (!db.objectStoreNames.contains('consultations')) {
                    const consultStore = db.createObjectStore('consultations', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    consultStore.createIndex('userId', 'userId', { unique: false });
                    consultStore.createIndex('synced', 'synced', { unique: false });
                    consultStore.createIndex('created_at', 'created_at', { unique: false });
                }

                // Doctors store
                if (!db.objectStoreNames.contains('doctors')) {
                    const docStore = db.createObjectStore('doctors', { keyPath: 'id' });
                    docStore.createIndex('specialization', 'specialization', { unique: false });
                }

                // Hospitals store
                if (!db.objectStoreNames.contains('hospitals')) {
                    db.createObjectStore('hospitals', { keyPath: 'id' });
                }

                // NGOs store
                if (!db.objectStoreNames.contains('ngos')) {
                    db.createObjectStore('ngos', { keyPath: 'id' });
                }

                // User cache
                if (!db.objectStoreNames.contains('userCache')) {
                    db.createObjectStore('userCache', { keyPath: 'key' });
                }
            };
        });
    }

    async addConsultation(consultation) {
        const tx = this.db.transaction(['consultations'], 'readwrite');
        const store = tx.objectStore('consultations');
        return store.add(consultation);
    }

    async getUnsyncedConsultations() {
        const tx = this.db.transaction(['consultations'], 'readonly');
        const store = tx.objectStore('consultations');
        const index = store.index('synced');
        return new Promise((resolve, reject) => {
            const request = index.getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async markConsultationSynced(id) {
        const tx = this.db.transaction(['consultations'], 'readwrite');
        const store = tx.objectStore('consultations');
        const consultation = await this.getConsultation(id);
        consultation.synced = true;
        return store.put(consultation);
    }

    async getConsultation(id) {
        const tx = this.db.transaction(['consultations'], 'readonly');
        const store = tx.objectStore('consultations');
        return new Promise((resolve, reject) => {
            const request = store.get(id);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveCache(key, data) {
        const tx = this.db.transaction(['userCache'], 'readwrite');
        const store = tx.objectStore('userCache');
        return store.put({ key, data, updated_at: new Date().toISOString() });
    }

    async getCache(key) {
        const tx = this.db.transaction(['userCache'], 'readonly');
        const store = tx.objectStore('userCache');
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result?.data);
            request.onerror = () => reject(request.error);
        });
    }

    async saveDoctors(doctors) {
        const tx = this.db.transaction(['doctors'], 'readwrite');
        const store = tx.objectStore('doctors');
        for (const doctor of doctors) {
            await store.put(doctor);
        }
    }

    async getDoctors(specialization = null) {
        const tx = this.db.transaction(['doctors'], 'readonly');
        const store = tx.objectStore('doctors');
        
        if (specialization) {
            const index = store.index('specialization');
            return new Promise((resolve, reject) => {
                const request = index.getAll(specialization);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }
        
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveHospitals(hospitals) {
        const tx = this.db.transaction(['hospitals'], 'readwrite');
        const store = tx.objectStore('hospitals');
        for (const hospital of hospitals) {
            await store.put(hospital);
        }
    }

    async getHospitals() {
        const tx = this.db.transaction(['hospitals'], 'readonly');
        const store = tx.objectStore('hospitals');
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveNGOs(ngos) {
        const tx = this.db.transaction(['ngos'], 'readwrite');
        const store = tx.objectStore('ngos');
        for (const ngo of ngos) {
            await store.put(ngo);
        }
    }

    async getNGOs() {
        const tx = this.db.transaction(['ngos'], 'readonly');
        const store = tx.objectStore('ngos');
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
}

// Initialize DB
const db = new WeCareDB();
db.init().catch(console.error);
