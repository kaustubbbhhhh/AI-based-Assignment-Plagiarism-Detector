"""
Fine-Tune TrOCR (microsoft/trocr-base-handwritten) on Student Handwritten Dataset
================================================================================
Optimized for RTX 2050 GPU / CUDA acceleration with mixed precision (FP16).
Trains on line crops and ground truth text in backend/ocr_dataset/.
Saves fine-tuned model weights to: backend/models/trocr_finetuned/
"""

import os
import sys
import shutil
import torch
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator
)
import jiwer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "ocr_dataset")
CSV_PATH = os.path.join(DATASET_DIR, "metadata.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "models", "trocr_finetuned")


class HandwrittenDataset(Dataset):
    def __init__(self, df, root_dir, processor, max_target_length=128):
        self.df = df.reset_index(drop=True)
        self.root_dir = root_dir
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        file_name = row["file_name"]
        text = str(row["text"]).strip()

        image_path = os.path.join(self.root_dir, file_name)
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (384, 384), (255, 255, 255))

        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze(0)

        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True
        ).input_ids

        # Set -100 for padding tokens so PyTorch CrossEntropyLoss ignores them
        labels = [label if label != self.processor.tokenizer.pad_token_id else -100 for label in labels]

        return {
            "pixel_values": pixel_values,
            "labels": torch.tensor(labels, dtype=torch.long)
        }


def run_training(epochs=5, batch_size=2, lr=3e-5, max_samples=None):
    print("=" * 60, flush=True)
    print("Continuing TrOCR Fine-Tuning Pipeline", flush=True)
    print("=" * 60, flush=True)

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] metadata.csv not found at: {CSV_PATH}", flush=True)
        print("Please run `python prepare_ocr_dataset.py` first to generate training data.", flush=True)
        return

    df = pd.read_csv(CSV_PATH)
    # Filter out empty or very short noise
    df = df[df["text"].astype(str).str.strip().str.len() > 1].reset_index(drop=True)
    
    if max_samples and max_samples < len(df):
        print(f"Limiting dataset to {max_samples} samples for fast training.", flush=True)
        df = df.sample(n=max_samples, random_state=42).reset_index(drop=True)

    print(f"Total training samples loaded: {len(df)}", flush=True)

    if len(df) < 5:
        print("[ERROR] Not enough training samples. At least 5 line samples are required.", flush=True)
        return

    # Train / Val Split (85% train / 15% validation)
    train_df = df.sample(frac=0.85, random_state=42)
    val_df = df.drop(train_df.index)

    # Check if we already have trained weights in OUTPUT_DIR
    model_source = "microsoft/trocr-base-handwritten"
    if os.path.exists(os.path.join(OUTPUT_DIR, "model.safetensors")):
        print(f"\nResuming fine-tuning from our previously trained weights in: {OUTPUT_DIR}", flush=True)
        model_source = OUTPUT_DIR
    else:
        print(f"\nLoading base pre-trained model: {model_source}...", flush=True)

    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained(model_source)

    # Configure special tokens on model and generation_config
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    model.config.eos_token_id = processor.tokenizer.sep_token_id

    if hasattr(model, "generation_config") and model.generation_config is not None:
        model.generation_config.decoder_start_token_id = processor.tokenizer.cls_token_id
        model.generation_config.pad_token_id = processor.tokenizer.pad_token_id
        model.generation_config.eos_token_id = processor.tokenizer.sep_token_id
        model.generation_config.max_length = 64
        model.generation_config.early_stopping = True
        model.generation_config.no_repeat_ngram_size = 3
        model.generation_config.length_penalty = 2.0
        model.generation_config.num_beams = 4

    train_dataset = HandwrittenDataset(train_df, DATASET_DIR, processor)
    val_dataset = HandwrittenDataset(val_df, DATASET_DIR, processor)

    use_cuda = torch.cuda.is_available()
    device_name = f"GPU (CUDA: {torch.cuda.get_device_name(0)})" if use_cuda else "CPU"
    print(f"Training on device: {device_name}", flush=True)
    print(f"Train size: {len(train_dataset)}, Validation size: {len(val_dataset)}", flush=True)

    training_args = Seq2SeqTrainingArguments(
        predict_with_generate=False,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_only_model=True,  # Saves model.safetensors only; prevents Windows zipfile large optimizer error
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=2,
        fp16=use_cuda,
        learning_rate=lr,
        num_train_epochs=epochs,
        weight_decay=0.01,
        logging_steps=10,
        output_dir=OUTPUT_DIR,
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        report_to="none",
        dataloader_num_workers=0
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=default_data_collator,
    )

    # Clean intermediate subfolders to save disk space
    for sub in os.listdir(OUTPUT_DIR):
        subpath = os.path.join(OUTPUT_DIR, sub)
        if os.path.isdir(subpath) and sub.startswith("checkpoint-"):
            shutil.rmtree(subpath, ignore_errors=True)

    print("\nTraining in progress...", flush=True)
    trainer.train()

    print(f"\nSaving final fine-tuned model and processor to: {OUTPUT_DIR}...", flush=True)
    model.save_pretrained(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)
    print("=" * 60, flush=True)
    print("[SUCCESS] Fine-tuned TrOCR model saved successfully!", flush=True)
    print("=" * 60, flush=True)

    # Run quick sample predictions
    print("\nTesting sample predictions with fine-tuned model:", flush=True)
    model.eval()
    if use_cuda:
        model.to("cuda")

    for i in range(min(5, len(val_df))):
        sample_row = val_df.iloc[i]
        sample_img_path = os.path.join(DATASET_DIR, sample_row["file_name"])
        try:
            sample_img = Image.open(sample_img_path).convert("RGB")
            pixel_vals = processor(sample_img, return_tensors="pt").pixel_values
            if use_cuda:
                pixel_vals = pixel_vals.to("cuda")
            generated_ids = model.generate(pixel_vals)
            pred_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            print(f"  [Sample {i+1}] Source: {sample_row['source']}", flush=True)
            print(f"             Target: '{sample_row['text']}'", flush=True)
            print(f"             Pred:   '{pred_text}'\n", flush=True)
        except Exception as e:
            print(f"  Sample {i+1} test error: {e}", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fine-tune TrOCR on handwritten assignments")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs (default: 5)")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size per device (default: 2)")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate (default: 3e-5)")
    parser.add_argument("--max-samples", type=int, default=None, help="Max samples to train on")
    args = parser.parse_args()

    run_training(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, max_samples=args.max_samples)
