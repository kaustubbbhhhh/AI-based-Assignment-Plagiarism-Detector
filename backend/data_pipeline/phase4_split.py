"""
Phase 4: Feature Scaling & Train-Test Split
=============================================
Normalizes features with StandardScaler and performs a group-stratified
split by question_id to prevent data leakage.

Steps:
  1. Load features.csv from Phase 3
  2. Separate X (18 features), y (label), groups (question_id)
  3. Group-stratified split (80/20) by question_id
  4. Fit StandardScaler on train, transform both train and test
  5. Save all artifacts

Input:  backend/data_pipeline/output/features.csv
Output: X_train.pkl, X_test.pkl, y_train.pkl, y_test.pkl, scaler.pkl, feature_names.json
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(PIPELINE_DIR, "output", "features.csv")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")

# Import feature names from extractors
import sys
sys.path.insert(0, PIPELINE_DIR)
from feature_extractors import FEATURE_NAMES


def run_phase4():
    print("=" * 60)
    print("PHASE 4: Feature Scaling & Train-Test Split")
    print("=" * 60)

    # --- Step 1: Load ---
    print(f"\n[Step 1] Loading feature matrix from: {INPUT_PATH}")
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: File not found: {INPUT_PATH}")
        print("  Run Phase 3 first.")
        return

    df = pd.read_csv(INPUT_PATH)
    print(f"  Loaded: {df.shape}")

    # --- Step 2: Separate X, y, groups ---
    print(f"\n[Step 2] Separating features, labels, and groups...")

    X = df[FEATURE_NAMES].values
    y = df["label"].values
    groups = df["question_id"].values

    print(f"  X shape: {X.shape} ({len(FEATURE_NAMES)} features)")
    print(f"  y shape: {y.shape}")
    print(f"  Unique question_ids: {len(np.unique(groups))}")
    print(f"  Class distribution: 0(Human)={np.sum(y==0)}, 1(AI)={np.sum(y==1)}")

    # --- Step 3: Group-stratified split ---
    print(f"\n[Step 3] Performing group-stratified split (80/20) by question_id...")

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    groups_train, groups_test = groups[train_idx], groups[test_idx]

    print(f"  Train: {X_train.shape[0]} samples")
    print(f"  Test:  {X_test.shape[0]} samples")

    # Verify no question_id overlap
    train_questions = set(groups_train)
    test_questions = set(groups_test)
    overlap = train_questions & test_questions

    if overlap:
        print(f"  WARNING: {len(overlap)} question_ids appear in both train and test!")
    else:
        print(f"  No question_id overlap between train and test. OK")

    # Class distribution in each split
    print(f"\n  Train class distribution:")
    train_human = np.sum(y_train == 0)
    train_ai = np.sum(y_train == 1)
    print(f"    0 (Human): {train_human} ({train_human/len(y_train)*100:.1f}%)")
    print(f"    1 (AI):    {train_ai} ({train_ai/len(y_train)*100:.1f}%)")

    print(f"\n  Test class distribution:")
    test_human = np.sum(y_test == 0)
    test_ai = np.sum(y_test == 1)
    print(f"    0 (Human): {test_human} ({test_human/len(y_test)*100:.1f}%)")
    print(f"    1 (AI):    {test_ai} ({test_ai/len(y_test)*100:.1f}%)")

    # --- Step 4: Feature scaling ---
    print(f"\n[Step 4] Fitting StandardScaler on train set...")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"  Train scaled stats (should be ~mean=0, std=1):")
    train_means = np.mean(X_train_scaled, axis=0)
    train_stds = np.std(X_train_scaled, axis=0)
    print(f"    Mean range: [{train_means.min():.4f}, {train_means.max():.4f}]")
    print(f"    Std range:  [{train_stds.min():.4f}, {train_stds.max():.4f}]")

    print(f"\n  Test scaled stats (should be close to mean=0, std=1):")
    test_means = np.mean(X_test_scaled, axis=0)
    test_stds = np.std(X_test_scaled, axis=0)
    print(f"    Mean range: [{test_means.min():.4f}, {test_means.max():.4f}]")
    print(f"    Std range:  [{test_stds.min():.4f}, {test_stds.max():.4f}]")

    # --- Step 5: Save artifacts ---
    print(f"\n[Step 5] Saving artifacts to: {OUTPUT_DIR}")

    artifacts = {
        "X_train.pkl": X_train_scaled,
        "X_test.pkl": X_test_scaled,
        "y_train.pkl": y_train,
        "y_test.pkl": y_test,
        "scaler.pkl": scaler,
    }

    for filename, data in artifacts.items():
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "wb") as f:
            pickle.dump(data, f)
        print(f"  Saved: {filename}")

    # Save feature names as JSON
    feature_names_path = os.path.join(OUTPUT_DIR, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)
    print(f"  Saved: feature_names.json")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"PHASE 4 COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Train set: {X_train_scaled.shape[0]} samples x {X_train_scaled.shape[1]} features")
    print(f"  Test set:  {X_test_scaled.shape[0]} samples x {X_test_scaled.shape[1]} features")
    print(f"  Scaler:    fitted on train, applied to both")
    print(f"  Groups:    no question_id leakage")
    print(f"\n  All artifacts saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_phase4()
