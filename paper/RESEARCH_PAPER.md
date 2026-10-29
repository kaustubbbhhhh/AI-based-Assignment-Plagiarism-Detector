# Robust Multi-Modal Academic Integrity: An Integrated Vision-Language and Stylometric Framework for Handwritten and Digital Assignment Plagiarism Detection

**Abstract**—The proliferation of large language models (LLMs) such as GPT-4o, Claude 3.5, and Llama 3 has precipitated an unprecedented integrity crisis across secondary and tertiary educational institutions. Existing academic integrity frameworks suffer from three systemic deficiencies: (1) an inability to ingest non-digital modalities (e.g., student handwritten assignments, scanned examinations, crumpled sheets, and smartphone photographs); (2) high false-positive rates on authentic human writing—particularly penalizing non-native English learners; and (3) severe data-privacy and FERPA/GDPR violations stemming from cloud-based text transmission to proprietary third-party detectors. In this paper, we propose an enterprise-grade, multi-modal, privacy-preserving academic integrity framework that couples an 8-layer layout-aware Optical Character Recognition (OCR) vision pipeline with an adversarial defense-in-depth detection architecture. The vision engine utilizes CRAFT line detection, Microsoft TrOCR for unconstrained cursive handwriting, and GOT-OCR 2.0 for mathematical notations and tabular formatting, reconciled through Levenshtein consensus arbitration and topological reading-order sorting. Extracted text is evaluated via a multi-layer attribution engine comprising: (a) a semantic curriculum alignment gate; (b) a local neural language model (Qwen 2.5 0.5B) computing token-level perplexity, loss variance, Shannon entropy, and sentence burstiness coefficient of variation; (c) an 18-dimensional stylometric, syntactic, and structural feature extractor; and (d) a calibrated ensemble Random Forest classifier. Concurrently, a dual-tier peer plagiarism subsystem detects image-level resubmissions via 64-bit difference perceptual hashing ($\text{dHash}$) and textual collusion via cohort-isolated unigram/bigram TF-IDF cosine similarity. Rigorous empirical evaluation across a benchmark dataset of 2,739 authentic student and LLM-generated submissions demonstrates that our model achieves **97.43% classification accuracy**, **99.22% precision**, **96.96% recall**, **98.08% F1-score**, and an **ROC-AUC of 0.9924**. Crucially, the system reduces the false-positive rate on authentic human writing to **1.59%** (3 false positives out of 189 test instances), while executing completely on-premise without cloud data exfiltration.

**Keywords**—Academic Integrity, AI-Generated Text Detection, Perplexity, Stylometry, Optical Character Recognition, TrOCR, GOT-OCR 2.0, Peer Plagiarism, Perceptual Hashing, Machine Learning.

---

## 1. Introduction

The rapid democratization of generative Artificial Intelligence (GenAI) and Large Language Models (LLMs)—epitomized by OpenAI's GPT-4o, Anthropic's Claude 3.5 Sonnet, and Meta's Llama 3—has revolutionized automated text synthesis. While these models unlock transformative potential in creative writing and programming assistance, they pose an existential threat to traditional pedagogical assessment paradigms \cite{brown2020language, foltynek2019academic}. Educational institutions rely heavily on independent written assignments, laboratory reports, and take-home examinations to assess critical thinking, synthesis, and subject mastery. However, students can now effortlessly generate articulate, structurally coherent, and superficially convincing submissions in seconds, bypassing the cognitive learning process \cite{crothers2023machine}.

Traditional academic plagiarism detection engines (e.g., Turnitin, CopyLeaks, Unicheck) were engineered around exact and near-exact verbatim string-matching, $n$-gram fingerprinting (e.g., winnowing), and document-level information retrieval \cite{meuschke2013analyzing, salton1988term}. When applied to AI-generated essays, these traditional engines fail completely: LLMs synthesize novel token combinations rather than copying verbatim text from a central repository, producing near-zero similarity against global web indices.

To counter this, a first generation of commercial "AI detectors" emerged, largely relying on zero-shot perplexity heuristics or monolithic deep classification heads \cite{mitchell2023detectgpt}. Nevertheless, real-world deployment of these commercial tools in higher education has exposed three critical vulnerabilities:

1. **Modal Isolation (Text-Only Limitation):** Institutional coursework is fundamentally multi-modal. In STEM, humanities, and in-class examinations, students frequently submit handwritten problem sets, physical exam booklets, or photographs of documents taken with mobile devices. Current detectors cannot parse physical documents directly, forcing instructors to manually transcribe text or rely on naive OCR utilities that garble multi-column text, drop mathematical formulas, and corrupt cursive handwriting.
2. **The False-Positive Disaster & Disparate Impact:** Wrongful accusations of academic dishonesty carry catastrophic academic, psychological, and disciplinary consequences. Empirical studies have proven that monolithic commercial detectors exhibit alarming false-positive rates (FPR), particularly discriminating against non-native English writers who utilize standardized sentence templates and limited vocabulary \cite{liang2023gpt}. High false-positive rates erode student-faculty trust and render automated scores legally indefensible in academic appeals.
3. **Regulatory and Privacy Violations (FERPA / GDPR):** Commercial detectors operate as proprietary cloud software-as-a-service (SaaS). Transmitting student submissions to external corporate servers violates strict student privacy regulations, including the United States Family Educational Rights and Privacy Act (FERPA) and the European Union General Data Protection Regulation (GDPR). Educational institutions have an urgent legal and ethical imperative to retain full custody of student intellectual work.

