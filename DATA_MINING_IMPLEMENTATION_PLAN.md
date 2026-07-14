# Data Mining & Forensic Analytics: Implementation Plan

This document details the architecture and technical approach for implementing the Advanced Data Mining & Forensic Analytics Layer in the AI Plagiarism Detector.

---

## 1. System Architecture

The data mining layer acts as a post-processing analytics engine running on the server. It uses `pandas`, `scikit-learn`, and `networkx` to parse, model, and visualize trends from the existing relational database tables (`users`, `submissions`, `reports`).

```
+------------------+     +------------------------+     +-----------------------------+
|   Database DB    | --> |   Data Mining Engine   | --> |     FastAPI REST API        |
| (Reports/Subs)   |     | (pandas, networkx, ML) |     |  (/api/analytics/...)       |
+------------------+     +------------------------+     +-----------------------------+
                                                                       |
                                                                       v
                                                        +-----------------------------+
                                                        |      React Frontend         |
                                                        | (HOD Forensic Dashboard)    |
                                                        +-----------------------------+
```

---

## 2. Core Forensic Modules

### A. Social Network Mining (Cheating Rings)
- **Concept:** Identifies groups of students who copy from each other instead of external sources.
- **Implementation:**
  - Build a graph $G = (V, E)$ where nodes $V$ are students.
  - Edges $E$ represent high-similarity links. An edge is created between Student A and Student B if:
    - They have submitted assignments (same subject) with text cosine similarity $> 30\%$.
    - They uploaded the exact same image (`visual_hash` matches).
  - Use `networkx.connected_components` to extract clusters of cooperating students.
  - Edge weights correspond to the maximum similarity between their submissions.

### B. Stylometric Profiling (Authorship Verification)
- **Concept:** Detects "contract cheating" (where a student hires a third party to write their paper) by profiling writing style over time.
- **Implementation:**
  - For each student, parse the `processed_text` of all past submissions.
  - Extract the following lexical and syntactic features:
    - **Average word length:** Mean character count per word.
    - **Average sentence length:** Mean word count per sentence.
    - **Vocabulary complexity (Type-Token Ratio - TTR):** Count of unique words divided by total words (measures lexical variety).
    - **Punctuation density:** Number of punctuation marks (`,`, `.`, `!`, `?`, `;`, `:`) divided by total character count.
  - If a student has $\ge 3$ past submissions, calculate the mean ($\mu$) and standard deviation ($\sigma$) for each metric to establish their baseline "fingerprint".
  - For any new submission, calculate its distance in standard deviations from their baseline. If the average Z-score distance is $> 2.0$, flag the submission as a **Stylometric Anomaly** (high style-shift risk).

### C. Temporal & Behavioral Risk
- **Concept:** Connects student behaviors (like submission hours) to plagiarism rates to discover institutional vulnerabilities.
- **Implementation:**
  - Bin all submissions by hour of the day (0–23).
  - Calculate average `plagiarism_score` and `ai_score` per hour.
  - Correlate submission "rush hours" (e.g., midnight to 4 AM) with high plagiarized content.

### D. Institutional ROI & Subject Vulnerability
- **Concept:** Provide HODs with high-level reporting on subject risk and teacher time saved.
- **Implementation:**
  - **ROI Formula:** Total hours saved = $\text{Total submissions} \times 0.25\text{ hours}$ (representing a conservative 15 minutes of grading/checking time per file).
  - **Subject Vulnerability:** Group reports by subject and compute average AI score, average plagiarism score, and count of flagged/mixed content.

---

## 3. Database & REST API Specs

### Endpoints to Add:
1. `GET /api/analytics/summary`
   - Returns counts of total evaluated, anomalous style shifts, active cheating rings, and ROI hours saved.
2. `GET /api/analytics/cheating-rings`
   - Returns clustered lists of students who have high-similarity links.
3. `GET /api/analytics/stylometric-anomalies`
   - Returns a list of reports where the latest text style deviates severely from the student's historical average.
4. `GET /api/analytics/risk-factors`
   - Returns submission risk binned by hour of the day.
5. `GET /api/analytics/insights`
   - Returns subject rankings and ROI.

---

## 4. UI Dashboard Details

In `HODPortal.jsx`, a new **Forensic Analytics** section will be accessible via a toggle button. This view displays:
1. **Analytics Summary Cards:** Beautiful glassmorphism cards tracking active cheating rings, style anomalies, and teacher hours saved.
2. **Cheating Rings Interactive Network List:** Groups of students clustered by matching visual hashes or high text similarity, complete with maximum matched percentages and the specific subjects involved.
3. **Stylometric Anomalies Table:** Displays students, subjects, dates, and calculated Z-score deviations (e.g., 3.4σ shift) with details on which parameter shifted the most.
4. **Behavioral Heatmap Chart:** A responsive `BarChart` using Recharts to visualize plagiarism risk against the time of day.
5. **Subject Vulnerability Roster:** A ranked grid showing which subjects have the highest plagiarism density.
