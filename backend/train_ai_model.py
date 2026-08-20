"""
Train AI Detection Model
==========================
Wrapper script to retrain the AI detection model using the full data pipeline.

Usage:
    python train_ai_model.py           # Run full pipeline (Phase 1-5)
    python train_ai_model.py --phase N # Run specific phase only

The trained model (rf_model_v2.pkl, scaler_v2.pkl) is automatically copied
to backend/services/ml_services/ after successful training.
"""

import os
import sys
import shutil

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(__file__))

PIPELINE_DIR = os.path.join(os.path.dirname(__file__), "data_pipeline")
ML_SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services", "ml_services")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")


def run_pipeline(start_phase=1):
    """Run the data pipeline from the specified phase."""

    phases = {
        1: ("Phase 1: Data Cleaning", "phase1_clean"),
        2: ("Phase 2: Label Encoding & Balancing", "phase2_label"),
        3: ("Phase 3: Feature Extraction", "phase3_features"),
        4: ("Phase 4: Feature Scaling & Split", "phase4_split"),
        5: ("Phase 5: Model Training & Evaluation", "phase5_train"),
    }

    for phase_num in range(start_phase, 6):
        name, module_name = phases[phase_num]
        print(f"\n{'#' * 60}")
        print(f"# {name}")
        print(f"{'#' * 60}\n")

        module = __import__(f"data_pipeline.{module_name}", fromlist=[f"run_phase{phase_num}"])
        run_func = getattr(module, f"run_phase{phase_num}")
        run_func()

    # --- Deploy model to ml_services ---
    print(f"\n{'#' * 60}")
    print(f"# Deploying model to live system")
    print(f"{'#' * 60}\n")

    files_to_copy = {
        "rf_model.pkl": "rf_model_v2.pkl",
        "scaler.pkl": "scaler_v2.pkl",
        "feature_names.json": "feature_names.json",
    }

    for src_name, dst_name in files_to_copy.items():
        src = os.path.join(OUTPUT_DIR, src_name)
        dst = os.path.join(ML_SERVICES_DIR, dst_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {src_name} -> {dst_name}")
        else:
            print(f"  WARNING: {src_name} not found, skipping.")

    print(f"\nTraining and deployment complete!")
    print(f"Restart the backend server to load the new model.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train AI Detection Model")
    parser.add_argument("--phase", type=int, default=1,
                        help="Start from this phase (1-5, default: 1)")
    args = parser.parse_args()

    run_pipeline(start_phase=args.phase)