### 1.1 Contributions of this Work

To overcome these fundamental limitations, this paper presents the design, mathematical formulation, empirical validation, and production deployment of the **AI-Based Assignment Plagiarism Detector**. The key scientific and engineering contributions of this paper are:

- **End-to-End Multi-Modal Architecture:** We formulate an end-to-end framework capable of ingesting raw digital text (`.pdf`, `.docx`, `.txt`) as well as multi-page smartphone camera captures and degraded scans of handwritten and printed student assignments.
- **8-Layer Layout-Aware OCR Vision Pipeline:** We propose a modular computer vision pipeline integrating morphological contrast enhancement, Hough deskewing, Sauvola binarization, notebook line inpainting, CRAFT line-level text detection, dynamic region routing, Microsoft TrOCR for cursive handwriting, and GOT-OCR 2.0 for LaTeX equations and markdown tables. A Levenshtein consensus arbiter and topological column sorter reconstruct accurate reading order without column interleaving.
- **Defense-in-Depth AI Attribution Engine:** We construct a hybrid detection engine combining a local neural language model (Qwen 2.5 0.5B) for token-level log-loss, perplexity, and sentence burstiness coefficient of variation ($CV$) with an 18-dimensional stylometric, syntactic, and readability feature space. An ensemble Random Forest classifier delivers calibrated probabilities with conservative, three-tier academic decision thresholds.
- **Dual-Tier Peer Collusion Engine:** We implement a localized peer-to-peer plagiarism engine that cross-references submissions within the same course cohort. It combines 64-bit difference perceptual hashing ($\text{dHash}$) to catch visual image resubmissions with $L_2$-normalized unigram/bigram TF-IDF cosine similarity, optimized via in-memory MD5 matrix caching.
- **Empirical Rigor & Open Governance:** Evaluated on a balanced corpus of 2,739 student and LLM essays, the model delivers **97.43% accuracy**, **99.22% precision**, **98.08% F1-score**, and **0.9924 ROC-AUC**, while suppressing false positives on human text to **1.59%**. The entire platform operates fully on-premise on standard workstation hardware via an asynchronous Celery/Redis microservices architecture.

---

## 2. Related Work

### 2.1 Traditional Textual Plagiarism Detection
Automated plagiarism detection has evolved over three decades. Early systems relied on string matching algorithms such as the Knuth-Morris-Pratt and Boyer-Moore algorithms, progressing toward fuzzy string matching using Levenshtein edit distance. Salton and Buckley established the vector space model (VSM) using Term Frequency-Inverse Document Frequency (TF-IDF) \cite{salton1988term}. Later, Schleimer et al. introduced the *winnowing* algorithm, a local fingerprinting technique that extracts minimum hash values within a sliding window to detect verbatim substring matching robustly against minor perturbations. While effective for detecting peer-to-peer copying and online source scraping \cite{meuschke2013analyzing}, these methods are blind to machine-generated paraphrasing and prompt-engineered synthesis.

### 2.2 Machine-Generated Text Detection
Approaches for identifying machine-generated text generally fall into three categories: watermarking, zero-shot statistical metrics, and supervised deep classifiers \cite{crothers2023machine}.
- *Watermarking:* Involves altering the sampling distribution of LLM logits during token generation by partitioning vocabulary into pseudo-random "green" and "red" lists. While theoretically sound, watermarking requires model provider compliance and is easily washed out via paraphrasing, translation round-tripping, or local open-weight model generation.
- *Zero-Shot Statistical Detectors:* Rely on the observation that autoregressive language models maximize probability under their training distribution. Consequently, machine text tends to exhibit lower perplexity and flatter token loss distributions than human prose. Mitchell et al. introduced *DetectGPT*, which measures the log-probability curvature of perturbed text \cite{mitchell2023detectgpt}. While effective, DetectGPT requires dozens of model forward passes per document, imposing prohibitive computational overhead for institutional batch grading.
- *Supervised Classifiers:* Fine-tune pre-trained transformers (e.g., RoBERTa, DeBERTa) as binary classifiers. While achieving high benchmark accuracy, these models often overfit to specific prompt styles, exhibit out-of-distribution brittleness, and suffer from severe false-positive rates when tested on non-native English speakers \cite{liang2023gpt}.

### 2.3 Document Image Processing and Optical Character Recognition
Document processing in academic settings is complicated by diverse handwriting styles, low contrast, non-uniform illumination, and complex multi-column layouts. Traditional OCR frameworks (e.g., Tesseract) rely on connected-component analysis and LSTM sequence modeling, which deteriorate drastically on cursive handwriting and multi-line equations. Baek et al. introduced CRAFT (Character Region Awareness for Text Detection), which uses a fully convolutional network to predict character affinity and region centers \cite{baek2019character}. For sequence recognition, Li et al. developed TrOCR, which couples a Vision Transformer (ViT) encoder with a RoBERTa text decoder, pre-trained on large-scale synthetic and handwritten datasets \cite{li2022trocr}. Recently, Cui et al. proposed GOT-OCR 2.0 (General OCR Theory), an end-to-end multi-modal vision model capable of transcribing full pages, LaTeX formulas, and complex tables \cite{cui2024got}. However, existing systems have not integrated these specialized vision networks into an automated arbitration and academic integrity pipeline.

---

## 3. System Architecture & Mathematical Foundations

The architecture decouples lightweight synchronous client ingestion from compute-intensive asynchronous vision and neural inference. Figure 1 illustrates the end-to-end dataflow across the seven operational milestones.

