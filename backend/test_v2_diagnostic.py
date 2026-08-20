"""Diagnostic test: check feature values + test with actual dataset essays."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pandas as pd
from services.ai_detection import analyze_ai_content

# Load actual essays from the dataset for realistic testing
df = pd.read_csv(r"D:\AI based Assignment Plagiarism Detector\backend\data_pipeline\output\labeled_essays.csv")

# Pick a few real human and AI essays
humans = df[df["label"] == 0].sample(3, random_state=99)
ais = df[df["label"] == 1].sample(3, random_state=99)

print("=" * 60)
print("INTEGRATION TEST: Real Dataset Essays")
print("=" * 60)

# Test human essays
print("\n--- Human Essays ---")
human_scores = []
for idx, row in humans.iterrows():
    result = analyze_ai_content(row["answer"])
    score = result["ai_score"]
    human_scores.append(score)
    preview = row["answer"][:80].replace("\n", " ")
    print(f"  Score: {score:5.1f}% | Label: {result['label']:14s} | {preview}...")

# Test AI essays
print("\n--- AI Essays ---")
ai_scores = []
for idx, row in ais.iterrows():
    result = analyze_ai_content(row["answer"])
    score = result["ai_score"]
    ai_scores.append(score)
    preview = row["answer"][:80].replace("\n", " ")
    print(f"  Score: {score:5.1f}% | Label: {result['label']:14s} | {preview}...")

print(f"\n--- Summary ---")
print(f"  Human avg score: {sum(human_scores)/len(human_scores):.1f}%")
print(f"  AI avg score:    {sum(ai_scores)/len(ai_scores):.1f}%")

all_human_pass = all(s < 50 for s in human_scores)
all_ai_pass = all(s > 50 for s in ai_scores)
print(f"  All humans < 50%: {'PASS' if all_human_pass else 'FAIL'} {human_scores}")
print(f"  All AIs > 50%:    {'PASS' if all_ai_pass else 'FAIL'} {ai_scores}")

# Also show v2 feature details for first human essay
print(f"\n--- Feature Details (first human essay) ---")
result = analyze_ai_content(humans.iloc[0]["answer"])
if "v2_details" in result and result["v2_details"]:
    fv = result["v2_details"]["feature_vector"]
    for name, val in fv.items():
        print(f"  {name:30s} = {val}")
