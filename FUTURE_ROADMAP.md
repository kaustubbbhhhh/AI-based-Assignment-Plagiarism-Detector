# AI Plagiarism Detector: Future Implementations Roadmap

This document outlines the five major system upgrades necessary to transition the current prototype into a production-ready, highly robust academic evaluation system.

## 1. Semantic Subject / Context Matching
**The Problem:** Currently, a student can upload a completely irrelevant assignment (like Physics) into a computer science subject category, and the system would give it a 0% plagiarism score because it is comparing it to the wrong corpus.

**The Implementation:** 
* Add a feature where teachers input keywords or a topic description when they create an assignment.
* Before checking for plagiarism, run a **Semantic Similarity Check** to compare the uploaded text against the teacher's expected topic constraints.
* If the text diverges entirely from the expected topic, the system automatically rejects it as "Off-Topic" or "Irrelevant".

## 2. Two-Layer AI Detection Architecture
**The Problem:** Current AI detection relies on basic statistical mathematical heuristics. Adaptive students can bypass this by manually varying sentence structures or using light paraphrasing. A multi-layered approach is required to verify authenticity with higher confidence.

**The Implementation:**

### Layer 1: Statistical Analysis Engine (Neural-Heuristic Analysis)
*   **Goal:** Evaluate text using **only mathematical and probabilistic signals** derived from a local language model.
*   **Implementation Context:**
    *   **Stack:** Use `torch` (PyTorch) for tensor computation and `transformers` (Hugging Face) for model loading.
    *   **Model:** Causal language model (e.g., `distilgpt2`) providing **token-level log probabilities**.
    *   **Environment:** Must run in `eval()` mode and `torch.no_grad()` context for deterministic and efficient inference.
*   **Core Computation Requirements:**
    *   **Tokenization & Log-Probabilities:** Tokenize input and pass through the model to extract loss (negative log-likelihood) and token-level log probabilities.
    *   **Sliding Window Analysis:** Split tokens into chunks (50–100 tokens) to extract `mean_perplexity`, `perplexity_variance`, and `max_perplexity_spike`.
    *   **Burstiness:** Compute the variance of token log-probabilities to detect stylistic shifts.
    *   **Entropy Estimation:** Estimate the entropy of the token probability distribution.
    *   **Uniformity Detection:** Calculate a score based on low perplexity, low burstiness, and consistent chunk scores.
    *   **Calibration:** Compare against human baseline statistics (`z_score_human`).
*   **Output Format (Strict JSON):**
    ```json
    {
      "normalized_perplexity": float,
      "mean_perplexity": float,
      "perplexity_variance": float,
      "max_perplexity_spike": float,
      "burstiness": float,
      "entropy": float,
      "uniformity_score": float,
      "z_score_human": float,
      "statistical_ai_likelihood": float,
      "confidence": float,
      "pattern_type": "uniform | mixed | irregular",
      "risk_level": "low | moderate | high",
      "reasoning": "1–2 lines based ONLY on statistical patterns"
    }
    ```

### Layer 2: Semantic Analysis Engine (Context & Style Analysis)
*   **Goal:** Evaluate the **meaning, style, and human-likeness** of the text to provide "semantic intelligence" that complements Layer 1's statistical signals. Focus on writing behavior, not correctness.
*   **Core Semantic Metrics (Score 0-1):**
    *   **Generic Phrasing:** Template-like, textbook-style, or reusable language.
    *   **Lack of Personal Voice:** Absence of individuality, personal examples, or human tone.
    *   **Over-Structured Coherence:** Unnaturally perfect flow or mechanical transitions.
    *   **Repetitiveness:** Repeated semantic or structural patterns.
    *   **Semantic Predictability:** Safe, expected phrasing with low originality.
    *   **Conceptual Shallowness:** Correct but lacks depth, nuance, or insight.
*   **Output Format (Strict JSON):**
    ```json
    {
      "generic_phrasing": float,
      "lack_of_personal_voice": float,
      "over_structured_coherence": float,
      "repetitiveness": float,
      "semantic_predictability": float,
      "conceptual_shallowness": float,
      "final_ai_likelihood": float,
      "confidence": float,
      "signal_alignment": "low | medium | high",
      "risk_level": "low | moderate | high",
      "reasoning": "2–4 lines (semantic reasoning only)"
    }
    ```
*   **Operational Constraints:**
    *   **Layer Separation:** DO NOT use statistical reasoning (no perplexity, entropy, etc.) or assume access to token probabilities.
    *   **Signal Alignment:** Increase AI likelihood **only when multiple signals are high**. If signals conflict, reduce confidence and keep scores in the 0.4–0.6 range.
    *   **Human Imperfection Bias:** Reduce AI likelihood if the text shows personal examples, uneven flow, minor inconsistencies, or natural human variation.
    *   **Conservative Scoring:** Avoid extreme values unless evidence is strong; prefer moderate scores when uncertain.
    *   **Grammar Trap Avoidance:** DO NOT assume grammatically correct text is AI-generated.