```
+-----------------------------------------------------------------------------------+
|                           END-TO-END PIPELINE DATAFLOW                            |
+-----------------------------------------------------------------------------------+
  [ Student / Teacher / HOD Portals ]
                   │
                   ▼  (REST API / JWT Authentication / SHA-256 Hashing)
  [ FastAPI Gateway & Perimeter Security ]
                   │
                   ▼  (Celery Async Queue / Redis Broker)
  [ Stage 1: Document Preprocessing & DPI Normalization (300 DPI, Deskew, Inpaint) ]
                   │
                   ▼
  [ Stage 2: CRAFT Text & Line Detection + Morphological Profiling ]
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
  [ Clean / Cursive ]   [ Math / Tables ]
         │                   │
         ▼                   ▼
    TrOCR Base          GOT-OCR 2.0
         │                   │
         └─────────┬─────────┘
                   ▼  (Confidence < 0.80 Escalation & Levenshtein Consensus)
  [ Stage 3: Result Fusion & Topological Column Reading Order Reconstruction ]
                   │
                   ▼
  [ Stage 4: Curriculum Gate (Syllabus TF-IDF Cosine Filter >= 0.12) ]
                   │
         ┌─────────┴───────────────────────────────┐
         ▼                                         ▼
  [ Stage 5: AI Detection Engine ]          [ Stage 6: Peer Plagiarism Engine ]
   • Qwen 2.5 0.5B Perplexity & Burstiness   • 64-bit dHash Perceptual Hashing
   • 18D Stylometric & Syntactic Features    • Cohort-Isolated N-Gram TF-IDF
   • Calibrated Random Forest Ensemble       • MD5-Cached Similarity Matrix
         │                                         │
         └─────────────────────────┬───────────────┘
                                   ▼
  [ Stage 7: Persisted Audit Record (MySQL / PostgreSQL) & Role-Based UI ]
```

### 3.1 Multi-Tier Layout-Aware Vision OCR Engine

Student submissions range from mobile camera photographs of lined paper to scanned multi-column exam booklets. The vision engine executes an 8-layer sequence designed to produce high-fidelity transcribed text without layout corruption.

#### 3.1.1 Image Preprocessing and Normalization
1. **DPI Normalization:** Input PDFs are rasterized at 300 DPI using PyMuPDF (`fitz`). Camera captures falling below 150 DPI undergo bicubic interpolation to preserve fine stroke contours:
   $$\hat{I}(x, y) = \sum_{i=-1}^{2} \sum_{j=-1}^{2} I(x_i, y_j) W(x - x_i) W(y - y_j)$$
   where $W(t)$ is the standard cubic convolution kernel.
2. **Deskewing:** Skew angles are estimated via probabilistic Hough transform over Canny edge maps. The document is rotated by angle $\theta$:
   $$\theta = \operatorname{median}(\{\arctan(m_k)\}_{k=1}^K)$$
3. **Contrast Enhancement & Sauvola Binarization:** To eliminate non-uniform shadows from mobile camera images, Sauvola local adaptive thresholding is applied:
   $$T(x, y) = \mu(x, y) \cdot \left[1 + k \cdot \left(\frac{\sigma(x, y)}{R} - 1\right)\right]$$
   where $\mu(x, y)$ and $\sigma(x, y)$ denote the local mean and standard deviation in an $N \times N$ window, $R=128$, and $k=0.2$.
4. **Ruled Line Inpainting:** Ruled notebook lines (horizontal blue/gray lines) interfere with character ascenders and descenders. Morphological horizontal kernel opening ($1 \times 35$) isolates continuous ruling lines, which are removed via Telea fast marching inpainting.

#### 3.1.2 Text Detection & Dynamic Routing
Line detection is executed via CRAFT \cite{baek2019character}. CRAFT outputs a pixel-level *Region Score* (presence of characters) and an *Affinity Score* (continuity between adjacent characters). Connected component analysis produces tightly wrapped bounding polygons $\mathcal{B} = \{b_1, b_2, \dots, b_M\}$.

Each detected region $b_m$ is evaluated by a morphological classifier:
- **Aspect Ratio & Stroke Density:**
  $$\rho_s = \frac{\sum_{(x,y) \in b_m} \mathbf{1}(I_{\text{edge}}(x,y) > 0)}{\operatorname{Area}(b_m)}$$
- **Table / Grid Detector:** Horizontal and vertical morphological kernels detect intersecting grid lines. If intersection points $> 4$, the region is categorized as `TABLE`.
- **Mathematical Formula Detector:** Evaluates the presence of isolated horizontal bars (fraction lines), sigma/integral loops, and unbalanced character heights. If detected, categorized as `FORMULA`.
- **Text Lines:** Categorized as `NORMAL`.

#### 3.1.3 Dual Recognition Models & Result Fusion
- **Microsoft TrOCR (`trocr-base-handwritten`):** Standard and cursive text lines are routed to TrOCR \cite{li2022trocr}. The visual encoder (ViT-B) processes the cropped image strip into $16 \times 16$ patches, and an autoregressive RoBERTa decoder generates character sequences via beam search (width $= 4$). The confidence score is computed as the normalized token sequence probability:
  $$C_{\text{TrOCR}} = \exp\left(\frac{1}{|Y|} \sum_{t=1}^{|Y|} \log P(y_t \mid y_{<t}, \mathbf{X})\right)$$
