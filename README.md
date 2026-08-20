# 🎓 AI-Based Assignment Plagiarism Detector

An enterprise-grade, role-based platform designed for academic institutions to verify the originality and authenticity of student assignments. The system features a **multi-layer AI generation detector**, a **peer-to-peer plagiarism engine**, and an advanced **OCR vision pipeline** for digitized and handwritten assignments.

---

## 🌟 Key Capabilities

- **🔐 Role-Based Access Control (RBAC):** Dedicated portals tailored for **Students**, **Teachers**, and **Heads of Department (HOD)** with granular permissions and actionable insights.
- **👁️ Multi-Tier OCR Vision Pipeline:**
  - Robust document preprocessing: adaptive thresholding, deskewing, shadow removal, and contrast enhancement via OpenCV.
  - Neural text recognition using **Microsoft TrOCR** (`trocr-base-handwritten`) with CRAFT line segmentation.
  - High-accuracy fallbacks with **EasyOCR** and **Tesseract**.
- **🧠 Multi-Layer AI-Generated Content Detection:**
  - **Statistical Neural Engine:** Computes token-level perplexity, loss variance (burstiness), and entropy using local `distilgpt2`.
  - **Machine Learning Classification:** Trained Random Forest classifier evaluating 20+ stylistic, linguistic, and statistical features.
  - **Semantic Context Engine:** Validates subject relevance and topical alignment against course syllabi.
- **🔍 Peer-to-Peer Plagiarism Engine:**
  - TF-IDF N-gram vectorization with cosine similarity matching across submission repositories within the same subject and department.
  - Highlights matching source segments with detailed similarity breakdowns.
- **⚡ Asynchronous & Real-Time Processing:**
  - Asynchronous task execution powered by **Celery** and **Redis** for heavy OCR and ML workloads.
  - Real-time submission status tracking with animated progression indicators in the student portal.
- **📧 Password Recovery & Notifications:**
  - Token-based secure password reset workflow with branded HTML emails dispatched via SMTP.
- **📊 Institutional Analytics & Dashboards:**
  - Interactive charts (Recharts) visualizing department-wide trends, risk factor distributions, and submission statistics.

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    User([User: Student / Teacher / HOD]) -->|Interacts via Browser| Frontend[React + Vite Frontend]
    Frontend -->|REST API Requests / JWT| Backend[FastAPI Backend Server]
    
    subgraph Backend Pipeline
        Backend --> DB[(MySQL / PostgreSQL / SQLite)]
        Backend --> Redis[(Redis Broker)]
        Redis --> CeleryWorker[Celery Background Worker]
        
        CeleryWorker --> OCR[OCR Pipeline\nOpenCV + TrOCR + EasyOCR]
        CeleryWorker --> AI[AI Detection Engine\nDistilGPT2 + Random Forest]
        CeleryWorker --> Plag[Plagiarism Engine\nTF-IDF + Cosine Similarity]
        CeleryWorker --> Sem[Semantic Engine\nSubject Relevance Validation]
    end
    
    Backend --> SMTP[SMTP Mail Server]
    SMTP -->|Password Reset Emails| User
```

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, Lucide React, Recharts, React Router 7 |
| **Backend API** | FastAPI, Python 3.10+, Uvicorn, Pydantic v2 |
| **Task Queue** | Celery, Redis |
| **Database** | MySQL (PyMySQL) / PostgreSQL (psycopg3) / SQLite (via SQLAlchemy 2.0) |
| **Machine Learning & NLP** | PyTorch, Hugging Face Transformers (`distilgpt2`, `trocr`), Scikit-learn, NLTK, OpenCV |
| **Document Processing** | PyMuPDF (fitz), PyPDF2, python-docx, Pillow, EasyOCR, Pytesseract |
| **Security & Auth** | JWT (`python-jose`), Passlib (`bcrypt`), SMTP Email Verification |

---

## 📁 Repository Structure

```
├── backend/
│   ├── api/                     # FastAPI route controllers (auth, submissions, reports, analytics)
│   ├── core/                    # Core configuration, database engine, security & dependencies
│   ├── data_pipeline/           # 5-phase ML feature engineering & training pipeline
│   ├── models/                  # SQLAlchemy ORM models (User, Submission, Report)
│   ├── schemas/                 # Pydantic request/response validation models
│   ├── services/
│   │   ├── ml_services/         # Pre-trained ML classifiers, feature extractors & statistical engine
│   │   ├── ai_detection.py      # Multi-layer AI detection service
│   │   ├── email_service.py     # SMTP password reset email dispatcher
│   │   ├── ocr_service.py       # Handwritten & digital OCR extraction service
│   │   ├── plagiarism.py        # TF-IDF cosine similarity plagiarism comparator
│   │   └── text_extraction.py   # Multi-format document text extraction (.pdf, .docx, .txt, images)
│   ├── tasks/                   # Celery asynchronous task definitions
│   ├── init_mysql.py            # Database initialization script
│   ├── seed_users.py            # Demo user accounts seeding script
│   ├── requirements.txt         # Python dependencies
│   └── main.py                  # FastAPI application entry point
├── src/                         # React frontend source code
│   ├── components/              # Shared UI components (Navbar, ProtectedRoutes)
│   ├── pages/                   # Portal views (Student, Teacher, HOD, Login, Register, Password Reset)
│   ├── App.jsx                  # React application router
│   └── index.css                # Global stylesheet and custom component design tokens
├── public/                      # Static web assets
├── package.json                 # Node.js project manifest & dependencies
├── vite.config.js               # Vite build configuration
└── README.md                    # Project documentation
```

---

## 🛠️ Getting Started

### Prerequisites
- **Node.js** (v18.0 or higher) & **npm**
- **Python** (v3.10 or higher)
- **MySQL** (or PostgreSQL / SQLite)
- **Redis** (optional, recommended for async Celery processing)

---

### 1. Backend Setup

1. **Navigate to the backend directory and create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     .\venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy the `.env.example` template:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to configure your database connection and SMTP credentials:
   ```ini
   DATABASE_URL=mysql://root:password@localhost:3306/plagiarism_db
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your-secure-random-secret-key
   ```

5. **Initialize Database & Seed Demo Users:**
   ```bash
   python init_mysql.py
   python seed_users.py
   ```

6. **Start the Backend API Server:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The Swagger interactive API documentation will be available at `http://localhost:8000/docs`.*

---

### 2. Frontend Setup

1. **Open a new terminal in the project root directory:**
   ```bash
   npm install
   ```

2. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   Navigate to `http://localhost:5173` in your browser.

3. **Build for Production:**
   ```bash
   npm run build
   ```

---

### 3. (Optional) Start Celery Background Worker

To enable asynchronous background processing for document uploads and deep ML inference:
```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info --pool=threads
```

---

## 👥 Demo Credentials

The `seed_users.py` script provisions the following accounts:

| Role | Email | Password | Description |
|---|---|---|---|
| **Student** | `student@demo.edu` | `pass123` | Upload assignments, view plagiarism scores, inspect AI detection breakdowns & OCR previews |
| **Teacher** | `teacher@demo.edu` | `pass123` | Review batch submissions, flag suspect papers, inspect side-by-side similarities |
| **HOD** | `hod@demo.edu` | `pass123` | Institutional analytics, batch comparison, risk factor breakdown & departmental metrics |

---

## 🧪 Testing & Verification

Run backend diagnostic and unit test suites:
```bash
cd backend
python test_ai_layers.py
python test_forgot_password.py
python test_v2_integration.py
```

---

## 📄 License

This project is developed for educational and institutional research purposes.

