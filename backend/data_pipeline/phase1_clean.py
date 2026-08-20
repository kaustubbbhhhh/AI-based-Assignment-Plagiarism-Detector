"""
Phase 1: Data Loading & Cleaning
=================================
Loads essays.csv, selects relevant columns, and produces a clean text dataset.

Steps:
  1. Load raw data
  2. Select columns: answer, text_author, question_id, dataset
  3. Remove duplicate essays
  4. Strip HTML tags
  5. Normalize Unicode (NFKD)
  6. Remove extra whitespace / tabs / blank lines
  7. Remove prompt leakage phrases
  8. Log stats after each step

Input:  dataset/essays.csv
Output: backend/data_pipeline/output/cleaned_essays.csv
"""

import os
import re
import sys
import unicodedata
import pandas as pd
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_PATH = os.path.join(PROJECT_ROOT, "dataset", "essays.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "cleaned_essays.csv")

# ---------------------------------------------------------------------------
# HTML Stripper
# ---------------------------------------------------------------------------
class _HTMLStripper(HTMLParser):
    """Minimal HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.fed = []

    def handle_data(self, data):
        self.fed.append(data)

    def get_text(self):
        return "".join(self.fed)


def strip_html(text: str) -> str:
    """Remove all HTML tags from text."""
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


# ---------------------------------------------------------------------------
# Prompt Leakage Patterns
# ---------------------------------------------------------------------------
PROMPT_LEAKAGE_PATTERNS = [
    r"(?i)^as an ai( language model)?,?\s*",
    r"(?i)^i'?d be happy to help[.!]?\s*",
    r"(?i)^sure[,!]?\s*(here'?s?|i can|let me)\s*",
    r"(?i)^certainly[,!]?\s*(here'?s?|i can|let me)\s*",
    r"(?i)^of course[,!]?\s*(here'?s?|i can|let me)\s*",
    r"(?i)^absolutely[,!]?\s*(here'?s?|i can|let me)\s*",
    r"(?i)^great question[.!]?\s*",
    r"(?i)^that'?s a (great|good|interesting) question[.!]?\s*",
    r"(?i)^here is (a |an |my |the )?(essay|response|answer|text).*?:\s*",
    r"(?i)^(title|essay|response|answer)\s*:\s*",
]

COMPILED_LEAKAGE = [re.compile(p) for p in PROMPT_LEAKAGE_PATTERNS]


# ---------------------------------------------------------------------------
# Cleaning Functions
# ---------------------------------------------------------------------------
def normalize_unicode(text: str) -> str:
    """Normalize Unicode to NFKD form and remove non-printable characters."""
    text = unicodedata.normalize("NFKD", text)
    # Remove zero-width characters, control characters (keep newlines and tabs for now)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text


def clean_whitespace(text: str) -> str:
    """Remove extra spaces, tabs, and collapse blank lines."""
    # Replace tabs with single space
    text = text.replace("\t", " ")
    # Collapse multiple spaces into one
    text = re.sub(r" {2,}", " ", text)
    # Collapse 3+ newlines into 2 (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Strip overall
    return text.strip()


def remove_prompt_leakage(text: str) -> str:
    """Remove common AI prompt leakage from the beginning of text."""
    for pattern in COMPILED_LEAKAGE:
        text = pattern.sub("", text, count=1)
    return text.strip()


def clean_essay(text: str) -> str:
    """Apply all cleaning steps to a single essay."""
    text = strip_html(text)
    text = normalize_unicode(text)
    text = clean_whitespace(text)
    text = remove_prompt_leakage(text)
    return text


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------
def run_phase1():
    print("=" * 60)
    print("PHASE 1: Data Loading & Cleaning")
    print("=" * 60)

    # --- Step 1: Load ---
    print(f"\n[Step 1] Loading data from: {INPUT_PATH}")
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: File not found: {INPUT_PATH}")
        sys.exit(1)

    df = pd.read_csv(INPUT_PATH)
    print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")

    # --- Step 2: Select columns ---
    print(f"\n[Step 2] Selecting columns: answer, text_author, question_id, dataset")
    required_cols = ["answer", "text_author", "question_id", "dataset"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}")
        sys.exit(1)

    df = df[required_cols].copy()
    print(f"  Selected {len(df)} rows × {len(df.columns)} columns")

    # --- Step 3: Remove duplicates ---
    print(f"\n[Step 3] Removing duplicate essays...")
    before = len(df)
    df = df.drop_duplicates(subset=["answer"], keep="first")
    after = len(df)
    print(f"  Before: {before} -> After: {after} (removed {before - after} duplicates)")

    # --- Step 4: Strip HTML ---
    print(f"\n[Step 4] Stripping HTML tags...")
    # Check if any rows actually contain HTML
    html_pattern = re.compile(r"<[^>]+>")
    html_count = df["answer"].str.contains(html_pattern, na=False).sum()
    print(f"  Rows containing HTML tags: {html_count}")
    df["answer"] = df["answer"].apply(strip_html)
    print(f"  Done.")

    # --- Step 5: Normalize Unicode ---
    print(f"\n[Step 5] Normalizing Unicode (NFKD)...")
    df["answer"] = df["answer"].apply(normalize_unicode)
    print(f"  Done.")

    # --- Step 6: Clean whitespace ---
    print(f"\n[Step 6] Cleaning whitespace (extra spaces, tabs, blank lines)...")
    df["answer"] = df["answer"].apply(clean_whitespace)
    print(f"  Done.")

    # --- Step 7: Remove prompt leakage ---
    print(f"\n[Step 7] Removing prompt leakage phrases...")
    # Track how many essays had leakage removed
    original_lengths = df["answer"].str.len()
    df["answer"] = df["answer"].apply(remove_prompt_leakage)
    cleaned_lengths = df["answer"].str.len()
    leakage_count = (original_lengths != cleaned_lengths).sum()
    print(f"  Essays with prompt leakage removed: {leakage_count}")

    # --- Step 8: Remove essays that became too short after cleaning ---
    print(f"\n[Step 8] Removing essays with < 50 words after cleaning...")
    before = len(df)
    df["_word_count"] = df["answer"].str.split().str.len()
    df = df[df["_word_count"] >= 50].copy()
    df = df.drop(columns=["_word_count"])
    after = len(df)
    print(f"  Before: {before} -> After: {after} (removed {before - after} short essays)")

    # --- Final Stats ---
    print(f"\n{'=' * 60}")
    print(f"CLEANING COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Final row count: {len(df)}")
    print(f"  Null values in 'answer': {df['answer'].isnull().sum()}")

    word_counts = df["answer"].str.split().str.len()
    print(f"  Word count stats:")
    print(f"    Min:    {word_counts.min()}")
    print(f"    Max:    {word_counts.max()}")
    print(f"    Mean:   {word_counts.mean():.1f}")
    print(f"    Median: {word_counts.median():.1f}")

    print(f"\n  text_author distribution:")
    for author, count in df["text_author"].value_counts().items():
        pct = count / len(df) * 100
        print(f"    {author}: {count} ({pct:.1f}%)")

    print(f"\n  dataset distribution:")
    for ds, count in df["dataset"].value_counts().items():
        pct = count / len(df) * 100
        print(f"    {ds}: {count} ({pct:.1f}%)")

    # --- Spot Check ---
    print(f"\n{'=' * 60}")
    print(f"SPOT CHECK: 5 random cleaned essays (first 120 chars)")
    print(f"{'=' * 60}")
    samples = df.sample(n=5, random_state=42)
    for idx, row in samples.iterrows():
        preview = row["answer"][:120].replace("\n", " ")
        print(f"  [{row['text_author']:>45}] {preview}...")

    # --- Save ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[OK] Saved cleaned data to: {OUTPUT_PATH}")
    print(f"  Shape: {df.shape}")


if __name__ == "__main__":
    run_phase1()