*   **Scoring Logic:**
    *   **final_ai_likelihood:** Weighted combination of all metrics; increase only when multiple indicators align.
    *   **confidence:** HIGH → signals strongly agree; LOW → conflicting indicators.
    *   **signal_alignment:** high → strong agreement; medium → partial agreement; low → inconsistent.
    *   **risk_level:** low (human-like), moderate (uncertain), or high (strong AI-like traits).

### Fusion Layer: Final Decision Engine
*   **Goal:** Combine objective statistical evidence (Layer 1) with semantic interpretation (Layer 2) to produce a balanced, reliable final decision.
*   **Fusion Rules:**
    *   **Weighted Decision:** Layer 1 (statistical signals) is given slightly more importance, while Layer 2 serves as contextual validation.
    *   **Disagreement Handling:** If the two layers strongly disagree, the engine MUST return "Uncertain" rather than forcing a decision.
    *   **Agreement Boost:** Strong agreement between both layers increases final confidence and produces definitive "AI Likely" or "Human Likely" labels.
    *   **Pattern Awareness:** Automatically flags strong AI intent if `pattern_type` is "uniform" AND `signal_alignment` is "high".
    *   **Conservative Bias:** Prioritize avoiding false positives. If the evidence is mixed or weak, the system defaults to "Uncertain".
*   **Output Format (Strict JSON):**
    ```json
    {
      "final_score": float,
      "final_label": "AI Likely | Human Likely | Uncertain",
      "confidence": float,
      "decision_basis": "agreement | disagreement | statistical_dominant | semantic_dominant",
      "reasoning": "2–3 lines explaining fusion logic"
    }
    ```
*   **Core Constraints:**
    *   DO NOT rely on a single layer for the final verdict.
    *   DO NOT ignore layer disagreements; treat them as indicators of high uncertainty.
    *   DO NOT provide extreme outputs without strong multi-layer agreement.


## 3. Intelligent OCR & Image Pre-processing (Tesseract + OpenCV)
**The Problem:** The current system is "blind" to images. Scanned handwritten documents or photo-based PDFs bypass the system because standard extraction returns 0 words. Cheaters can also exploit blur or low lighting to hide plagiarized text from basic OCR.

**Implementation Phases:**

### Phase 1: The "Digital Vision" Foundation (OpenCV)
*   **Goal:** Clean images before they reach the OCR engine to maximize accuracy.
*   **Steps:**
    *   Integrate `opencv-python` to handle image normalization.
    *   Implement **Adaptive Thresholding** to remove shadows and convert greyish paper photos into high-contrast black-and-white.
    *   Implement **Denoising & Bilateral Filtering** to sharpen blurry edges and remove digital artifacts from low-light photos.
    *   Implement **Deskewing** to automatically straighten tilted or rotated page photos.

### Phase 2: Hybrid Extraction Pipeline (Tesseract)
*   **Goal:** Create a seamless fallback mechanism for non-digital documents.
*   **Steps:**
    *   Integrate `pytesseract` and Google’s Tesseract OCR engine.
    *   Update `text_extraction.py`: If digital extraction (`PyPDF2`) returns < 20 words, automatically trigger the OpenCV -> Tesseract pipeline.
    *   Convert multi-page PDFs into image arrays for individual page scanning.

### Phase 3: Quality Control & Confidence Scoring
*   **Goal:** Prevent "Garbage In, Garbage Out" scenarios.
*   **Steps:**
    *   Extract Tesseract’s **Confidence Scores** for every word.
    *   Implement a "Rejection Gate": If average confidence is < 65% (meaning the photo is too blurry or dark), the system automatically rejects the submission and asks the student for a clearer photo.

### Phase 4: Perceptual Hashing (Visual Plagiarism)
*   **Goal:** Detect visual copies even without reading the text.
*   **Steps:**
    *   Generate a **Visual Hash** of every uploaded image using OpenCV.
    *   Compare hashes to detect if two students uploaded the exact same photo, even if the filename or student name was changed.

## 4. Teacher Subject Management & Dashboard Integration
**The Problem:** Currently, the system lacks granular filtering by subject on the teacher's dashboard, making it difficult for teachers who handle multiple subjects to organize and view student submissions efficiently.

**The Implementation:**
* **Dashboard Enhancement:** Add a "Subject" dropdown selection box adjacent to the existing "Section" dropdown on the Teacher's Dashboard. This will allow for multi-layered filtering of assignments.
* **Teacher Settings:** Implement a dedicated Subject Management section within the Teacher Settings. This interface will allow teachers to:
    * Add new subjects to their teaching profile.
    * Remove subjects no longer being taught.
    * Edit existing subject labels.
* **Backend Update:** Update the database schema and API endpoints to associate assignments with specific subjects and link those subjects to individual teacher profiles.

## 5. Advanced Data Mining & Forensic Analytics
**The Problem:** Simple detection is reactive. To prevent plagiarism systematically, the system needs to identify patterns, cheating rings, and "contract cheating" (where students pay others to write for them).

**The Implementation:**
* See the dedicated [DATA_MINING_ROADMAP.md](./DATA_MINING_ROADMAP.md) for a detailed 5-phase breakdown of implementation strategies, including Social Network Mining and Stylometric Profiling.
