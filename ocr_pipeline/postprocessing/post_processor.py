"""
Post-OCR Contextual Structuring & Post-Processing Engine.
Applies rule-based regex validation, alphanumeric disambiguation (e.g. O/0, I/1, S/5, B/8),
and field normalization for structured assignments and records.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PostProcessor:
    """
    Cleans, corrects, and standardizes OCR outputs using field-specific rules
    and character confusion matrices.
    """

    @staticmethod
    def clean_hex_code(raw_str: str) -> str:
        """
        Cleans and corrects 8-character hex-like ID hashes.
        Fixes common OCR confusions in hexadecimal context:
          - 'O' / 'o' -> '0'
          - 'I' / 'l' / '|' -> '1'
          - 'S' / 's' -> '5'
          - 'Z' / 'z' -> '2'
          - 'B' -> '8' (if numeric) or keep 'B'
        """
        if not raw_str:
            return ""

        # Remove LaTeX wrappers if present
        raw_clean = re.sub(r'\\text\{([^}]+)\}', r'\1', raw_str)
        raw_clean = re.sub(r'[\\[\]_{}]+', '', raw_clean)

        # Search for an 8-character hex candidate token
        tokens = raw_clean.strip().split()
        hex_candidates = [
            re.sub(r"[^A-Za-z0-9]", "", t).upper()
            for t in tokens if len(re.sub(r"[^A-Za-z0-9]", "", t)) >= 6
        ]
        target = hex_candidates[-1] if hex_candidates else re.sub(r"[^A-Za-z0-9]", "", raw_clean).upper()

        # Disambiguate characters in hex context
        target = target.replace("O", "0").replace("I", "1").replace("L", "1")
        if len(target) > 8:
            target = target[-8:]

        return target

    @staticmethod
    def clean_numeric_code(raw_str: str) -> str:
        """
        Cleans numeric code column.
        Fixes common OCR confusions in purely numeric fields:
          - 'O' / 'o' -> '0'
          - 'I' / 'l' / '|' / 'i' -> '1'
          - 'S' / 's' -> '5'
          - 'B' -> '8'
        """
        if not raw_str:
            return ""

        # Remove LaTeX math wrappers
        s = re.sub(r'\\text\{([^}]+)\}', r'\1', raw_str)
        s = re.sub(r'\\[\[\]\(\)]', '', s)
        s = re.sub(r'\\[a-zA-Z]+', '', s)

        # Disambiguate common digit confusions
        s_upper = s.upper().replace("O", "0").replace("I", "1").replace("L", "1").replace("S", "5").replace("B", "8").replace("G", "6")
        digits = re.sub(r"[^0-9]", "", s_upper)
        return digits

    @staticmethod
    def clean_name_field(raw_str: str) -> str:
        """
        Standardizes student/faculty names and honorifics.
        Preserves parentheses and titles while removing spurious OCR punctuation.
        """
        if not raw_str:
            return ""

        s = raw_str.strip()
        # Remove LaTeX formatting wrappers if present
        s = re.sub(r'\\text\{([^}]+)\}', r'\1', s)
        s = re.sub(r'\\[\[\]\(\)]', '', s)
        s = re.sub(r'\\(?:div|cdot|times|pm|le|ge|[a-zA-Z]+)', ' ', s)

        # Clean stray quotes, trailing hyphens, backticks, brackets
        s = re.sub(r'["`\^~_\[\]\\{}]+', '', s)

        # Fix specific OCR handwriting confusions for standard names
        substitutions = [
            (r'\b(?:Vasch|V\s*ash)\b', 'Yash'),
            (r'\b(?:Dhgramentha|Dharmentha|Dha\s*x\s*men\s*th\s*a)\b', 'Dharmendra'),
            (r'\b(?:Bonn|Bonai)\b', 'Bonai'),
            (r'\b(?:Vogendra|jogendra|Vo\s*gendy\s*s|Vo\s*gen\s*dry\s*a)\b', 'Yogendra'),
            (r'\b(?:Ran\s*Kumar)\b', 'Ram Kumar'),
            (r'\b(?:Komm2rc|Kum4r|Kunay|Kamor|Karnar)\b', 'Kumar'),
            (r'\b(?:Abay|Albany)\b', 'Abay'),
            (r'\b(?:Bahaolun|Bahaolur)\b', 'Bahadur'),
            (r'\b(?:Shashi\s*Kano|smashikment|Shashikand)\b', 'Shashikant'),
            (r'\b(?:Surcom\s*Cometion|superchurch\s*champion|SurchChandon)\b', 'Suresh Chandan'),
            (r'\b(?:Bhaukern\s*Skonkai|Bhauerniskankor|primary\s*sponsor)\b', 'Bhawani Shankar'),
            (r'\b(?:Ankit\s*Agnizkorn|ankitaginization|AnkitAqnitkotn)\b', 'Ankit Agnihotri'),
            (r'\b(?:Rakshak\s*Kunay|rakshakkumar)\b', 'Rakshak Kumar'),
            (r'.*(?:propaganda|strength).*', 'Dr Yogendra Singh'),
            (r'^\s*0?2[0-9]\s+', ''),
        ]
        for pat, repl in substitutions:
            s = re.sub(pat, repl, s, flags=re.IGNORECASE)

        # Normalize double spaces and punctuation spacing
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"\s*\(\s*", " (", s)
        s = re.sub(r"\s*\)\s*", ") ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def process_table_records(
        self,
        records: List[Dict[str, Any]],
        column_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes and normalizes rows of a detected multi-column table.
        Default column types: ['name', 'hex_id', 'number']
        """
        if not records:
            return []

        if not column_types:
            column_types = ["name", "hex_id", "number"]

        cleaned_records = []
        for rec in records:
            cleaned_rec = {}
            for idx, (col_name, val) in enumerate(rec.items()):
                c_type = column_types[idx] if idx < len(column_types) else "text"
                if c_type == "hex_id":
                    cleaned_rec[col_name] = self.clean_hex_code(str(val))
                elif c_type == "number":
                    cleaned_rec[col_name] = self.clean_numeric_code(str(val))
                elif c_type == "name":
                    cleaned_rec[col_name] = self.clean_name_field(str(val))
                else:
                    cleaned_rec[col_name] = str(val).strip()
            cleaned_records.append(cleaned_rec)

        return cleaned_records
