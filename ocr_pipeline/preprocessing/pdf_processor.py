"""
PDF Processor.
Converts PDF documents into high-resolution RGB image arrays for OCR processing using PyMuPDF.
"""

import os
import logging
from typing import List, Tuple, Union
import numpy as np
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, target_dpi: int = 300, max_dimension: int = 2500):
        self.target_dpi = target_dpi
        self.max_dimension = max_dimension

    def pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """
        Convert all pages of a PDF into high-res RGB numpy arrays.

        Args:
            pdf_path: Absolute or relative path to the PDF file.

        Returns:
            List of numpy ndarray (H, W, 3) in RGB format, one per page.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Opening PDF for rasterization: {pdf_path} (target DPI: {self.target_dpi})")
        doc = fitz.open(pdf_path)
        images = []

        try:
            # 72 is standard PDF default points per inch
            zoom = self.target_dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                # Convert pixmap to numpy array (RGB)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, 3))

                # If dimensions exceed max_dimension, downsample proportionally
                h, w = img.shape[:2]
                max_dim = max(h, w)
                if max_dim > self.max_dimension:
                    scale = self.max_dimension / float(max_dim)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    pil_img = Image.fromarray(img)
                    img = np.array(pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS))

                images.append(img)
                logger.info(f"Rendered Page {page_num + 1}/{len(doc)}: shape={img.shape}")

        finally:
            doc.close()

        return images

    def load_document(self, input_path: str) -> List[np.ndarray]:
        """
        Loads document as a list of RGB images.
        Supports both image files (.png, .jpg, .jpeg, etc.) and PDF files.
        """
        ext = os.path.splitext(input_path)[1].lower()
        if ext == ".pdf":
            return self.pdf_to_images(input_path)

        # Direct image file
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Image file not found: {input_path}")

        pil_img = Image.open(input_path).convert("RGB")
        img = np.array(pil_img)
        return [img]
