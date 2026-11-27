"""Project-wide constants for the ESC-50 MLOps project.

Everything that identifies *which* data we use lives here, so that the
acquisition script, the loaders and the tests agree on a single source of truth.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
#: Repository root (``src/esc50_mlops/config.py`` -> three levels up).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Raw, immutable data (DVC-tracked, never committed to Git).
RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"

#: Folder where the original archive is cached before extraction (Git-ignored).
DOWNLOAD_DIR: Path = PROJECT_ROOT / "data" / "external"

#: Name of the extracted dataset folder inside ``RAW_DIR`` (matches the proposal's dvc.yaml).
DATASET_DIRNAME: str = "ESC-50-master"

#: Default location of the extracted dataset.
DATASET_DIR: Path = RAW_DIR / DATASET_DIRNAME

# --------------------------------------------------------------------------- #
# Source (pinned for reproducibility)
# --------------------------------------------------------------------------- #
#: Upstream repository.
SOURCE_REPO: str = "https://github.com/karolpiczak/ESC-50"

#: Commit of ``karolpiczak/ESC-50`` that defines data version v1 (master as of 2023-10-13).
SOURCE_COMMIT: str = "33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6"

#: Archive URL for that exact commit (GitHub codeload, ~646 MB).
SOURCE_URL: str = f"https://codeload.github.com/karolpiczak/ESC-50/zip/{SOURCE_COMMIT}"

#: SHA-256 of the archive above, measured on 2026-11-26.
SOURCE_SHA256: str = "661183a6f53ef04f12c9bd618fed0ddc1713280d6c94a5a5431e844ba6f6a21f"

#: File name used for the cached archive.
ARCHIVE_NAME: str = f"ESC-50-{SOURCE_COMMIT[:7]}.zip"

# --------------------------------------------------------------------------- #
# Dataset contract (from the ESC-50 README; checked by ``validate_dataset``)
# --------------------------------------------------------------------------- #
METADATA_RELPATH: str = "meta/esc50.csv"
AUDIO_RELDIR: str = "audio"

METADATA_COLUMNS: tuple[str, ...] = (
    "filename", "fold", "target", "category", "esc10", "src_file", "take",
)

N_CLIPS: int = 2000
N_CLASSES: int = 50
CLIPS_PER_CLASS: int = 40
N_FOLDS: int = 5
CLIPS_PER_FOLD: int = 400
N_ESC10_CLASSES: int = 10

SAMPLE_RATE: int = 44_100
N_CHANNELS: int = 1
CLIP_SECONDS: float = 5.0
CLIP_FRAMES: int = int(SAMPLE_RATE * CLIP_SECONDS)  # 220,500 samples

#: Filename convention ``{FOLD}-{CLIP_ID}-{TAKE}-{TARGET}.wav``.
FILENAME_REGEX: str = r"^(?P<fold>[1-5])-(?P<clip_id>\d+)-(?P<take>[A-Z])-(?P<target>\d{1,2})\.wav$"

#: Major semantic categories (README), keyed by ``target // 10``.
MAJOR_CATEGORIES: dict[int, str] = {
    0: "Animals",
    1: "Natural soundscapes & water sounds",
    2: "Human, non-speech sounds",
    3: "Interior/domestic sounds",
    4: "Exterior/urban noises",
}