- **GOT-OCR 2.0 (`stepfun-ai/GOT-OCR2_0`):** `TABLE` and `FORMULA` regions, or regions where $C_{\text{TrOCR}} < 0.80$, are routed to GOT-OCR 2.0 \cite{cui2024got}. GOT-OCR generates structured LaTeX notation for formulas and GitHub-flavored Markdown for tables.
- **Levenshtein Consensus Arbitration:** For ambiguous regions evaluated by both models, normalized Levenshtein similarity is computed:
  $$\operatorname{Sim}_{\text{Lev}}(s_1, s_2) = 1.0 - \frac{\operatorname{Lev}(s_1, s_2)}{\max(|s_1|, |s_2|)}$$
  If $\operatorname{Sim}_{\text{Lev}} \ge 0.82$, the higher confidence prediction is adopted. If models disagree drastically ($\operatorname{Sim}_{\text{Lev}} < 0.82$) and both confidences fall below $0.70$, the region is preserved with an explicit `needs_review: true` flag rather than hallucinating erroneous characters.

#### 3.1.4 Multi-Column Layout & Reading Order Reconstruction
Naive OCR systems sort bounding boxes strictly by vertical $y$-coordinate, creating garbled text interleaving across two-column papers. Our **LayoutAnalyzer** performs topological column reconstruction:
1. Identify spanning header blocks where width $w_b > 0.75 \cdot W_{\text{page}}$.
2. Project remaining bounding centroids onto the horizontal $X$-axis to generate a 1D spatial histogram.
3. Compute the primary column gutter $G_x = \arg\min_x \operatorname{Hist}(X)$ in the center quartile $[0.25 W_{\text{page}}, 0.75 W_{\text{page}}]$.
4. Partition regions into Column 0 ($x_{\text{center}} < G_x$) and Column 1 ($x_{\text{center}} \ge G_x$).
5. Sort each partition independently from top to bottom, assembling the document in natural reading flow:
   $$\mathcal{T}_{\text{final}} = [\text{Spanning Headers}] \cup [\text{Col } 0 \downarrow] \cup [\text{Col } 1 \downarrow] \cup [\text{Footers}]$$

---

### 3.2 Multi-Layer AI-Generated Text Attribution Engine

The detection subsystem rejects single-metric heuristics in favor of a layered defense combining neural probability modeling with multi-dimensional stylometry.

#### 3.2.1 Curriculum Gate (Syllabus Cosine Alignment)
Before engaging GPU-intensive neural evaluation, the submission is checked against departmental course syllabi. Using sublinear TF-IDF vectorization:
$$\operatorname{Sim}_{\text{Syllabus}} = \frac{\mathbf{V}_{\text{sub}} \cdot \mathbf{V}_{\text{syllabus}}}{\|\mathbf{V}_{\text{sub}}\|_2 \|\mathbf{V}_{\text{syllabus}}\|_2}$$
If $\operatorname{Sim}_{\text{Syllabus}} < 0.12$, the submission is flagged as off-topic or fraudulent, halting execution and saving computational resources.

#### 3.2.2 Neural Statistical Engine (Qwen 2.5 0.5B Language Model)
Autoregressive language models generate text by sampling from predicted conditional probability distributions. Given token sequence $X = (x_1, x_2, \dots, x_N)$, the token loss is defined as:
$$\mathcal{L}(x_i) = -\log P(x_i \mid x_1, x_2, \dots, x_{i-1})$$

Our local statistical engine deploys **Qwen 2.5 0.5B** to compute three fundamental metrics:
1. **Mean Perplexity (PPL):**
   $$\text{PPL}(X) = \exp\left(\frac{1}{N} \sum_{i=1}^{N} \mathcal{L}(x_i)\right)$$
   LLM-generated text exhibits characteristically low perplexity ($\text{PPL} \in [15.0, 38.0]$) because sampling strategies optimize likelihood under the model distribution. Human writing exhibits significantly higher and widely fluctuating perplexity ($\text{PPL} > 55.0$).
2. **Perplexity Variance & Shannon Entropy:**
   $$\operatorname{Var}(\mathcal{L}) = \frac{1}{N} \sum_{i=1}^{N} (\mathcal{L}(x_i) - \bar{\mathcal{L}})^2, \quad \mathcal{H}(X) = -\sum_{v \in \mathcal{V}} P(v) \log_2 P(v)$$
3. **Sentence Burstiness Coefficient of Variation ($CV$):**
   Human authors exhibit "bursty" writing, interweaving short, punchy declarative remarks with intricate compound-complex sentences. Conversely, LLMs maintain monotonous sentence-to-sentence perplexity. Let $\text{PPL}_s$ denote the mean perplexity of sentence $s \in \{1, \dots, S\}$:
   $$CV_{\text{burstiness}} = \frac{\sigma_{\text{sent}}}{\mu_{\text{sent}}} = \frac{\sqrt{\frac{1}{S}\sum_{s=1}^S (\text{PPL}_s - \bar{\text{PPL}}_s)^2}}{\frac{1}{S}\sum_{s=1}^S \text{PPL}_s}$$
   AI text exhibits $CV < 0.20$, whereas authentic student prose exhibits $CV \in [0.45, 0.85]$.

#### 3.2.3 18-Dimensional Stylometric and Syntactic Feature Space
To ensure resilience against prompt perturbation, temperature scaling, and black-box paraphrasing, we formulate an 18-dimensional numerical feature space $\mathbf{f} \in \mathbb{R}^{18}$ spanning statistical, stylometric, syntactic, structural, readability, and semantic properties:

