from database import SessionLocal, init_db
from models import Doctor, Hospital, NGO

# Initialize database
init_db()

db = SessionLocal()

# Seed Doctors
doctors_data = [
    {
        "name": "Dr. Fatima Rahman",
        "specialization": "General Medicine",
        "qualification": "MBBS, MD",
        "phone": "+880-1711-123456",
        "hospital": "Rangamati General Hospital",
        "available_days": "Mon, Wed, Fri",
        "fee": 500,
        "address": "Rangamati, Chittagong Hill Tracts",
        "latitude": "22.6533",
        "longitude": "92.1985"
    },
    {
        "name": "Dr. Kamal Hossain",
        "specialization": "Pediatrics",
        "qualification": "MBBS, DCH",
        "phone": "+880-1712-234567",
        "hospital": "Bandarban District Hospital",
        "available_days": "Tue, Thu, Sat",
        "fee": 600,
        "address": "Bandarban, Chittagong Hill Tracts",
        "latitude": "22.1953",
        "longitude": "92.2183"
    },
    {
        "name": "Dr. Ayesha Begum",
        "specialization": "Gynecology",
        "qualification": "MBBS, FCPS",
        "phone": "+880-1713-345678",
        "hospital": "Khagrachari Sadar Hospital",
        "available_days": "Mon, Tue, Thu",
        "fee": 700,
        "address": "Khagrachari, Chittagong Hill Tracts",
        "latitude": "23.1322",
        "longitude": "91.9490"
    },
    {
        "name": "Dr. Ripon Das",
        "specialization": "Dermatology",
        "qualification": "MBBS, DDV",
        "phone": "+880-1714-456789",
        "hospital": "Cox's Bazar Medical College",
        "available_days": "Wed, Fri, Sat",
        "fee": 800,
        "address": "Cox's Bazar",
        "latitude": "21.4272",
        "longitude": "92.0058"
    },
    {
        "name": "Dr. Nusrat Jahan",
        "specialization": "Cardiology",
        "qualification": "MBBS, MD (Cardiology)",
        "phone": "+880-1715-567890",
        "hospital": "Chittagong Medical College",
        "available_days": "Mon, Wed, Fri",
        "fee": 1000,
        "address": "Chittagong City",
        "latitude": "22.3569",
        "longitude": "91.7832"
    },
    {
        "name": "Dr. Rafiqul Islam",
        "specialization": "Orthopedics",
        "qualification": "MBBS, MS (Ortho)",
        "phone": "+880-1716-678901",
        "hospital": "Rangamati General Hospital",
        "available_days": "Tue, Thu, Sat",
        "fee": 900,
        "address": "Rangamati, Chittagong Hill Tracts",
        "latitude": "22.6533",
        "longitude": "92.1985"
    },
    {
        "name": "Dr. Sharmila Chakma",
        "specialization": "ENT",
        "qualification": "MBBS, DLO",
        "phone": "+880-1717-789012",
        "hospital": "Bandarban District Hospital",
        "available_days": "Mon, Wed, Fri",
        "fee": 650,
        "address": "Bandarban, Chittagong Hill Tracts",
        "latitude": "22.1953",
        "longitude": "92.2183"
    }
]

