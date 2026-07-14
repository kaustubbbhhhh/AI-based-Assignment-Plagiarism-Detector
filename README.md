# AI-Based Assignment Plagiarism Detector

An intelligent, role-based platform designed to verify the originality of student assignments using Natural Language Processing (NLP). The system detects both **AI-generated content** and **peer-to-peer plagiarism**.

## 🌟 Key Features
- **Role-Based Access Control (RBAC):** Dedicated, secure portals for Students, Teachers, and HODs.
- **Dynamic Registration:** Custom form fields based on the selected role (e.g., Enrollment No. for students, dynamic Branch/Subject assignment for teachers).
- **Multi-Format Processing:** Capable of extracting and analyzing text from `.pdf`, `.docx`, and `.txt` files.
- **Dual-Engine Analysis Pipeline:** 
  - **AI Detection:** Analyzes word entropy and sentence burstiness to identify machine-generated text.
  - **Plagiarism Detection:** Uses TF-IDF vectorization and Cosine Similarity to compare a submission against peers who submitted for the same subject.
- **Comprehensive Dashboards:** Visualizations including pie charts and bar graphs for segmenting data by student, section, and institutional batch.

## 🚀 Tech Stack
- **Frontend:** React.js, Vite, Tailwind CSS (via Lucide React/Recharts)
- **Backend:** FastAPI, Python, SQLAlchemy
- **Database:** SQLite (Development mode)
- **NLP Toolkit:** Scikit-learn, NLTK, PyPDF2, python-docx

## 🛠️ How to Run Locally

### 1. Start the Backend
Open a terminal in the `backend` folder and run up the server:
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```
*(Alternatively, you can just double-click the `start_backend.bat` file located in the root directory).*

### 2. Start the Frontend
Open a second terminal in the root project folder and start the Vite dev server:
```bash
npm run dev
```
Navigate to `http://localhost:5174` in your browser.

### 3. Demo Credentials
If the database was just initialized, you can seed demo data by running `python seed_users.py` in the `backend` folder.
| Role | Email | Password |
|------|-------|----------|
| **Student** | `student@demo.edu` | `pass123` |
| **Teacher** | `teacher@demo.edu` | `pass123` |
| **HOD**     | `hod@demo.edu`     | `pass123` |

---

## 🗺️ Roadmap & Unimplemented Features (Not Executed Yet)

The following features have been identified as critical architectural upgrades but are currently **not executed yet**:

1. **Semantic Subject/Context Matching:** 
   *(Identified Edge Case)* Currently, a student could select "Subject A" in the UI but upload a document about "Subject B". The system will process it and likely give a 0% plagiarism score because it doesn't match other Subject A documents.
   **Solution to be built:** Implement a Semantic Relevance Engine that compares the extracted text against the Teacher's predefined syllabus/keywords for that subject, immediately flagging off-topic submissions before they even reach the plagiarism engine.

2. **Transformer-Based AI Detection Setup:** 
   The system currently uses a lightweight mathematical heuristic approach to keep local development fast. Upgrading to a deep-learning architecture (like GPT-2 text perplexity scoring) requires re-introducing heavy ML libraries (`torch`, `transformers`).

3. **Asynchronous Worker Queue:** 
   Transition the synchronous API file-processing pipeline back to Celery + Redis for true background processing, preventing browser timeouts when handling massive batches of documents concurrently.

4. **Exportable PDF Reports:** 
   Add capability for Teachers and HODs to generate and download physical `.pdf` analytical reports of the dashboard data using `reportlab`.