| # | Feature Identifier | Mathematical Formulation | AI Characteristic | Human Characteristic |
|---|---|---|---|---|
| $f_1$ | `mean_perplexity` | $\exp\left(\frac{1}{N}\sum \mathcal{L}_i\right)$ | Low (15 – 38) | High (> 55) |
| $f_2$ | `perplexity_variance` | $\frac{1}{N}\sum (\mathcal{L}_i - \bar{\mathcal{L}})^2$ | Uniform / Low | Highly variable |
| $f_3$ | `entropy` | $-\sum P(x) \log_2 P(x)$ | Predictable / Low | Lexically erratic |
| $f_4$ | `avg_sentence_length` | $\mu_{sl} = \frac{1}{S}\sum \text{Words}_s$ | Balanced (18 – 24 wds) | Wide dispersion |
| $f_5$ | `sentence_length_std` | $\sigma_{sl} = \sqrt{\operatorname{Var}(\text{Words}_s)}$ | Low ($\sigma < 4.0$) | High ($\sigma > 8.0$) |
| $f_6$ | `type_token_ratio` | $\text{TTR} = \frac{|\mathcal{V}_{\text{doc}}|}{N_{\text{total}}}$ | Moderate / Regular | Idiosyncratic |
| $f_7$ | `stop_word_ratio` | $\frac{N_{\text{stop}}}{N_{\text{total}}}$ | Rigid scaffolding | Context-dependent |
| $f_8$ | `punctuation_frequency` | $\frac{N_{\text{punct}}}{N_{\text{total}}}$ | Symmetrical commas/dashes | Irregular / Minimal |
| $f_9$ | `contraction_ratio` | $\frac{N_{\text{contractions}}}{N_{\text{total}}}$ | Rare in academic mode | Frequent colloquialisms |
| $f_{10}$ | `noun_ratio` | $\frac{N_{\text{noun}}}{N_{\text{total}}}$ (spaCy POS) | Dense nominal phrases | Varied |
| $f_{11}$ | `verb_ratio` | $\frac{N_{\text{verb}}}{N_{\text{total}}}$ (spaCy POS) | Balanced tense structures | Narrative-driven |
| $f_{12}$ | `adjective_ratio` | $\frac{N_{\text{adj}}}{N_{\text{total}}}$ (spaCy POS) | Embellished descriptors | Sparse |
| $f_{13}$ | `named_entity_density` | $\frac{N_{\text{entities}}}{N_{\text{total}}}$ | High general entities | Specific local entities |
| $f_{14}$ | `avg_paragraph_length` | $\frac{S_{\text{total}}}{P_{\text{total}}}$ | Structured 4–5 sentences | Highly variable |
| $f_{15}$ | `flesch_reading_ease` | $206.835 - 1.015\left(\frac{W}{S}\right) - 84.6\left(\frac{\text{Syll}}{W}\right)$ | Undergraduate (45 – 65) | Extreme extremes |
| $f_{16}$ | `generic_phrasing` | $\frac{\text{ClicheCount} \times 1000}{N_{\text{total}}}$ | Dense summary platitudes | Rare |
| $f_{17}$ | `lack_of_personal_voice` | $1.0 - \frac{N_{\text{1stPersonPronouns}}}{N_{\text{total}}}$ | Approaching 1.0 | Lower (uses "I", "we") |
| $f_{18}$ | `over_structured_coherence`| $\frac{\text{AITransitions} \times 1000}{N_{\text{total}}}$ | High ("Furthermore", etc.) | Organic transitions |

#### 3.2.4 Calibrated Random Forest Classification & Decision Tiering
The raw vector is normalized using pre-computed z-score standardization:
$$\mathbf{z} = \frac{\mathbf{f} - \boldsymbol{\mu}}{\boldsymbol{\sigma}}$$
The normalized vector is evaluated by a trained ensemble of 200 de-correlated decision trees with balanced class weighting \cite{breiman2001random}:
$$P(\text{AI} \mid \mathbf{z}) = \frac{1}{200} \sum_{t=1}^{200} P_t(\text{AI} \mid \mathbf{z})$$

To protect students against false accusations, we implement a **Three-Tier Calibrated Decision Policy**:
- **Tier 1: Original Human Content ($P(\text{AI}) < 30.0\%$):** Cleared automatically.
- **Tier 2: Mixed / AI-Assisted Content ($30.0\% \le P(\text{AI}) < 70.0\%$):** Flagged for manual teacher evaluation; no punitive action can be taken automatically.
- **Tier 3: Pure AI-Generated Content ($P(\text{AI}) \ge 70.0\%$):** High-confidence classification supported by feature attribution reports.

---

### 3.3 Dual-Tier Peer-to-Peer Plagiarism Engine

Student collusion frequently takes the form of document sharing, where an assignment is copied with minor rephrasing or an identical photo scan is uploaded under multiple accounts.

#### 3.3.1 Tier 1: Perceptual Difference Hashing (Visual Resubmission)
To detect identical visual submissions (including re-scans or image re-uploads), the engine computes a 64-bit difference hash ($\text{dHash}$):
1. Convert the rendered document page to an $8\text{-bit}$ grayscale image.
2. Downsample to a $(9 \times 8)$ pixel grid.
3. Compare adjacent horizontal pixels to construct a 64-bit binary sequence:
   $$h_k = \begin{cases} 1 & \text{if } I(x+1, y) > I(x, y) \\ 0 & \text{otherwise} \end{cases} \quad \text{for } x \in [0, 7], y \in [0, 7]$$
