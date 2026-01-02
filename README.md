# Forensic CTF Platform

A production-grade, story-driven forensic simulation CTF platform designed for **serious cybersecurity practitioners**.

---

## 🎯 Philosophy

This is **NOT** a casual CTF platform. This is a forensic simulation environment where:

### Story-Driven, Case-Based Challenges
Every challenge is a complete forensic scenario with narrative background, investigation objectives, and realistic artifacts. Participants don't just "find the flag" – they conduct actual investigations.

### No Static Flags
**Static flags are forbidden.** Every flag is dynamically generated using HMAC:

```
flag = HMAC(secret, user_id + case_id + semantic_truth_hash)
```

This means:
- Your flag won't work for anyone else
- You can't use someone else's flag
- Write-ups become learning resources, not cheat sheets

### Anti-Writeup by Design
The platform is architecturally designed to prevent flag sharing:
- Per-user, per-case unique flags
- Semantic truth (actual answer) is never stored in plaintext
- Constant-time verification prevents timing attacks
- Rate limiting prevents brute force attempts

### Noise-Heavy, Realism-First
Cases include:
- Red herrings and misleading data
- Realistic noise in artifacts
- Multiple investigation paths
- Industry-standard evidence formats

### Built for Practitioners
- Invite-only registration
- No gamification gimmicks
- Focus on forensic methodology
- Professional-grade infrastructure

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Forensic CTF Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   FastAPI    │    │  PostgreSQL  │    │    MinIO     │       │
│  │   Backend    │───▶│   Database   │    │   Storage    │       │
│  │   (Python)   │    │              │    │   (S3-API)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                    Docker Network                     │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT + Argon2 password hashing |
| Storage | MinIO (S3-compatible) |
| Config | Pydantic Settings |
| Container | Docker + docker-compose |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd forensic-ctf-platform

# Copy environment template
cp .env.example .env

# Generate secure keys
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"
python -c "import secrets; print(f'FLAG_SECRET_KEY={secrets.token_hex(32)}')"

# Update .env with generated keys
```

### 2. Start Services

```bash
# Development mode (with hot-reload)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create initial admin (see scripts)
docker-compose exec backend python scripts/create_admin.py
```

### 4. Access the Platform

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

---

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register (invite required) |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/validate-invite` | Validate invite code |

### Cases
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cases` | List cases |
| GET | `/api/v1/cases/{id}` | Get case details |
| GET | `/api/v1/cases/{id}/artifacts` | List case artifacts |
| GET | `/api/v1/cases/{id}/artifacts/{id}/download` | Download artifact |

### Submissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/submissions/submit` | Submit answer |
| GET | `/api/v1/submissions/history` | Get submission history |
| GET | `/api/v1/submissions/leaderboard` | Get leaderboard |

### Admin (Requires admin privileges)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/cases` | Create case |
| PUT | `/api/v1/admin/cases/{id}` | Update case |
| DELETE | `/api/v1/admin/cases/{id}` | Delete case |
| POST | `/api/v1/admin/invite-codes` | Generate invite code |
| GET | `/api/v1/admin/stats` | Platform statistics |

---

## 🔐 Security Model

### Flag Generation

```python
# Semantic truth (answer) is hashed immediately
semantic_truth_hash = SHA256(normalize(answer))

# Flag is generated per-user, per-case
flag = HMAC-SHA256(
    key=FLAG_SECRET_KEY,
    message=f"{user_id}:{case_id}:{case_salt}:{semantic_truth_hash}"
)

# Formatted as: FORENSIC{base64_truncated_hmac}
```

### Why This Matters

1. **No database contains flags**: Flags are computed on-demand
2. **No sharing possible**: Each user's flag is cryptographically unique
3. **Write-ups are safe**: Sharing the flag from a write-up won't help others
4. **Answer integrity**: The actual answer hash is compared, not the flag

### Password Security

- Argon2id hashing (memory-hard, GPU-resistant)
- Configurable time/memory/parallelism costs
- Automatic rehashing on parameter changes

### Rate Limiting

- Submissions: 10 per minute per user
- Authentication: 5 per minute per IP
- Admin endpoints: Standard API limits

---

## 🛠️ Development

### Local Development (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with local database/storage settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_flag_engine.py -v
```

### Code Quality

```bash
# Format code
black app/

# Lint
ruff check app/

