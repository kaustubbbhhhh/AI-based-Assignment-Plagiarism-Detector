"""
Phase 5: Model Training & Evaluation
=======================================
Trains a Random Forest classifier on the extracted features and
produces a comprehensive evaluation report.

Steps:
  1. Load train/test splits from Phase 4
  2. Train RandomForestClassifier
  3. Evaluate: Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC
  4. Feature importance analysis
  5. Save model + evaluation artifacts

Input:  backend/data_pipeline/output/X_train.pkl, X_test.pkl, y_train.pkl, y_test.pkl
Output: rf_model.pkl, evaluation_report.txt, confusion_matrix.png, roc_curve.png, feature_importance.png
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")


def load_pickle(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(data, f)


def run_phase5():
    print("=" * 60)
    print("PHASE 5: Model Training & Evaluation")
    print("=" * 60)

    # --- Step 1: Load data ---
    print(f"\n[Step 1] Loading train/test data...")

    X_train = load_pickle("X_train.pkl")
    X_test = load_pickle("X_test.pkl")
    y_train = load_pickle("y_train.pkl")
    y_test = load_pickle("y_test.pkl")

    # Load feature names
    with open(os.path.join(OUTPUT_DIR, "feature_names.json"), "r") as f:
        feature_names = json.load(f)

    print(f"  X_train: {X_train.shape}")
    print(f"  X_test:  {X_test.shape}")
    print(f"  y_train: {y_train.shape} (Human={np.sum(y_train==0)}, AI={np.sum(y_train==1)})")
    print(f"  y_test:  {y_test.shape} (Human={np.sum(y_test==0)}, AI={np.sum(y_test==1)})")

    # --- Step 2: Train model ---
    print(f"\n[Step 2] Training RandomForestClassifier...")
    print(f"  Parameters: n_estimators=200, max_depth=10, class_weight='balanced'")

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    print(f"  Training complete.")

    # --- Step 3: Predictions ---
    print(f"\n[Step 3] Generating predictions...")

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]  # probability of AI class

    train_pred = clf.predict(X_train)

    # --- Step 4: Evaluation metrics ---
    print(f"\n[Step 4] Evaluation Results")
    print(f"{'=' * 60}")

    # Accuracy
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"\n  Accuracy:")
    print(f"    Train: {train_acc*100:.2f}%")
    print(f"    Test:  {test_acc*100:.2f}%")

    # Precision, Recall, F1
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print(f"\n  Test Set Metrics (for AI class):")
    print(f"    Precision: {precision*100:.2f}%")
    print(f"    Recall:    {recall*100:.2f}%")
    print(f"    F1-Score:  {f1*100:.2f}%")

    # ROC-AUC
    roc_auc = roc_auc_score(y_test, y_prob)
    print(f"    ROC-AUC:   {roc_auc:.4f}")

    # Full classification report
    print(f"\n  Classification Report:")
    report = classification_report(y_test, y_pred, target_names=["Human (0)", "AI (1)"])
    print(report)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:")
    print(f"                 Predicted")
    print(f"                Human    AI")
    print(f"    Actual Human  {cm[0][0]:4d}  {cm[0][1]:4d}")
    print(f"    Actual AI     {cm[1][0]:4d}  {cm[1][1]:4d}")

    tn, fp, fn, tp = cm.ravel()
    print(f"\n    True Negatives (correct Human):  {tn}")
    print(f"    False Positives (Human -> AI):    {fp}")
    print(f"    False Negatives (AI -> Human):    {fn}")
    print(f"    True Positives (correct AI):      {tp}")

    # --- Step 5: Feature importance ---
    print(f"\n[Step 5] Feature Importance (top 10):")

    importances = clf.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False)

    for i, row in importance_df.head(10).iterrows():
        bar = "#" * int(row["importance"] * 100)
        print(f"    {row['feature']:30s} {row['importance']:.4f} {bar}")

    # --- Step 6: Generate plots ---
    print(f"\n[Step 6] Generating evaluation plots...")

    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        # --- Confusion Matrix Plot ---
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
        plt.colorbar(im, ax=ax)

        classes = ["Human (0)", "AI (1)"]
        tick_marks = [0, 1]
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(classes)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(classes)
        ax.set_ylabel("Actual", fontsize=12)
        ax.set_xlabel("Predicted", fontsize=12)

        # Add text annotations
        for i in range(2):
            for j in range(2):
                color = "white" if cm[i, j] > cm.max() / 2 else "black"
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        fontsize=18, fontweight="bold", color=color)

        plt.tight_layout()
        cm_path = os.path.join(OUTPUT_DIR, "confusion_matrix.png")
        plt.savefig(cm_path, dpi=150)
        plt.close()
        print(f"  Saved: confusion_matrix.png")

        # --- ROC Curve Plot ---
        fpr, tpr, thresholds = roc_curve(y_test, y_prob)

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(fpr, tpr, color="#e94560", lw=2,
                label=f"ROC Curve (AUC = {roc_auc:.4f})")
        ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--",
                label="Random Baseline")
        ax.set_xlabel("False Positive Rate", fontsize=12)
        ax.set_ylabel("True Positive Rate", fontsize=12)
        ax.set_title("ROC Curve", fontsize=14, fontweight="bold")
        ax.legend(loc="lower right", fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        roc_path = os.path.join(OUTPUT_DIR, "roc_curve.png")
        plt.savefig(roc_path, dpi=150)
        plt.close()
        print(f"  Saved: roc_curve.png")

        # --- Feature Importance Plot ---
        fig, ax = plt.subplots(figsize=(10, 6))
        top_features = importance_df.head(15)
        bars = ax.barh(
            range(len(top_features)),
            top_features["importance"].values,
            color="#0f3460",
            edgecolor="#e94560",
        )
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features["feature"].values, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel("Importance", fontsize=12)
        ax.set_title("Feature Importance (Random Forest)", fontsize=14, fontweight="bold")
        ax.grid(True, axis="x", alpha=0.3)

        plt.tight_layout()
        fi_path = os.path.join(OUTPUT_DIR, "feature_importance.png")
        plt.savefig(fi_path, dpi=150)
        plt.close()
        print(f"  Saved: feature_importance.png")

    except ImportError:
        print(f"  WARNING: matplotlib not installed. Skipping plots.")

    # --- Step 7: Save model + report ---
    print(f"\n[Step 7] Saving model and report...")

    save_pickle(clf, "rf_model.pkl")
    print(f"  Saved: rf_model.pkl")

    # Save text report
    report_path = os.path.join(OUTPUT_DIR, "evaluation_report.txt")
    with open(report_path, "w") as f:
        f.write("AI Detection Model - Evaluation Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Model: RandomForestClassifier\n")
        f.write(f"  n_estimators: 200\n")
        f.write(f"  max_depth: 10\n")
        f.write(f"  class_weight: balanced\n\n")
        f.write(f"Dataset:\n")
        f.write(f"  Train: {X_train.shape[0]} samples\n")
        f.write(f"  Test:  {X_test.shape[0]} samples\n")
        f.write(f"  Features: {X_train.shape[1]}\n\n")
        f.write(f"Results:\n")
        f.write(f"  Train Accuracy: {train_acc*100:.2f}%\n")
        f.write(f"  Test Accuracy:  {test_acc*100:.2f}%\n")
        f.write(f"  Precision:      {precision*100:.2f}%\n")
        f.write(f"  Recall:         {recall*100:.2f}%\n")
        f.write(f"  F1-Score:       {f1*100:.2f}%\n")
        f.write(f"  ROC-AUC:        {roc_auc:.4f}\n\n")
        f.write(f"Classification Report:\n{report}\n")
        f.write(f"Confusion Matrix:\n{cm}\n\n")
        f.write(f"Feature Importance:\n")
        for _, row in importance_df.iterrows():
            f.write(f"  {row['feature']:30s} {row['importance']:.4f}\n")

    print(f"  Saved: evaluation_report.txt")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"PHASE 5 COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Test Accuracy:  {test_acc*100:.2f}%")
    print(f"  Test F1-Score:  {f1*100:.2f}%")
    print(f"  Test ROC-AUC:   {roc_auc:.4f}")
    print(f"  Top feature:    {importance_df.iloc[0]['feature']}")

    # Quality gates
    print(f"\n  Quality Gates:")
    f1_pass = f1 >= 0.80
    recall_human = recall_score(y_test, y_pred, pos_label=0)
    recall_ai = recall_score(y_test, y_pred, pos_label=1)
    recall_pass = recall_human >= 0.70 and recall_ai >= 0.70

    print(f"    F1 >= 0.80:           {'PASS' if f1_pass else 'FAIL'} ({f1:.4f})")
    print(f"    Human recall >= 0.70: {'PASS' if recall_human >= 0.70 else 'FAIL'} ({recall_human:.4f})")
    print(f"    AI recall >= 0.70:    {'PASS' if recall_ai >= 0.70 else 'FAIL'} ({recall_ai:.4f})")

    if f1_pass and recall_pass:
        print(f"\n  ALL QUALITY GATES PASSED. Model is ready for Phase 6 integration.")
    else:
        print(f"\n  SOME GATES FAILED. Consider revisiting features in Phase 3.")


if __name__ == "__main__":
    run_phase5()