4. Compute Hamming distance $\mathcal{D}_H(h_A, h_B)$ against prior cohort submissions. If $\mathcal{D}_H \le 3$ bits, the submission is flagged as an exact visual replica ($100\%$ visual plagiarism match).

#### 3.3.2 Tier 2: Cohort-Isolated TF-IDF Cosine Similarity
Plagiarism is evaluated strictly within the same subject and department, excluding the student's own prior drafts:
1. Extract unigrams and bigrams ($n \in \{1, 2\}$) with standard stop-word removal.
2. Build an $L_2$-normalized sparse TF-IDF matrix over vocabulary $\mathcal{V}$ ($|\mathcal{V}| \le 5,000$):
   $$\text{TF-IDF}(t, d) = \left(1 + \log \text{TF}(t, d)\right) \cdot \log\left(\frac{|\mathcal{D}| + 1}{\operatorname{DF}(t) + 1}\right)$$
3. Compute pairwise cosine similarity against all $K$ submissions in the peer cohort:
   $$\operatorname{Sim}_{\text{peer}}(d_{\text{target}}, d_k) = \frac{\mathbf{v}_{\text{target}} \cdot \mathbf{v}_k}{\|\mathbf{v}_{\text{target}}\|_2 \|\mathbf{v}_k\|_2}$$
   $$\text{Score}_{\text{plag}} = \max_{k \in \{1, \dots, K\}} \left(\operatorname{Sim}_{\text{peer}}(d_{\text{target}}, d_k)\right) \times 100$$
4. **MD5 Matrix Caching:** To prevent quadratic $O(K^2)$ recomputation as class submissions accumulate, the fitted vectorizer and corpus matrix are cached in memory keyed by the MD5 hash of the sorted cohort submission IDs.

---

## 4. Experimental Setup & Benchmark Evaluation

### 4.1 Benchmark Dataset Construction
To train and evaluate the detection framework, we constructed a comprehensive benchmark corpus of 2,739 curated academic essays and assignments. The raw dataset was processed through a 5-phase engineering pipeline:
1. **Phase 1 (Data Cleaning):** HTML tags stripped, Unicode normalized (NFKD), whitespace and line-break artifacts cleaned, and explicit prompt leakage phrases (e.g., *"As an AI language model..."*, *"Certainly, here is an essay..."*) systematically removed via regex filters.
2. **Phase 2 (Class Balancing):** To prevent machine learning bias from extreme class imbalances, the dataset was undersampled to a controlled $2:1$ AI-to-Human ratio.
3. **Phase 3 (Feature Extraction):** All 18 stylometric, syntactic, and neural perplexity features were extracted across every sample.
4. **Phase 4 (Stratified Splitting):** Stratified $80/20$ train-test partitioning yielding **2,155 training samples** and **584 held-out test samples**.
5. **Phase 5 (Model Training):** 200 de-correlated estimators with maximum depth 10.

```
+-----------------------------------------------------------------------------------+
|                        BENCHMARK DATASET CHARACTERISTICS                          |
+-----------------------------------------------------------------------------------+
  Total Evaluated Samples:      2,739 Essays
  Training Partition:           2,155 Samples (Human: 708, AI: 1,447)
  Held-Out Test Partition:      584 Samples   (Human: 189, AI: 395)
  AI Generation Engines:        GPT-4o, Claude 3.5 Sonnet, Llama 3 70B
  Human Submissions:            Authentic undergraduate coursework & examination essays
```

---

## 5. Empirical Results & Discussion

### 5.1 AI-Generated Text Classification Performance

The Random Forest model was evaluated on the 584 held-out test samples. Table 1 summarizes the performance metrics across all evaluation criteria.

```
+-----------------------------------------------------------------------------------+
|               TABLE 1: QUANTITATIVE CLASSIFICATION PERFORMANCE                    |
+-----------------------------------------------------------------------------------+
  Metric                                   Train Set               Test Set (Held-Out)
  ---------------------------------------------------------------------------------
  Accuracy                                  100.00%                      97.43%
  Precision (AI Detection)                     --                        99.22%
  Recall (AI Detection)                        --                        96.96%
  F1-Score (AI Detection)                      --                        98.08%
  ROC-AUC                                      --                        0.9924
  Specificity (True Negative Rate)             --                        98.41%
  False Positive Rate (FPR on Humans)          --                         1.59%
```

#### Detailed Confusion Matrix Analysis
Evaluating test set predictions against ground truth yields the following confusion matrix:

$$\begin{pmatrix} \text{True Negatives (Human)} & \text{False Positives (Human} \to \text{AI)} \\ \text{False Negatives (AI} \to \text{Human)} & \text{True Positives (AI)} \end{pmatrix} = \begin{pmatrix} 186 & 3 \\ 12 & 383 \end{pmatrix}$$

- **True Negatives ($TN = 186$):** 186 of 189 authentic student essays were correctly identified as human writing.
- **False Positives ($FP = 3$):** Only 3 authentic human essays were misclassified as AI, yielding an exceptionally low false-positive rate of **1.59%**. This low FPR is crucial for academic integrity systems, where false accusations can destroy student careers.
- **False Negatives ($FN = 12$):** 12 of 395 AI essays evaded high-confidence classification, typically occurring in very brief answers (< 80 words) where stylometric variance is constrained.
- **True Positives ($TP = 383$):** 383 AI submissions were successfully detected, demonstrating high sensitivity across multiple LLM families.

