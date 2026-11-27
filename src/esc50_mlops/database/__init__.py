"""Data acquisition and loading for ESC-50 (TDSP stage: data acquisition and understanding)."""

from esc50_mlops.database.acquisition import acquire, download_archive, extract_archive, sha256sum
from esc50_mlops.database.loading import (
    ValidationReport,
    class_names,
    fold_split,
    iter_clips,
    load_clip,
    load_metadata,
    summarize,
    validate_dataset,
)

__all__ = [
    "ValidationReport",
    "acquire",
    "class_names",
    "download_archive",
    "extract_archive",
    "fold_split",
    "iter_clips",
    "load_clip",
    "load_metadata",
    "sha256sum",
    "summarize",
    "validate_dataset",
]
