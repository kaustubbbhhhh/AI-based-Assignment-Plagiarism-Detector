"""
Phase 2: Label Encoding & Balancing
=====================================
Converts text_author to binary labels and handles the 13.9:1 class imbalance.

Steps:
  1. Load cleaned data from Phase 1
  2. Map: human -> 0, all AI sources -> 1
  3. Print class distribution
  4. Random undersample AI class to ~2:1 ratio
  5. Shuffle dataset
  6. Save labeled + balanced dataset

Input:  backend/data_pipeline/output/cleaned_essays.csv
Output: backend/data_pipeline/output/labeled_essays.csv
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(PIPELINE_DIR, "output", "cleaned_essays.csv")
OUTPUT_PATH = os.path.join(PIPELINE_DIR, "output", "labeled_essays.csv")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# Target ratio of AI:Human after undersampling
TARGET_RATIO = 2  # 2:1 (AI:Human)
RANDOM_STATE = 42


def run_phase2():
    print("=" * 60)
    print("PHASE 2: Label Encoding & Balancing")
    print("=" * 60)

    # --- Step 1: Load cleaned data ---
    print(f"\n[Step 1] Loading cleaned data from: {INPUT_PATH}")
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: File not found: {INPUT_PATH}")
        print("  Run Phase 1 first.")
        return

    df = pd.read_csv(INPUT_PATH)
    print(f"  Loaded: {len(df)} rows")

    # --- Step 2: Map labels ---
    print(f"\n[Step 2] Encoding labels: human -> 0, all AI sources -> 1")
    print(f"  Original text_author values:")
    for author, count in df["text_author"].value_counts().items():
        print(f"    {author}: {count}")

    df["label"] = df["text_author"].apply(lambda x: 0 if x == "human" else 1)

    print(f"\n  After encoding:")
    label_counts = df["label"].value_counts().sort_index()
    for label, count in label_counts.items():
        name = "Human" if label == 0 else "AI"
        pct = count / len(df) * 100
        print(f"    {label} ({name}): {count} ({pct:.1f}%)")

    human_count = label_counts.get(0, 0)
    ai_count = label_counts.get(1, 0)
    current_ratio = ai_count / human_count if human_count > 0 else float("inf")
    print(f"\n  Current ratio (AI:Human): {current_ratio:.1f}:1")

    # --- Step 3: Balance via undersampling ---
    print(f"\n[Step 3] Balancing dataset (target ratio: {TARGET_RATIO}:1)")

    if current_ratio <= TARGET_RATIO:
        print(f"  Ratio is already <= {TARGET_RATIO}:1. No undersampling needed.")
        df_balanced = df.copy()
    else:
        target_ai_count = human_count * TARGET_RATIO

        df_human = df[df["label"] == 0]
        df_ai = df[df["label"] == 1]

        # Stratified undersample: sample proportionally from each AI source
        # so we keep diversity across gpt-4o-mini, llama, dipper
        print(f"  Undersampling AI class: {ai_count} -> {target_ai_count}")
        print(f"  Sampling proportionally from each AI source:")

        ai_sources = df_ai["text_author"].value_counts()
        sampled_parts = []

        for source, source_count in ai_sources.items():
            # Proportion of this source within all AI samples
            proportion = source_count / ai_count
            n_sample = max(1, int(round(target_ai_count * proportion)))
            # Don't sample more than available
            n_sample = min(n_sample, source_count)

            sampled = df_ai[df_ai["text_author"] == source].sample(
                n=n_sample, random_state=RANDOM_STATE
            )
            sampled_parts.append(sampled)
            print(f"    {source}: {source_count} -> {n_sample} ({proportion*100:.1f}%)")

        df_ai_sampled = pd.concat(sampled_parts)

        # Adjust if total doesn't exactly match target due to rounding
        actual_total = len(df_ai_sampled)
        if actual_total > target_ai_count:
            df_ai_sampled = df_ai_sampled.sample(
                n=target_ai_count, random_state=RANDOM_STATE
            )
        
        df_balanced = pd.concat([df_human, df_ai_sampled])

    # --- Step 4: Shuffle ---
    print(f"\n[Step 4] Shuffling dataset...")
    df_balanced = df_balanced.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    print(f"  Done.")

    # --- Final Stats ---
    print(f"\n{'=' * 60}")
    print(f"BALANCING COMPLETE")
    print(f"{'=' * 60}")

    final_counts = df_balanced["label"].value_counts().sort_index()
    for label, count in final_counts.items():
        name = "Human" if label == 0 else "AI"
        pct = count / len(df_balanced) * 100
        print(f"  {label} ({name}): {count} ({pct:.1f}%)")

    final_human = final_counts.get(0, 0)
    final_ai = final_counts.get(1, 0)
    final_ratio = final_ai / final_human if final_human > 0 else 0
    print(f"\n  Final ratio (AI:Human): {final_ratio:.1f}:1")
    print(f"  Total samples: {len(df_balanced)}")

    # Verify AI source diversity is preserved
    print(f"\n  AI source diversity in balanced set:")
    ai_only = df_balanced[df_balanced["label"] == 1]
    for source, count in ai_only["text_author"].value_counts().items():
        pct = count / len(ai_only) * 100
        print(f"    {source}: {count} ({pct:.1f}%)")

    # Verify all human samples preserved
    print(f"\n  All {final_human} human samples preserved: ", end="")
    print("YES" if final_human == human_count else f"NO (expected {human_count})")

    # Verify labels are only 0 and 1
    unique_labels = sorted(df_balanced["label"].unique())
    print(f"  Labels are only [0, 1]: {'YES' if unique_labels == [0, 1] else 'NO'}")

    # --- Save ---
    df_balanced.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[OK] Saved labeled data to: {OUTPUT_PATH}")
    print(f"  Shape: {df_balanced.shape}")
    print(f"  Columns: {list(df_balanced.columns)}")


if __name__ == "__main__":
    run_phase2()