# Type checking
mypy app/
```

---

## 📁 Project Structure

```
forensic-ctf-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth/         # Authentication endpoints
│   │   │       ├── cases/        # Case management endpoints
│   │   │       ├── submissions/  # Submission endpoints
│   │   │       └── admin/        # Admin endpoints
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic Settings
│   │   │   ├── security.py       # Auth & JWT
│   │   │   ├── crypto.py         # Flag generation
│   │   │   └── dependencies.py   # FastAPI dependencies
│   │   ├── db/
│   │   │   ├── base.py           # SQLAlchemy base
│   │   │   ├── models.py         # ORM models
│   │   │   └── session.py        # Database session
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/
│   │   │   ├── flag_engine.py    # Flag logic
│   │   │   ├── case_engine.py    # Case logic
│   │   │   └── user_service.py   # User logic
│   │   └── utils/
│   │       ├── rate_limiter.py   # Rate limiting
│   │       └── storage.py        # S3/MinIO client
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # Test suite
│   ├── main.py                   # Application entry
│   └── requirements.txt
├── docker/
│   ├── Dockerfile.backend        # Production Dockerfile
│   ├── Dockerfile.dev            # Development Dockerfile
│   ├── nginx.conf                # Nginx configuration
│   └── init-db.sql               # Database initialization
├── docker-compose.yml            # Development compose
├── docker-compose.prod.yml       # Production compose
├── .env.example                  # Environment template
└── README.md
```

---

## 🚢 Production Deployment

### 1. Configure Production Environment

```bash
# Use production compose file
cp .env.example .env.prod

# Generate strong secrets
python -c "import secrets; print(secrets.token_hex(32))"

# Set DEBUG=false
# Configure real domain
# Set up SSL certificates
```

### 2. Deploy

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 3. SSL Certificates

Place your SSL certificates in `docker/ssl/`:
- `fullchain.pem`
- `privkey.pem`

Or use Let's Encrypt with Certbot.

---

## 📝 Creating Cases

Cases are created via the admin API. Here's the workflow:

### 1. Create the Case

```bash
curl -X POST http://localhost:8000/api/v1/admin/cases \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Insider Threat",
    "description": "Investigate a potential data exfiltration incident",
    "story_background": "On March 15th, the security team detected unusual...",
    "investigation_objectives": "Determine: 1) What data was accessed...",
    "difficulty": "intermediate",
    "semantic_truth": "john.doe@company.com",
    "points": 500
  }'
```

### 2. Upload Artifacts

```bash
# Get upload URL
curl -X POST http://localhost:8000/api/v1/admin/cases/{case_id}/artifacts/upload-url \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"filename": "disk_image.E01", "file_size": 10485760}'

# Upload to presigned URL
curl -X PUT "<presigned_url>" --upload-file disk_image.E01

# Create artifact record
curl -X POST http://localhost:8000/api/v1/admin/cases/{case_id}/artifacts \
  -H "Authorization: Bearer <admin_token>" \
  -F "artifact_id=<id>" \
  -F "name=Workstation Disk Image" \
  -F "artifact_type=disk_image" \
  ...
```

---

## ⚠️ Why Static Flags Are Forbidden

Traditional CTF platforms use static flags like `CTF{h4ck3r_m4n}`. This approach has fundamental problems:

### 1. Flag Sharing Epidemic
Static flags can be copied and shared. Once one person solves a challenge, everyone can "solve" it by copying the flag.

### 2. Write-ups Become Cheat Sheets
Static flags in write-ups allow direct copying without understanding.

### 3. No Learning Verification
Submitting a copied flag proves nothing about the submitter's skills.

### 4. Unfair Competition
Shared flags undermine fair competition and ranking integrity.

### Our Solution
HMAC-based flags ensure that even if someone shares their flag or writes detailed solutions, others still need to solve the case themselves to get their own unique flag.

---

## �️ Frontend

### The Investigation Aesthetic

The frontend embodies the serious, focused nature of digital forensics work:

- **No Gamification**: No badges, achievements, or leaderboards
- **No Colors**: Pure grayscale palette - cold, professional
- **No Animations**: Zero transitions - information appears instantly
- **Typography First**: Monospace fonts, clear hierarchy
- **Serious Tone**: You're not "playing a game", you're reviewing case files

**It feels like opening a sealed envelope marked "CONFIDENTIAL".**

### Tech Stack
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- JWT authentication with http-only cookies

### Running Frontend
```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3001

See [frontend/README.md](frontend/README.md) for complete documentation.

---

## �📄 License

[Your License Here]

---

## 🤝 Contributing

[Contribution guidelines]

---

Built with 🔐 for the forensics community.
