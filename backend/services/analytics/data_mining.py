"""
Advanced Data Mining & Forensic Analytics Service.
Implements:
1. Social Network Mining (Cheating Ring Detection)
2. Stylometric Profiling (Authorship Verification & Anomaly Detection)
3. Temporal & Behavioral Risk Modeling
4. Institutional Insights & ROI Analytics
"""

import logging
import re
import string
from collections import defaultdict
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import networkx as nx
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.submission import Submission
from models.report import Report
from models.user import User

logger = logging.getLogger(__name__)

# --- Helper functions for Stylometrics ---
def extract_stylometrics(text: str) -> Dict[str, float]:
    """
    Extracts lexical and syntactic stylometric features from text:
    - Average Word Length
    - Average Sentence Length
    - Vocabulary Complexity (Type-Token Ratio / TTR)
    - Punctuation Density
    """
    if not text or len(text.strip()) < 10:
        return {
            "word_length": 0.0,
            "sentence_length": 0.0,
            "ttr": 0.0,
            "punctuation_density": 0.0
        }

    words = text.split()
    total_words = len(words)
    
    if total_words == 0:
        return {"word_length": 0.0, "sentence_length": 0.0, "ttr": 0.0, "punctuation_density": 0.0}

    # 1. Average Word Length (chars per word)
    total_chars_in_words = sum(len(w.strip(string.punctuation)) for w in words)
    avg_word_length = total_chars_in_words / total_words

    # 2. Average Sentence Length (words per sentence)
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    total_sentences = len(sentences)
    avg_sentence_length = total_words / max(1, total_sentences)

    # 3. Vocabulary Complexity (Type-Token Ratio)
    cleaned_words = [w.lower().strip(string.punctuation) for w in words]
    cleaned_words = [w for w in cleaned_words if w]
    unique_words = len(set(cleaned_words))
    ttr = unique_words / max(1, len(cleaned_words))

    # 4. Punctuation Density
    punctuation_chars = set(string.punctuation)
    punct_count = sum(1 for c in text if c in punctuation_chars)
    punct_density = punct_count / len(text) if len(text) > 0 else 0.0

    return {
        "word_length": avg_word_length,
        "sentence_length": avg_sentence_length,
        "ttr": ttr,
        "punctuation_density": punct_density
    }


# --- Analytics Core functions ---

