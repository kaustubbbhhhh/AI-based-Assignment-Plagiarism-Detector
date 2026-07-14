# AI Detection System — Why It's Failing & The Fix

## 🔴 Root Cause Diagnosis

The two-layer AI detection system is **structurally sound in design** but has **3 critical scoring bugs** that cause it to systematically **under-detect** AI-generated content.

---

### Bug 1: Layer 1 — Perplexity Scoring is Inverted for Modern AI

**File:** `backend/services/ml_services/statistical_engine.py` — Line 82

```python
# CURRENT:
perp_score = max(0.0, min(100.0, (50.0 - mean_perplexity) * 2))
```

**Problem:** This formula assumes AI text has perplexity < 25 and human text has perplexity > 50. But **distilgpt2 is not GPT-4/Claude.** When distilgpt2 reads GPT-4 output, the perplexity is often **30–60** (not ultra-low), because distilgpt2 can't perfectly predict GPT-4's token choices. This means the formula gives GPT-4-written text a **low AI score** — the exact opposite of what we want.

**The key insight:** The perplexity thresholds (`50.0` baseline, `*2` multiplier) were hand-tuned with no calibration data. They're essentially guesses.

---

### Bug 2: Layer 2 — Semantic Engine Pattern Lists Are Too Weak

**File:** `backend/services/ml_services/semantic_engine.py` — Lines 12–29

```python
# CURRENT: Only 9 generic phrases, 17 transitions
GENERIC_PHRASES = [
    r"\bcan be defined as\b", r"\bplays a crucial role\b", ...  # just 9 entries
]
```

**Problem:** The keyword lists are **too small**. Modern AI text (especially from ChatGPT/Claude) doesn't always use phrases like "delving into" or "in today's fast-paced." It uses **subtler patterns** this regex engine completely misses:

| Missed Pattern | Why It Matters |
|----------------|---------------|
| Overly balanced sentence lengths | AI paragraphs have uniform ~15-20 word sentences |
| Excessive hedging | "It is worth noting that...", "One could argue..." |
| Perfect paragraph structure | Intro → Body → Conclusion in *every* paragraph |
| Lack of contractions | "do not" instead of "don't", "cannot" instead of "can't" |
| Absence of typos/slang | Real students make errors, AI doesn't |
| Formulaic conclusions | "In conclusion, it is clear that..." |

---

### Bug 3: Layer 1 — Burstiness Scale Divisor is Wrong

**File:** `backend/services/ml_services/statistical_engine.py` — Line 78

```python
# CURRENT:
uniformity_score = max(0.0, 1.0 - (burstiness / 5.0))
```

**Problem:** The divisor `5.0` is arbitrary. Real token-loss variance from distilgpt2 typically ranges from **2.0 to 15.0+**. Dividing by `5.0` means any text with variance > 5 gets a uniformity_score of `0.0` (classified as "human"), even if it's actually AI-generated text that just happens to have a few unusual tokens.

---

## 🟡 Current Architecture (What's Working vs What's Not)

```
┌─────────────────────────────────────────────────┐
│              FUSION ENGINE (ai_detection.py)     │
│                                                  │
│   ┌─────────────────┐  ┌──────────────────────┐ │
│   │  LAYER 1         │  │  LAYER 2              │ │
│   │  Statistical     │  │  Semantic             │ │
│   │  (distilgpt2)    │  │  (Regex Heuristics)   │ │
│   │                  │  │                       │ │
│   │  ✅ Perplexity   │  │  ✅ Generic phrases   │ │
│   │  ✅ Entropy      │  │  ✅ Personal voice    │ │
│   │  ✅ Burstiness   │  │  ✅ Transitions       │ │
│   │  ❌ Scoring math │  │  ❌ Too few patterns  │ │
│   │  ❌ Thresholds   │  │  ❌ No sentence-level │ │
│   └────────┬────────┘  └──────────┬───────────┘ │
│            │      60/40 Fusion     │             │
│            └──────────┬────────────┘             │
│                       ▼                          │
│              ❌ Hand-tuned weights                │
│              ❌ No calibration data               │
│              Final Score → Label                 │
└─────────────────────────────────────────────────┘
```

**What IS working:** The raw signal extraction (perplexity values, burstiness variance, entropy) from Layer 1 is accurate. The problem is in how those signals are **converted into a score.**

**What IS NOT working:** The formulas that map raw signals → 0-100 score are based on theoretical assumptions, not empirical measurement.

---

## 🟢 Fix Options

### Option A: Calibrated Thresholds (Quick Fix — ~1 hour)

Run a batch of known AI-generated and known human-written texts through the current engines, **log the raw scores**, and recalibrate the thresholds based on actual data.

- **Pros:** Fastest to implement
- **Cons:** Still relies on linear formulas; accuracy will plateau

### Option B: Fine-tuned Classifier (Recommended — ~3 hours)

Replace the hand-tuned formulas with a **lightweight scikit-learn classifier** trained on labeled examples.

**How it works:**
1. Collect ~50 AI-generated assignments + ~50 human-written assignments
2. Run each through both layers to extract raw features (perplexity, burstiness, entropy, generic_phrasing, lack_of_personal_voice, etc.)
3. Train a `LogisticRegression` or `RandomForestClassifier` on those features
4. Save the trained model as a `.joblib` file (~10 KB)
5. Replace the hand-tuned scoring with `model.predict_proba(features)`

- **Pros:** Best accuracy/complexity ratio; trains in <1 second; no GPU needed
- **Cons:** Requires labeled examples (one-time effort)

### Option C: Dedicated AI Detection Model (Best Accuracy — ~2 hours)

Use a purpose-built model like `roberta-base-openai-detector` from HuggingFace, which was specifically fine-tuned to distinguish human vs AI text.

- **Pros:** Best out-of-the-box accuracy
- **Cons:** ~500MB model download; slower inference; may not generalize perfectly to academic assignment style

---

## 📊 Comparison Table

| Aspect | Option A | Option B ⭐ | Option C |
|--------|----------|-----------|----------|
| Accuracy | ~65% | ~85% | ~90% |
| Training data needed | 20 samples | 100 samples | None |
| Implementation time | 1 hour | 3 hours | 2 hours |
| Model size | 0 KB | ~10 KB | ~500 MB |
| GPU required | No | No | Optional |
| Handles modern AI | Partially | Yes | Yes |

---

## 🚀 Recommended Implementation Plan (Option B)

### Phase 1: Dataset Creation
- Generate 50 AI-written assignments using ChatGPT / Claude / Gemini on our 5 subjects
- Collect 50 human-written assignments (or write synthetic human-like samples)
- Label each as `ai` or `human`

### Phase 2: Feature Extraction
- Run each sample through Layer 1 (statistical_engine) and Layer 2 (semantic_engine)
- Collect ~15 raw features per sample into a training matrix

### Phase 3: Model Training
```python
from sklearn.linear_model import LogisticRegression
import joblib

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
joblib.dump(model, "ai_classifier.joblib")
```

### Phase 4: Integration
- Load the trained model in `ai_detection.py`
- Replace hand-tuned formulas with `model.predict_proba()`
- Keep both layers as feature extractors (they're still valuable)

### Phase 5: Enhanced Layer 2
- Expand pattern lists from 9 → 50+ phrases
- Add sentence-level analysis (length variance, contraction detection)
- Add paragraph structure analysis

---

> **Bottom Line:** The current system is **not broken** — it's **uncalibrated**. The architecture (two-layer analysis with perplexity + semantic signals) is correct. The problem is that the scoring math was written with theoretical assumptions instead of empirical measurement. Option B (trained classifier) fixes this with minimal effort.