```
+-----------------------------------------------------------------------------------+
|                      FIGURE 2: DETAILED CLASSIFICATION MATRIX                     |
+-----------------------------------------------------------------------------------+
                                   PREDICTED CLASS
                           Human (0)             AI (1)
                     +--------------------+--------------------+
        Human (0)    |   TN = 186         |   FP = 3           |   Total = 189
  TRUE               |   (98.41%)         |   (1.59%)          |
  CLASS              +--------------------+--------------------+
        AI (1)       |   FN = 12          |   TP = 383         |   Total = 395
                     |   (3.04%)          |   (96.96%)         |
                     +--------------------+--------------------+
```

### 5.2 Feature Importance Ranking

Gini impurity feature importance analysis across the 200 ensemble trees reveals which linguistic markers most effectively distinguish LLM prose from authentic student writing:

```
+-----------------------------------------------------------------------------------+
|               TABLE 2: FEATURE IMPORTANCE RANKING (GINI IMPORTANCE)               |
+-----------------------------------------------------------------------------------+
  Rank   Feature Identifier           Importance Weight   Primary Discriminator
  ---------------------------------------------------------------------------------
  1      avg_paragraph_length              0.2632         Structural Symmetry
  2      mean_perplexity                   0.1668         Token Likelihood Surprise
  3      entropy                           0.1568         Information Density
  4      flesch_reading_ease               0.1099         Syllable-to-Word Ratio
  5      perplexity_variance               0.0631         Loss Fluctuation Rate
  6      stop_word_ratio                   0.0571         Syntactic Scaffolding
  7      type_token_ratio                  0.0392         Lexical Richness
  8      sentence_length_std               0.0274         Sentence Burstiness
  9      noun_ratio                        0.0177         Nominal Packaging
  10     avg_sentence_length               0.0171         Clustered Sentence Length
  11     over_structured_coherence         0.0144         Transition Phrases
  12     verb_ratio                        0.0129         Action Verb Distribution
  13     adjective_ratio                   0.0126         Descriptive Embellishment
  14     named_entity_density              0.0106         Entity Packaging
  15     punctuation_frequency             0.0106         Punctuation Balance
  16     lack_of_personal_voice            0.0106         Objective 3rd-Person Stance
  17     generic_phrasing                  0.0055         Platitude Frequency
  18     contraction_ratio                 0.0043         Colloquial Usage
```

The top 4 features (`avg_paragraph_length`, `mean_perplexity`, `entropy`, and `flesch_reading_ease`) account for over **69.6%** of total discriminative power. AI models consistently generate rigidly uniform paragraphs (typically 4–5 sentences) and exhibit predictable, low-entropy token sequences, whereas human student writing is structurally irregular and lexically spontaneous.

### 5.3 OCR Vision Pipeline Performance

To assess the multi-tier vision pipeline, we benchmarked the system against 100 scanned academic test pages containing cursive handwriting, mathematical derivations, and two-column layouts. We compared our hybrid **CRAFT + TrOCR + GOT-OCR 2.0** pipeline against standard Tesseract v5.0 and standalone EasyOCR.

```
+-----------------------------------------------------------------------------------+
|               TABLE 3: OCR BENCHMARK ON ACADEMIC ASSIGNMENTS                      |
+-----------------------------------------------------------------------------------+
  Architecture                 CER (%) ↓     WER (%) ↓    Formula LaTeX    Layout Acc.
  ---------------------------------------------------------------------------------
  Tesseract 5.0 (Baseline)       24.8%         38.2%          Fail            41.2%
  EasyOCR (Baseline)             18.4%         29.1%          Fail            58.6%
  Our Multi-Tier OCR Pipeline     3.9%          6.2%       94.1% Valid        98.4%
```

- **Character Error Rate (CER) and Word Error Rate (WER):** Our pipeline achieved a CER of **3.9%** and WER of **6.2%** on student cursive handwriting, representing an **83.7% error reduction** over baseline Tesseract.
- **Mathematical Formula Transcription:** By dynamically routing mathematical bounding boxes to GOT-OCR 2.0, **94.1%** of formulas were converted into syntactically valid LaTeX notation, whereas legacy baselines produced unreadable character sequences.
- **Column Order Integrity:** The topological column sorter achieved **98.4%** layout reconstruction accuracy, preventing column text interleaving across two-column exam sheets.

### 5.4 Computational Efficiency & Hardware Profiling

The framework was evaluated on an affordable edge-workstation configuration (AMD Ryzen 7 5800X, 32 GB RAM, single NVIDIA RTX 3060 12 GB GPU). Table 4 details the memory footprint and latency profile for each pipeline stage.

```
+-----------------------------------------------------------------------------------+
|                TABLE 4: COMPUTE BUDGET & LATENCY BENCHMARKS                       |
+-----------------------------------------------------------------------------------+
  Component                 Parameters     VRAM / RAM      Device      Latency / Unit
  ---------------------------------------------------------------------------------
  OpenCV Preprocessor           --          ~50 MB RAM      CPU         180 ms / page
  CRAFT Text Detector         20.7 M       ~180 MB VRAM     CUDA        450 ms / page
  TrOCR Base Handwritten     334.0 M       ~1.3 GB VRAM     CUDA (FP16) 110 ms / line
  GOT-OCR 2.0                580.0 M       ~2.2 GB VRAM     CUDA (FP16) 1.6 s / region
  Qwen 2.5 LM                490.0 M       ~1.1 GB VRAM     CUDA (FP16) 320 ms / essay
  Random Forest Classifier   200 Trees      ~15 MB RAM      CPU          < 4 ms / vector
  TF-IDF Plagiarism Engine    5k Vocab      ~30 MB RAM      CPU          22 ms / cohort
```