# Seed Hospitals
hospitals_data = [
    {
        "name": "Rangamati General Hospital",
        "type": "Government",
        "address": "Hospital Road, Rangamati, Chittagong Hill Tracts",
        "phone": "+880-351-62324",
        "emergency_available": True,
        "latitude": "22.6533",
        "longitude": "92.1985",
        "facilities": "Emergency, ICU, Surgery, Lab, X-Ray"
    },
    {
        "name": "Bandarban District Hospital",
        "type": "Government",
        "address": "Bandarban Sadar, Bandarban, Chittagong Hill Tracts",
        "phone": "+880-361-62233",
        "emergency_available": True,
        "latitude": "22.1953",
        "longitude": "92.2183",
        "facilities": "Emergency, General Ward, Lab, Pharmacy"
    },
    {
        "name": "Khagrachari Sadar Hospital",
        "type": "Government",
        "address": "Khagrachari Sadar, Khagrachari, Chittagong Hill Tracts",
        "phone": "+880-371-61325",
        "emergency_available": True,
        "latitude": "23.1322",
        "longitude": "91.9490",
        "facilities": "Emergency, Maternity Ward, Surgery, Lab"
    },
    {
        "name": "Hill View Clinic",
        "type": "Private",
        "address": "Main Road, Rangamati",
        "phone": "+880-1811-234567",
        "emergency_available": False,
        "latitude": "22.6550",
        "longitude": "92.2000",
        "facilities": "OPD, Diagnostic Center, Pharmacy"
    },
    {
        "name": "Green Valley Medical Center",
        "type": "Private",
        "address": "Bandarban Town, Bandarban",
        "phone": "+880-1812-345678",
        "emergency_available": True,
        "latitude": "22.1970",
        "longitude": "92.2200",
        "facilities": "24/7 Emergency, ICU, Surgery, Lab"
    }
]

# Seed NGOs
ngos_data = [
    {
        "name": "BRAC Health Programme",
        "services": "Primary healthcare, maternal health, TB/malaria treatment, health education",
        "address": "Multiple locations across Hill Tracts",
        "phone": "+880-2-9881265",
        "email": "health@brac.net",
        "latitude": "22.6533",
        "longitude": "92.1985",
        "working_areas": "Rangamati, Bandarban, Khagrachari"
    },
    {
        "name": "Friendship NGO",
        "services": "Mobile health clinics, telemedicine, emergency medical transport",
        "address": "Bandarban and remote areas",
        "phone": "+880-1713-098765",
        "email": "info@friendship.ngo",
        "latitude": "22.1953",
        "longitude": "92.2183",
        "working_areas": "Bandarban, Remote villages"
    },
    {
        "name": "Hill Women's Federation",
        "services": "Maternal health, family planning, women's health awareness",
        "address": "Khagrachari Town",
        "phone": "+880-1714-567890",
        "email": "hillwomen@gmail.com",
        "latitude": "23.1322",
        "longitude": "91.9490",
        "working_areas": "Khagrachari, Rangamati"
    },
    {
        "name": "Red Crescent Society - CHT Branch",
        "services": "First aid training, emergency medical support, ambulance service",
        "address": "Rangamati, Chittagong Hill Tracts",
        "phone": "+880-351-62456",
        "email": "chtbranch@redcrescent.org.bd",
        "latitude": "22.6533",
        "longitude": "92.1985",
        "working_areas": "All three hill districts"
    },
    {
        "name": "Save the Children - Bangladesh",
        "services": "Child health, nutrition programs, vaccination campaigns",
        "address": "Bandarban District",
        "phone": "+880-1715-678901",
        "email": "bangladesh@savethechildren.org",
        "latitude": "22.1953",
        "longitude": "92.2183",
        "working_areas": "Bandarban, remote villages"
    }
]

# Insert data
try:
    # Clear existing data
    db.query(Doctor).delete()
    db.query(Hospital).delete()
    db.query(NGO).delete()

    # Insert doctors
    for doc_data in doctors_data:
        doctor = Doctor(**doc_data)
        db.add(doctor)

    # Insert hospitals
    for hosp_data in hospitals_data:
        hospital = Hospital(**hosp_data)
        db.add(hospital)

    # Insert NGOs
    for ngo_data in ngos_data:
        ngo = NGO(**ngo_data)
        db.add(ngo)

    db.commit()
    print("✅ Seed data inserted successfully!")
    print(f"   - {len(doctors_data)} doctors")
    print(f"   - {len(hospitals_data)} hospitals")
    print(f"   - {len(ngos_data)} NGOs")

except Exception as e:
    db.rollback()
    print(f"❌ Error inserting seed data: {e}")
finally:
    db.close()
