<!--
If you are viewing this on GitHub, images are in ./for_redme
-->

# WeCare (WeCare Medical Service App)

Offline-first medical consultation and triage web app designed for rural / low-connectivity environments.

## Team & Institute

- Green University of Bangladesh
- Team: GreenU_Tensors
- Members:
   - Samim Reza
   - Fahim Sarker Mridul
   - Maheer Jabin Priya

## What We Built

WeCare is a local-first medical service app that can run inside a small region (LAN / router / community network) and still remain useful when the internet is unavailable.

For this project, we ran the AI model locally on our PC: Qwen3-VL-2B served via Ollama.

When internet is available, the system uses the MySQL server database as the central source of truth; when internet is not available, it stores data locally in IndexedDB and syncs to MySQL once connectivity returns.

- When online, the app uses the backend AI (vision + text) and syncs consultation data to a central database.
- When offline, the app continues to operate using browser storage (IndexedDB) and cached resources, then auto-syncs when connectivity returns.

## Key Features

- AI medical consultation (text + optional image)
   - Image analysis is supported online.
   - Offline mode supports text-only triage (image-only consultations require internet).

   ![User prompt page](for_redme/user_prompt_page.png)

- Offline-first storage and caching
   - Consultations are saved in IndexedDB when offline
   - Doctors / Hospitals / NGOs are cached locally for browsing
   - Auto-sync triggers when the device comes back online
- Priority-based triage
   - Priority levels: low / medium / high / critical
- First aid guidance
   - Output includes immediate first-aid suggestions
- Patient context control
   - User can choose whether the AI should use previous medical history and recent chat context
- Recommended doctors
   - The response includes a recommended specialization + matching doctor list from the database

   ![Prompt result](for_redme/prompt_result.png)

   ![Suggested doctor list](for_redme/suggest_doctor.png)

- Admin case management dashboard
   - Track cases as: pending → under supervision → solved
   - Admin can “take case”, “release case”, and “mark solved”

   ![Admin panel](for_redme/admin_panel.png)

   ![Admin summary](for_redme/summary_from_admin.png)

- User history & privacy controls
   - Users can view their consultation history and delete single or multiple consultations

   ![User history page](for_redme/user_history_page.png)

- Better UX while waiting
   - Shows rotating encouraging messages during AI processing
- Bilingual response (Bangla/English)
   - If a user prompts in Bengali (বাংলা), the AI responds in Bengali
   - If a user prompts in English, the AI responds in English

## UI Highlights

### Authentication

![User login system](for_redme/user_login_system.png)

### Resources Directory

![Doctors list](for_redme/doctors_list.png)

### Consultation Output Format

![Consultation report](for_redme/consultation_report.png)

## Architecture (Repo-Accurate)

- Frontend: vanilla HTML/CSS/JS + PWA (service worker)
- Backend: FastAPI
- AI: Qwen3-VL-2B running locally via Ollama (`/api/generate`)
- Database: MySQL (SQLAlchemy)
- Offline storage: IndexedDB (consultations + cached doctors/hospitals/ngos)
- Auth: JWT
- Case workflow: Consultation status + supervising admin

## How Offline Sync Works

- Online
   - Consultations are sent to `POST /api/consultation`
   - Data is stored centrally in the MySQL server database
   - Results return immediately to the user
   - Doctors/hospitals/ngos lists are fetched and cached in IndexedDB
- Offline
   - The UI generates a basic triage result and saves it to IndexedDB as “unsynced”
- Back online
   - The frontend automatically pushes unsynced consultations to `POST /api/sync/consultations`
   - Synced items are marked as synced locally

## Run Locally

### Prerequisites

- Python 3.10+
- MySQL server
- Ollama installed and running (for AI)

### 1) Setup Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

- Copy `.env.example` → `.env` and update the values for your machine.

### 3) Initialize DB and seed demo data

```bash
source venv/bin/activate
python seed_data.py
```

Optional (creates an admin user):

```bash
source venv/bin/activate
python create_admin.py
```

### 4) Start Ollama + pull model

```bash
ollama pull qwen3-vl:2b
ollama serve
```

### 5) Start the server

```bash
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 6) Open in browser

- Landing: `http://localhost:8000/`
- App: `http://localhost:8000/index.html`
- Admin: `http://localhost:8000/admin.html`

## Run on a Local Network (No Internet)

This project is designed to work in a community/local-LAN setup (similar to a small local server in a village/area).

1. Start the server with `--host 0.0.0.0`
2. Find the server PC’s LAN IP (example): `172.20.221.57`
3. Other devices connected to the same router open: `http://<LAN-IP>:8000`

Notes:
- If other devices cannot connect, check firewall rules and router “AP/client isolation”.

## API Overview

- Auth
   - `POST /api/auth/register`
   - `POST /api/auth/login`
   - `GET /api/auth/me`
- Consultation
   - `POST /api/consultation` (text + optional image)
   - `GET /api/consultations/history`
   - `DELETE /api/consultations/{id}`
   - `POST /api/consultations/delete-multiple`
   - `POST /api/sync/consultations` (offline → online sync)
- Resources
   - `GET /api/doctors`
   - `GET /api/hospitals`
   - `GET /api/ngos`
- Admin case management
   - `GET /api/admin/stats`
   - `GET /api/admin/consultations`
   - `POST /api/admin/consultations/{id}/take-case`
   - `POST /api/admin/consultations/{id}/release-case`
   - `POST /api/admin/consultations/{id}/mark-solved`

## Vision / Next Steps

- “Local server per region” deployment model (LAN-based clinic/community server)
- Smarter routing to the nearest facility/hospital when internet becomes available
- Replace / extend Ollama with a vLLM-based backend in future deployments

## License

License is not included in this repository yet.

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
