# AI Plagiarism Detector: Data Mining & Forensic Roadmap

This document outlines the strategic implementation of Data Mining techniques to transition the system from a "reactive" detector to a "proactive" academic integrity platform.

## Phase 1: Data Infrastructure for Analytics
**Goal:** Prepare the existing relational data for high-performance mining algorithms.

*   **Analytics View (Flattened Data):** Create a database view that joins `Submissions`, `Reports`, and `Users` to allow one-pass scanning.
*   **Feature Extraction Pipeline:** Implement a background worker (Celery) that extracts "mining features" from every report:
    *   Syntactic features (average sentence length, punctuation density).
    *   Lexical features (vocabulary richness, TTR - Type-Token Ratio).
    *   Temporal features (submission delay from deadline, time-of-day).
*   **Vector Storage:** Store `visual_hash` and text embeddings in a format suitable for fast similarity searches (e.g., using `scipy.spatial` or a vector index).

## Phase 2: Social Network Mining (Cheating Ring Detection)
**Goal:** Identify students who are not just copying from the web, but are sharing work among themselves.

*   **Similarity Graph Construction:** 
    *   Build a graph where **Nodes = Students** and **Edges = High Similarity Submissions**.
    *   Weight edges based on the percentage of shared content.
*   **Community Detection:** Use the **Louvain Algorithm** to find clusters of students who frequently exchange assignments.
*   **Visual Hash Matching:** Cross-reference students who upload the same photo (identical `visual_hash`) but for different subject IDs.

## Phase 3: Stylometric Profiling (Authorship Verification)
**Goal:** Detect "Contract Cheating" (where a student pays someone else to write their work) by tracking style shifts.

*   **Student Baseline Creation:** Mine the first 3 submissions of every student to create a "Writing Fingerprint."
*   **Anomaly Detection:** 
    *   Use **Isolation Forest** to flag submissions that deviate significantly from the student's historical fingerprint.
    *   *Metric:* If a student's "Vocabulary Complexity" jumps by >3 standard deviations, trigger a "Manual Review" flag.
*   **Cross-Subject Analysis:** Compare a student's style in 'Computer Science' vs 'English Literature' to ensure consistent authorship.

## Phase 4: Temporal & Behavioral Mining
**Goal:** Correlate student behavior with plagiarism risk to provide early interventions.

*   **Sequential Pattern Mining:** Analyze the "path to submission."
    *   *Example:* Do students who visit the dashboard 10+ times before uploading have lower plagiarism than those who upload on their first visit?
*   **Predictive Risk Scoring:** 
    *   Train a **Random Forest Classifier** to predict the likelihood of a submission being AI-generated based on:
        *   Time until deadline.
        *   Previous plagiarism history.
        *   Submission time (e.g., 3:00 AM).
*   **Heatmap Analytics:** Generate "Crunch Time" heatmaps for teachers to see when the most academic integrity violations occur.

## Phase 5: Institutional Insights & Dashboard
**Goal:** Provide macro-level data to school administrators.

*   **Subject Vulnerability Ranking:** Rank subjects by the frequency of AI vs. Web-based plagiarism.
*   **Source Attribution Mining:** Identify "Top 10" websites/tools being used by the student body (e.g., specific Discord bots, obscure study-help sites).
*   **ROI Analytics:** Calculate "Hours Saved" for teachers by comparing automated detection vs. manual grading time.

---

## Technical Stack Requirements
| Component | Technology |
| :--- | :--- |
| **Data Processing** | `Pandas`, `NumPy` |
| **Machine Learning** | `Scikit-Learn` |
| **Graph Analysis** | `NetworkX` |
| **Visualizations** | `Recharts` (Frontend), `Plotly` (Backend) |
| **Task Scheduling** | `Celery` + `Redis` |
