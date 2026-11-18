"""Shared utilities for the Mobile Computing Assignment 2 simulations."""
from __future__ import annotations
import csv
import random
from pathlib import Path
from typing import Iterable, Sequence

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

def ensure_directories() -> None:
    """Create the standard data and output directories when needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def seed_random(seed: int = 42) -> None:
    """Set Python's random seed for reproducible experiments."""
    random.seed(seed)

def save_csv(path: str | Path, header: Sequence[object],
             rows: Iterable[Sequence[object]]) -> Path:
    """Write a CSV file with a header and rows; return its path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)
    return destination

def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a CSV file as a list of dictionaries."""
    with Path(path).open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))