def get_cheating_rings(db: Session) -> List[Dict[str, Any]]:
    """
    Groups students into connected cheating components (rings) based on:
    - Dual text cosine similarity > 30% inside the same subject
    - Exact matching visual hashes of uploaded documents (visual plagiarism)
    """
    # Fetch all completed submissions with reports and student details
    records = (
        db.query(Submission, Report, User)
        .join(Report, Submission.id == Report.submission_id)
        .join(User, Submission.student_id == User.id)
        .all()
    )

    if not records:
        return []

    # Map student ID -> Name, enrollment, section details
    student_map = {}
    for sub, rep, user in records:
        student_map[user.id] = {
            "id": user.id,
            "name": user.name,
            "enrollment_no": user.enrollment_no or f"STU{user.id:04d}",
            "section": user.section or "N/A"
        }

    # Build student similarity graph
    G = nx.Graph()
    for sid in student_map.keys():
        G.add_node(sid)

    # Group records by subject to perform localized plagiarism matching
    subject_groups = defaultdict(list)
    for sub, rep, user in records:
        subject_groups[sub.subject].append((sub, rep, user))

    # 1. Text Similarity Matching per Subject
    for subject, items in subject_groups.items():
        if len(items) < 2:
            continue

        texts = [item[1].processed_text or "" for item in items]
        
        # Check if there's any actual text content to avoid TF-IDF empty vocabulary error
        has_content = any(len(t.strip()) > 5 for t in texts)
        if not has_content:
            continue
            
        # Fit TF-IDF on all texts in this subject
        try:
            vectorizer = TfidfVectorizer(max_features=2500, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(texts)
            sim_matrix = cosine_similarity(tfidf_matrix)

            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    similarity = float(sim_matrix[i, j])
                    student_a = items[i][2].id
                    student_b = items[j][2].id

                    # Create link if similarity is greater than 30%
                    if similarity > 0.30 and student_a != student_b:
                        current_weight = G.get_edge_data(student_a, student_b, default={}).get("weight", 0.0)
                        G.add_edge(
                            student_a,
                            student_b,
                            weight=max(current_weight, similarity),
                            reason=f"High Similarity in {subject} ({similarity:.1%})"
                        )
        except Exception as e:
            logger.error(f"Error computing pairwise text similarity for {subject}: {e}")

    # 2. Visual Hash Matching (Identical Images) across all items
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sub_i, rep_i, user_i = records[i]
            sub_j, rep_j, user_j = records[j]

            if user_i.id == user_j.id:
                continue

            if rep_i.visual_hash and rep_j.visual_hash and rep_i.visual_hash == rep_j.visual_hash:
                G.add_edge(
                    user_i.id,
                    user_j.id,
                    weight=1.0,
                    reason=f"Identical visual hash match in {sub_i.subject} vs {sub_j.subject}"
                )

    # Find connected components with size >= 2
    cheating_rings = []
    ring_id = 1

    for component in nx.connected_components(G):
        if len(component) < 2:
            continue

        members = []
        edges_details = []
        max_similarity = 0.0
        subjects_involved = set()

        for node in component:
            members.append(student_map[node])

        # Gather edge information inside the ring
        nodes_list = list(component)
        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                u, v = nodes_list[i], nodes_list[j]
                if G.has_edge(u, v):
                    edge_data = G.get_edge_data(u, v)
                    weight = edge_data.get("weight", 0.0)
                    reason = edge_data.get("reason", "Linked submissions")
                    max_similarity = max(max_similarity, weight)
                    
                    # Extract subject from reason
                    match = re.search(r"in ([\w\s,]+)(?:\s|$)", reason)
                    if match:
                        subjects_involved.add(match.group(1).strip())
                    else:
                        subjects_involved.add("Various")

                    edges_details.append({
                        "student_a": student_map[u]["name"],
                        "student_b": student_map[v]["name"],
                        "similarity": round(weight * 100, 1),
                        "reason": reason
                    })

        cheating_rings.append({
            "ring_id": f"RING-{ring_id:02d}",
            "size": len(component),
            "members": members,
            "links": edges_details,
            "max_similarity": round(max_similarity * 100, 1),
            "subjects": list(subjects_involved) if subjects_involved else ["Plagiarism Core"]
        })
        ring_id += 1

    # Sort rings by highest similarity first
    cheating_rings.sort(key=lambda r: r["max_similarity"], reverse=True)
    return cheating_rings


def get_stylometric_anomalies(db: Session) -> List[Dict[str, Any]]:
    """
    Analyzes historical writing style fingerprints per student.
    Flags submissions where the latest work severely deviates (Z-score > 2.0)
    from their personal historical standard deviation (style shifts / contract cheating).
    """
    records = (
        db.query(Submission, Report, User)
        .join(Report, Submission.id == Report.submission_id)
        .join(User, Submission.student_id == User.id)
        .order_by(Submission.created_at.asc())
        .all()
    )

    if not records:
        return []

    # Group reports by student
    student_history = defaultdict(list)
    for sub, rep, user in records:
        student_history[user.id].append((sub, rep, user))

    anomalies = []

    for student_id, history in student_history.items():
        if len(history) < 3:
            # Cold start: Skip students with less than 3 assignments (cannot calculate baseline variance)
            continue

        # Extract features for all submissions
        features_list = []
        for sub, rep, user in history:
            text = rep.processed_text or ""
            features = extract_stylometrics(text)
            features_list.append(features)

        # Baseline is computed on all but the LATEST submission
        baseline_features = features_list[:-1]
        latest_features = features_list[-1]
        latest_sub, latest_rep, user = history[-1]

        # Calculate mean and standard deviation for each feature
        metrics = ["word_length", "sentence_length", "ttr", "punctuation_density"]
        means = {}
        stds = {}

        for m in metrics:
            values = [feat[m] for feat in baseline_features]
            means[m] = np.mean(values)
            # prevent division by zero using a small epsilon
            stds[m] = np.std(values) if len(baseline_features) > 1 else 0.0

        # Compute Z-score deviations for the latest submission
        z_scores = {}
        max_deviation_metric = ""
        max_deviation_val = 0.0

        for m in metrics:
            val = latest_features[m]
            mean_val = means[m]
            std_val = stds[m]
            
            # Compute distance
            epsilon = 0.0001
            z = abs(val - mean_val) / (std_val + epsilon)
            z_scores[m] = z

            if z > max_deviation_val:
                max_deviation_val = z
                max_deviation_metric = m

        # Aggregate average deviation score
        avg_z_score = float(np.mean(list(z_scores.values())))

        # If average Z-score is > 2.0, flag as an anomaly
        if avg_z_score > 2.0:
            metric_display_names = {
                "word_length": "Average Word Length",
                "sentence_length": "Average Sentence Length",
                "ttr": "Vocabulary TTR Complexity",
                "punctuation_density": "Punctuation Density"
            }

            reason = (
                f"Significant shift in style detected ({avg_z_score:.2f}σ average deviation). "
                f"Most abnormal shift: {metric_display_names.get(max_deviation_metric)} was "
                f"{latest_features[max_deviation_metric]:.3f} vs historical average of "
                f"{means[max_deviation_metric]:.3f} ({max_deviation_val:.1f}σ deviation)."
            )

            anomalies.append({
                "student_name": user.name,
                "enrollment_no": user.enrollment_no or f"STU{user.id:04d}",
                "section": user.section or "N/A",
                "subject": latest_sub.subject,
                "filename": latest_sub.filename,
                "submission_id": latest_sub.id,
                "plagiarism_score": latest_rep.plagiarism_score,
                "ai_score": latest_rep.ai_score,
                "style_deviation": round(avg_z_score, 2),
                "reasoning": reason,
                "submitted_at": latest_sub.created_at
            })

    # Sort anomalies by highest deviation first
    anomalies.sort(key=lambda x: x["style_deviation"], reverse=True)
    return anomalies


def get_temporal_risk_factors(db: Session) -> List[Dict[str, Any]]:
    """
    Bins plagiarism and AI scores by the hour of the day.
    Identifies high-risk submission hours (like late-night crunch hours).
    """
    records = (
        db.query(Submission, Report)
        .join(Report, Submission.id == Report.submission_id)
        .all()
    )

    # Initialize bins
    hour_stats = {h: {"count": 0, "total_plag": 0.0, "total_ai": 0.0} for h in range(24)}

    for sub, rep in records:
        if sub.created_at:
            # Extract local submission hour (assumes DB stores local time or datetime object)
            hour = sub.created_at.hour
            hour_stats[hour]["count"] += 1
            hour_stats[hour]["total_plag"] += rep.plagiarism_score
            hour_stats[hour]["total_ai"] += rep.ai_score

    binned_risks = []
    for hour, stats in hour_stats.items():
        count = stats["count"]
        avg_plag = stats["total_plag"] / count if count > 0 else 0.0
        avg_ai = stats["total_ai"] / count if count > 0 else 0.0

        binned_risks.append({
            "hour": f"{hour:02d}:00",
            "hour_int": hour,
            "submissions_count": count,
            "avg_plagiarism": round(avg_plag, 1),
            "avg_ai": round(avg_ai, 1),
            "risk_level": "High" if (avg_plag > 25 or avg_ai > 40) and count > 0 else "Normal"
        })

    # Sort chronologically by hour of day
    binned_risks.sort(key=lambda x: x["hour_int"])
    return binned_risks


def get_institutional_insights(db: Session) -> Dict[str, Any]:
    """
    Computes macro level school analytics:
    - Subject Plagiarism/AI Risk Rankings
    - Total Hours Saved by Automated Evaluations
    - Key Risk Summary Statistics
    """
    records = (
        db.query(Submission, Report)
        .join(Report, Submission.id == Report.submission_id)
        .all()
    )

    total_submissions = len(records)
    
    # ROI Formula: 15 minutes (0.25 hrs) saved per assignment
    hours_saved = total_submissions * 0.25

    # Aggregate by subject
    subject_data = defaultdict(lambda: {"count": 0, "total_plag": 0.0, "total_ai": 0.0, "flagged": 0})
    
    for sub, rep in records:
        s_name = sub.subject
        subject_data[s_name]["count"] += 1
        subject_data[s_name]["total_plag"] += rep.plagiarism_score
        subject_data[s_name]["total_ai"] += rep.ai_score
        if rep.plagiarism_score > 30 or rep.ai_score > 50:
            subject_data[s_name]["flagged"] += 1

    subject_rankings = []
    for s_name, stats in subject_data.items():
        count = stats["count"]
        avg_plag = stats["total_plag"] / count
        avg_ai = stats["total_ai"] / count

        subject_rankings.append({
            "subject": s_name,
            "submissions_count": count,
            "avg_plagiarism": round(avg_plag, 1),
            "avg_ai": round(avg_ai, 1),
            "flagged_rate": round((stats["flagged"] / count) * 100, 1),
            "vulnerability_score": round((avg_plag * 0.6) + (avg_ai * 0.4), 1)
        })

    # Sort rankings by vulnerability score
    subject_rankings.sort(key=lambda x: x["vulnerability_score"], reverse=True)

    return {
        "total_evaluated": total_submissions,
        "hours_saved": round(hours_saved, 1),
        "subject_vulnerabilities": subject_rankings,
        "general_risk_notes": (
            "System performance optimized. Analytics compiled instantly."
            if total_submissions > 0 else "Insufficient data. Seed database to unlock analytics."
        )
    }
