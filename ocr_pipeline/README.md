# Multi-Model Assignment OCR Pipeline (CRAFT + TrOCR + GOT-OCR 2.0)

A modular, production-oriented OCR pipeline designed specifically for extracting highly accurate and structured content from academic student assignments (printed and handwritten, single and multi-column, equations, and tables).

---

## 1. System Architecture

```text
                    [ Student Assignment PDF / Image ]
                                   │
                                   ▼
                    [ Preprocessing & Normalization ]
                      (Deskew, Shadow Removal, Denoise)
                                   │
                                   ▼
                         [ CRAFT Text Detector ]
                      (Pixel-level Word & Line Bounding)
                                   │
                                   ▼
                         [ Region Analyzer ]
                      (Visual & Morphological Profiling)
                                   │
                                   ▼
                       [ Intelligent Region Router ]
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
     [ Normal Text ]       [ Complex Region ]    [ Uncertain Region ]
             │                     │                     │
             ▼                     ▼                     ▼
          TrOCR                GOT-OCR 2.0           TrOCR + GOT
             │                     │                     │
             │ (if conf < 0.80)    │                     │
             └──────────► GOT-OCR 2.0                    │
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   ▼
                         [ Result Fusion ]
              (Disagreement detection, specialty weighting,
               conflict resolution, alternative tracking)
                                   │
                                   ▼
                    [ Layout & Reading Order ]
              (Multi-column clustering, topological sort)
                                   │
                                   ▼
                       [ Assignment Parser ]
              (Questions, answers, subparts, metadata)
                                   │
                                   ▼
                   [ Unified Structured JSON Output ]
```

---

## 2. Model Roles & Specializations

| Model | Primary Responsibility | Input Format | Output Format |
|---|---|---|---|
| **CRAFT** | **Text Detection**: Locates text lines/boxes. NEVER recognizes characters. | Full page image | Bounding boxes `[x1,y1,x2,y2]`, Polygons, Detection confidence |
| **TrOCR** | **High-Precision Text Recognition**: Clean printed lines, handwriting lines, individual paragraphs. | Cropped line images | Clean text string, normalized token log-prob confidence |
| **GOT-OCR 2.0** | **Complex & Document-Level OCR**: Mathematical equations, tables, dense structured documents, escalation fallback. | Cropped complex regions or full page | Formatted LaTeX equations, Markdown/HTML tables |
| **Fusion Engine** | **Arbitration**: Compares outputs, applies specialization weights, flags ambiguous regions (`needs_review: true`). | TrOCR + GOT outputs | Single calibrated result with full alternatives preserved |

---

## 3. Intelligent Routing & Confidence Escalation

1. **Routing**:
   - Analyzes aspect ratio, stroke density, horizontal/vertical grid lines, and high-frequency Laplacian edge variance.
   - Grid lines present $\rightarrow$ Routed to **GOT-OCR** (Table mode).
   - Fraction bars / math symbols present $\rightarrow$ Routed to **GOT-OCR** (Formula mode).
   - Clean text line $\rightarrow$ Routed to **TrOCR**.
2. **Escalation**:
   - If TrOCR's confidence drops below the configurable threshold (`confidence_threshold: 0.80`), it is automatically escalated to GOT-OCR for a second opinion.
   - The Fusion module reconciles both predictions without hallucinating missing text.

---

## 4. Multi-Column Reading Order Reconstruction

Naive OCR systems sort all text top-to-bottom by vertical Y-coordinate, creating garbled text in 2-column papers (`Col1 Line1` + `Col2 Line1` interleaved).

The **LayoutAnalyzer**:
- Isolates spanning headers (assignment title, student information).
- Clusters remaining regions into distinct column gutters (Column 0, Column 1, etc.).
- Reconstructs natural human reading flow: **Header $\rightarrow$ Column 1 (Top to Bottom) $\rightarrow$ Column 2 (Top to Bottom) $\rightarrow$ Footer**.

---

## 5. Configuration (`ocr_pipeline/config/config.yaml`)

All thresholds, model paths, and hardware parameters are strictly externalized:

```yaml
models:
  craft:
    text_threshold: 0.7
    min_size: 15
    add_margin: 0.15

  trocr:
    model_path: "backend/models/trocr_finetuned"
    fallback_model: "microsoft/trocr-base-handwritten"
    device: "auto"
    fp16: true
    batch_size: 8

  got:
    enabled: true
    lazy_load: true
    model_name: "stepfun-ai/GOT-OCR2_0"
    device: "auto"
    fp16: true

routing:
  confidence_threshold: 0.80
  escalate_to_got: true
```

---

## 6. Running the Progressive Test Suite

Execute the full suite of 6 progressive tests:

```bash
pytest ocr_pipeline/tests -v
```

- `test_detection.py`: CRAFT bounding box extraction, noise filtering, and line grouping.
- `test_trocr.py`: **Test 1** (Clean printed text) and **Test 2** (Handwritten line recognition).
- `test_got.py`: **Test 3** (Mathematical equations) and **Test 4** (Tables).
- `test_fusion.py`: **Test 5** (Noisy text confidence escalation, model agreement, and review flagging).
- `test_layout.py`: Multi-column layout distinction and reading order sorting without interleaving.
- `test_pipeline.py`: **Test 6** (Full end-to-end 2-column assignment parsing).

---

## 7. Starting the REST API

```bash
uvicorn ocr_pipeline.api.app:app --host 0.0.0.0 --port 8001 --reload
```

Endpoints:
- `POST /api/v1/ocr/process-file`: Upload PDF or image for structured OCR parsing.
- `GET /health`: Device, VRAM, and model status.
- `POST /api/v1/ocr/clear-vram`: Explicit PyTorch CUDA memory cache release.
