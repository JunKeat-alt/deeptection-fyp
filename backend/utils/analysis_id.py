"""
Generate short, human-readable Analysis IDs.

Format:  XXXX-XXXX  (8 alphanumeric chars, dashed in the middle)
Example: A7F3-92KD

We use a 32-character alphabet that excludes visually ambiguous
characters (0/O, 1/I/L) so users can copy-paste or read aloud
without errors. 8 characters from this alphabet give ~10^12
combinations — collision-resistant for an FYP demo and beyond.
"""

from __future__ import annotations

import secrets

# Crockford-style alphabet (no 0/O/1/I/L)
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_analysis_id() -> str:
    """Return a fresh ID like 'A7F3-92KD'."""
    chars = [secrets.choice(_ALPHABET) for _ in range(8)]
    return f"{''.join(chars[:4])}-{''.join(chars[4:])}"