Total peak GPU memory consumption remained under **4.8 GB VRAM**, enabling continuous batch inference on consumer-grade workstation GPUs without requiring expensive enterprise data center infrastructure.

---

## 6. Institutional Ethics, Policy & False-Positive Mitigation

The deployment of automated AI detection software in academia introduces severe ethical and policy challenges. Monolithic, high-FPR detectors disproportionately harm vulnerable student demographics, particularly English as a Second Language (ESL) learners whose writing naturally exhibits lower syntactic perplexity \cite{liang2023gpt}.

Our framework introduces three critical institutional safeguards:
1. **Conservative Classification Policy:** Submissions scoring between $30\%$ and $70\%$ are classified as *"Mixed / Requires Instructor Review"*. The software explicitly disallows punitive grade deductions on Tier 2 classifications without independent faculty verification.
2. **Explainable Forensic Attribution:** Rather than presenting a single black-box percentage, the user interface provides teachers with full feature breakdowns: sentence burstiness curves, highlighted low-perplexity passages, and vocabulary entropy charts, enabling evidence-based student-instructor dialogue.
3. **FERPA and GDPR Compliance by Design:** All OCR transcription, language model inference, and plagiarism comparisons execute locally within the institution's private intranet. Zero student data is exfiltrated to external commercial APIs, preserving student copyright and satisfying institutional privacy mandates.

---

## 7. Conclusion & Future Work

In this paper, we introduced an end-to-end, multi-modal academic integrity framework that addresses the core challenges of contemporary plagiarism and AI-generated content detection. By coupling an 8-layer layout-aware OCR vision pipeline (CRAFT + TrOCR + GOT-OCR 2.0) with an adversarial defense-in-depth detection architecture (Qwen 2.5 0.5B neural perplexity + 18-dimensional stylometry + calibrated Random Forest) and a dual-tier peer plagiarism engine, the platform bridges the gap between physical student submissions and digital text verification.

Empirical evaluation on a balanced benchmark of 2,739 essays demonstrated **97.43% test accuracy**, **99.22% precision**, **98.08% F1-score**, and **0.9924 ROC-AUC**, while maintaining an exceptionally low false-positive rate of **1.59%** on authentic human student writing. The entire platform runs locally on standard institutional hardware with sub-5 GB VRAM utilization, guaranteeing complete compliance with student privacy regulations.

**Future Work:** Future research will explore:
1. Multimodal adversarial defenses against diffusion-generated handwriting and digital font rendering;
2. Cross-lingual stylometric transfer for multilingual assignment verification;
3. Self-supervised continual learning loops that adapt feature weights as generative LLM architectures evolve.

---

## References

1. T. Brown et al., "Language models are few-shot learners," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 1877–1901, 2020.
2. J. Achiam et al., "GPT-4 technical report," *arXiv preprint arXiv:2303.08774*, 2023.
3. E. Mitchell, Y. Lee, A. Khazatsky, C. D. Manning, and C. Finn, "DetectGPT: Zero-shot machine-generated text detection using probability curvature," in *International Conference on Machine Learning (ICML)*, pp. 24950–24962, 2023.
4. M. Li et al., "TrOCR: Transformer-based optical character recognition with pre-trained models," in *Proceedings of the AAAI Conference on Artificial Intelligence*, vol. 37, no. 11, pp. 13094–13102, 2023.
5. Y. Baek, B. Lee, D. Han, S. Yun, and H. Lee, "Character region awareness for text detection," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 9365–9374, 2019.
6. H. Cui, H. Wang, Z. Lin, D. Liang, and P. Liu, "General OCR Theory: Towards OCR-2.0 via a Unified End-to-End Model," *arXiv preprint arXiv:2409.01704*, 2024.
7. A. Yang et al., "Qwen2.5 technical report," *arXiv preprint arXiv:2412.15115*, 2024.
8. E. Crothers, N. Japkowicz, and H. L. Viktor, "Machine-generated text: A comprehensive survey of threat models and detection methods," *IEEE Access*, vol. 11, pp. 70977–71002, 2023.
9. W. Liang, M. Yuksekgonul, Y. Mao, E. Wu, and J. Zou, "GPT detectors are biased against non-native English writers," *Patterns*, vol. 4, no. 7, p. 100779, 2023.
10. T. Foltýnek et al., "Academic integrity in the age of artificial intelligence: A systematic literature review," *International Journal of Educational Technology in Higher Education*, vol. 20, no. 1, pp. 1–24, 2023.
11. N. Meuschke and B. Gipp, "State-of-the-art in detecting academic plagiarism," *International Journal for Educational Integrity*, vol. 9, no. 2, pp. 50–71, 2013.
12. G. Salton and C. Buckley, "Term-weighting approaches in automatic text retrieval," *Information Processing & Management*, vol. 24, no. 5, pp. 513–523, 1988.
13. L. Breiman, "Random forests," *Machine Learning*, vol. 45, no. 1, pp. 5–32, 2001.
14. J. P. Kincaid, R. P. Fishburne Jr, R. L. Rogers, and B. S. Chissom, "Derivation of new readability formulas (Automated Readability Index, Fog Count and Flesch Reading Ease Formula) for Navy enlisted personnel," *Chief of Naval Technical Training*, Research Branch Report 8-75, 1975.
15. M. Zaheer et al., "Big bird: Transformers for longer sequences," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 17283–17297, 2020.
