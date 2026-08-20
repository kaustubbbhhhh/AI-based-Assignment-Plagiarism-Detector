"""
Phase 3: Feature Extraction
=============================
Transforms raw essay text into a numerical feature matrix (18 features per essay).

Uses feature_extractors.py for all extraction logic.
Processes essays with a progress bar and saves to CSV.

Input:  backend/data_pipeline/output/labeled_essays.csv
Output: backend/data_pipeline/output/features.csv
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from tqdm import tqdm

# Ensure this directory is importable
sys.path.insert(0, os.path.dirname(__file__))
from feature_extractors import (
    extract_all_features,
    FEATURE_NAMES,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(PIPELINE_DIR, "output", "labeled_essays.csv")
OUTPUT_PATH = os.path.join(PIPELINE_DIR, "output", "features.csv")


def run_phase3():
    print("=" * 60)
    print("PHASE 3: Feature Extraction")
    print("=" * 60)

    # --- Step 1: Load labeled data ---
    print(f"\n[Step 1] Loading labeled data from: {INPUT_PATH}")
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: File not found: {INPUT_PATH}")
        print("  Run Phase 2 first.")
        return

    df = pd.read_csv(INPUT_PATH)
    print(f"  Loaded: {len(df)} rows")

    # --- Step 2: Load spaCy model ---
    print(f"\n[Step 2] Loading spaCy model (en_core_web_sm)...")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        print(f"  Loaded successfully.")
    except Exception as e:
        print(f"  WARNING: Could not load spaCy model: {e}")
        print(f"  POS/NER features will be set to 0.")
        nlp = None

    # --- Step 3: Load DistilGPT-2 (lazy, happens on first call) ---
    print(f"\n[Step 3] DistilGPT-2 will be loaded on first extraction...")

    # --- Step 4: Extract features ---
    print(f"\n[Step 4] Extracting 18 features from {len(df)} essays...")
    print(f"  Features: {FEATURE_NAMES}")
    print()

    start_time = time.time()
    all_features = []
    errors = 0

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="  Extracting"):
        try:
            features = extract_all_features(row["answer"], nlp=nlp)
            all_features.append(features)
        except Exception as e:
            # Append NaN row so indices stay aligned
            all_features.append({name: np.nan for name in FEATURE_NAMES})
            errors += 1
            if errors <= 5:
                tqdm.write(f"  ERROR at row {idx}: {e}")

    elapsed = time.time() - start_time
    print(f"\n  Extraction complete in {elapsed:.1f}s ({elapsed/len(df):.2f}s per essay)")
    if errors > 0:
        print(f"  Errors: {errors}")

    # --- Step 5: Build feature DataFrame ---
    print(f"\n[Step 5] Building feature matrix...")
    features_df = pd.DataFrame(all_features)

    # Ensure column order matches FEATURE_NAMES
    features_df = features_df[FEATURE_NAMES]

    # Attach metadata columns (not training features, but needed for Phase 4 split)
    features_df["label"] = df["label"].values
    features_df["question_id"] = df["question_id"].values
    features_df["text_author"] = df["text_author"].values

    print(f"  Shape: {features_df.shape}")
    print(f"  Feature columns: {FEATURE_NAMES}")

    # --- Step 6: Quality checks ---
    print(f"\n[Step 6] Quality checks...")

    # Check for NaN/Inf
    nan_counts = features_df[FEATURE_NAMES].isna().sum()
    inf_counts = np.isinf(features_df[FEATURE_NAMES].select_dtypes(include=[np.number])).sum()

    has_nans = nan_counts.sum() > 0
    has_infs = inf_counts.sum() > 0

    if has_nans:
        print(f"  WARNING: NaN values found:")
        for col, count in nan_counts.items():
            if count > 0:
                print(f"    {col}: {count} NaNs")
        # Fill NaNs with column median
        print(f"  Filling NaNs with column medians...")
        features_df[FEATURE_NAMES] = features_df[FEATURE_NAMES].fillna(
            features_df[FEATURE_NAMES].median()
        )
    else:
        print(f"  No NaN values found. OK")

    if has_infs:
        print(f"  WARNING: Inf values found. Replacing with column max...")
        for col in FEATURE_NAMES:
            mask = np.isinf(features_df[col])
            if mask.any():
                max_val = features_df.loc[~mask, col].max()
                features_df.loc[mask, col] = max_val
    else:
        print(f"  No Inf values found. OK")

    # --- Step 7: Descriptive stats ---
    print(f"\n[Step 7] Feature statistics:")
    print(f"\n{features_df[FEATURE_NAMES].describe().round(4).to_string()}")

    # --- Step 8: Compare human vs AI features ---
    print(f"\n[Step 8] Mean features by class (Human=0, AI=1):")
    grouped = features_df.groupby("label")[FEATURE_NAMES].mean()
    print(f"\n{grouped.round(4).to_string()}")

    # Show which features differ most
    print(f"\n  Top 5 features with largest mean difference (|AI - Human|):")
    diff = (grouped.loc[1] - grouped.loc[0]).abs().sort_values(ascending=False)
    for feat, val in diff.head(5).items():
        h_val = grouped.loc[0, feat]
        a_val = grouped.loc[1, feat]
        print(f"    {feat}: Human={h_val:.4f}, AI={a_val:.4f}, diff={val:.4f}")

    # --- Save ---
    features_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[OK] Saved feature matrix to: {OUTPUT_PATH}")
    print(f"  Shape: {features_df.shape}")
    print(f"  Columns: {list(features_df.columns)}")


if __name__ == "__main__":
    run_phase3()
