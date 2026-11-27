"""Loading and integrity validation of the raw ESC-50 dataset.

``load_metadata`` returns the clip-level table (one row per WAV file) with
typed columns and absolute paths. ``validate_dataset`` checks it against the
contract published in the ESC-50 README, so later phases can trust the data.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

from esc50_mlops import config


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
def load_metadata(dataset_dir: Path = config.DATASET_DIR) -> pd.DataFrame:
    """Read ``meta/esc50.csv`` into a typed DataFrame.

    Added columns:
      * ``clip_id``: Freesound clip ID parsed from the filename.
      * ``major_category``: one of the five README groups (``target // 10``).
      * ``path``: absolute path of the WAV file.
    """
    dataset_dir = Path(dataset_dir)
    csv = dataset_dir / config.METADATA_RELPATH
    if not csv.exists():
        raise FileNotFoundError(
            f"{csv} not found. Run `python scripts/data_acquisition/main.py` first."
        )
    df = pd.read_csv(
        csv,
        dtype={"filename": "string", "fold": "int8", "target": "int8",
               "category": "string", "esc10": "bool", "src_file": "string",
               "take": "string"},
    )
    missing = set(config.METADATA_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {csv}: {sorted(missing)}")

    df["clip_id"] = df["filename"].str.split("-").str[1].astype("string")
    df["major_category"] = pd.Categorical(
        (df["target"] // 10).map(config.MAJOR_CATEGORIES),
        categories=list(config.MAJOR_CATEGORIES.values()),
    )
    df["category"] = df["category"].astype("category")
    df["path"] = [str(dataset_dir / config.AUDIO_RELDIR / f) for f in df["filename"]]
    return df


def class_names(df: pd.DataFrame) -> list[str]:
    """Class names ordered by ``target`` (index ``i`` is the name of class ``i``)."""
    return (df[["target", "category"]].drop_duplicates()
            .sort_values("target")["category"].astype(str).tolist())


def fold_split(
    df: pd.DataFrame,
    train_folds: Sequence[int] = (1, 2, 3),
    val_folds: Sequence[int] = (4,),
    test_folds: Sequence[int] = (5,),
) -> dict[str, pd.DataFrame]:
    """Split by the predefined folds (never randomly: avoids source-file leakage)."""
    groups = {"train": set(train_folds), "val": set(val_folds), "test": set(test_folds)}
    names = list(groups)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if groups[a] & groups[b]:
                raise ValueError(f"Folds overlap between {a} and {b}: {groups[a] & groups[b]}")
    return {k: df[df["fold"].isin(v)].reset_index(drop=True) for k, v in groups.items()}


# --------------------------------------------------------------------------- #
# Audio
# --------------------------------------------------------------------------- #
def load_clip(path: str | Path) -> tuple[np.ndarray, int]:
    """Read one WAV file as ``float32`` in [-1, 1]. Returns ``(waveform, sample_rate)``.

    Mono files give shape ``(n_samples,)``. No resampling: that belongs to preprocessing.
    """
    y, sr = sf.read(str(path), dtype="float32", always_2d=False)
    return y, sr


def iter_clips(df: pd.DataFrame) -> Iterator[tuple[pd.Series, np.ndarray, int]]:
    """Yield ``(row, waveform, sample_rate)`` for every row of ``df``."""
    for _, row in df.iterrows():
        y, sr = load_clip(row["path"])
        yield row, y, sr


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""
    #: ``"error"`` fails the validation; ``"warning"`` is a documented, accepted dataset quirk.
    severity: str = "error"


@dataclass
class ValidationReport:
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True when no check of severity ``error`` failed (warnings do not fail)."""
        return all(c.passed for c in self.checks if c.severity == "error")

    @property
    def warnings(self) -> list[Check]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    def add(self, name: str, passed: bool, detail: str = "", severity: str = "error") -> None:
        self.checks.append(Check(name, bool(passed), str(detail), severity))

    def to_dict(self) -> dict:
        return {"passed": self.passed, "n_warnings": len(self.warnings),
                "checks": [c.__dict__ for c in self.checks]}

    def __str__(self) -> str:
        def tag(c: Check) -> str:
            return "PASS" if c.passed else ("WARN" if c.severity == "warning" else "FAIL")
        lines = [f"[{tag(c)}] {c.name}" + (f" - {c.detail}" if c.detail else "") for c in self.checks]
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'} "
                     f"({sum(c.passed for c in self.checks)}/{len(self.checks)} checks passed, "
                     f"{len(self.warnings)} warning(s))")
        return "\n".join(lines)


def validate_dataset(
    df: pd.DataFrame,
    dataset_dir: Path = config.DATASET_DIR,
    check_audio: bool = True,
    expected_clips: int = config.N_CLIPS,
    expected_classes: int = config.N_CLASSES,
    expected_per_class: int = config.CLIPS_PER_CLASS,
    expected_per_fold: int = config.CLIPS_PER_FOLD,
    expected_esc10_classes: int = config.N_ESC10_CLASSES,
) -> ValidationReport:
    """Check the metadata and the audio files against the ESC-50 contract.

    The ``expected_*`` arguments exist so tests can run on a tiny synthetic copy.
    """
    r = ValidationReport()
    dataset_dir = Path(dataset_dir)

    # Table-level checks
    r.add("row count", len(df) == expected_clips, f"{len(df)} rows (expected {expected_clips})")
    r.add("no missing values", not df[list(config.METADATA_COLUMNS)].isna().any().any())
    r.add("unique filenames", df["filename"].is_unique)

    per_class = df.groupby("target").size()
    r.add("class count", per_class.size == expected_classes, f"{per_class.size} classes")
    r.add("balanced classes", (per_class == expected_per_class).all(),
          f"clips per class: min {per_class.min()}, max {per_class.max()}")

    t2c = df.groupby("target")["category"].nunique()
    c2t = df.groupby("category", observed=True)["target"].nunique()
    r.add("target <-> category is 1:1", (t2c == 1).all() and (c2t == 1).all())

    per_fold = df.groupby("fold").size()
    r.add("fold sizes", set(per_fold.index) == set(range(1, config.N_FOLDS + 1))
          and (per_fold == expected_per_fold).all(),
          {int(k): int(v) for k, v in per_fold.items()})

    pattern = re.compile(config.FILENAME_REGEX)
    parsed = df["filename"].astype(str).str.extract(pattern)
    ok_name = (parsed.notna().all(axis=1)
               & (parsed["fold"].astype(float) == df["fold"])
               & (parsed["target"].astype(float) == df["target"])
               & (parsed["take"] == df["take"]))
    r.add("filename matches fold/target/take", ok_name.all(),
          f"{int((~ok_name).sum())} mismatches")

    # Leakage guard: fragments of one Freesound recording must share a fold.
    # Within a class this must hold (error). Across classes, ESC-50 has a few known
    # exceptions (same recording labelled e.g. hen and rooster), reported as a warning.
    folds_per_src_class = df.groupby(["src_file", "target"])["fold"].nunique()
    r.add("each src_file in a single fold within its class", (folds_per_src_class == 1).all(),
          f"{int((folds_per_src_class > 1).sum())} (src_file, class) pairs span several folds")
    folds_per_src = df.groupby("src_file")["fold"].nunique()
    shared = sorted(folds_per_src[folds_per_src > 1].index.astype(str))
    r.add("each src_file in a single fold across classes", not shared,
          f"{len(shared)} source files reused by two classes in different folds: {shared}",
          severity="warning")

    esc10_classes = df.loc[df["esc10"], "target"].nunique()
    esc10_pure = df.groupby("target")["esc10"].nunique().eq(1).all()
    r.add("ESC-10 subset is 10 whole classes",
          esc10_pure and esc10_classes == expected_esc10_classes,
          f"{esc10_classes} classes, {int(df['esc10'].sum())} clips")

    # File-level checks
    paths = df["path"].map(Path)
    missing = [p.name for p in paths if not p.exists()]
    r.add("all audio files exist", not missing, f"{len(missing)} missing" + (f": {missing[:3]}" if missing else ""))
    on_disk = {p.name for p in (dataset_dir / config.AUDIO_RELDIR).glob("*.wav")}
    extra = sorted(on_disk - set(df["filename"]))
    r.add("no unlisted audio files", not extra, f"{len(extra)} extra")

    if check_audio and not missing:
        bad_fmt, bad_signal = [], []
        for p in paths:
            info = sf.info(str(p))
            if (info.samplerate, info.channels, info.frames) != (
                    config.SAMPLE_RATE, config.N_CHANNELS, config.CLIP_FRAMES):
                bad_fmt.append(f"{p.name}: {info.samplerate} Hz, {info.channels} ch, {info.frames} frames")
            # Same content checks as the upstream ESC-50 test-suite: decodable,
            # non-constant signal and a small DC offset.
            y, _ = load_clip(p)
            if not (y.max() > 0 and y.min() < 0 and abs(float(y.mean())) < 0.2):
                bad_signal.append(p.name)
        r.add(f"audio format {config.SAMPLE_RATE} Hz / mono / {config.CLIP_SECONDS:g} s",
              not bad_fmt, f"{len(bad_fmt)} non-conforming" + (f": {bad_fmt[:3]}" if bad_fmt else ""))
        r.add("audio content (decodable, not silent, |DC offset| < 0.2)",
              not bad_signal, f"{len(bad_signal)} suspicious" + (f": {bad_signal[:3]}" if bad_signal else ""))
    return r


def summarize(df: pd.DataFrame) -> dict:
    """Small, JSON-serialisable description of the loaded dataset."""
    return {
        "n_clips": len(df),
        "n_classes": int(df["target"].nunique()),
        "n_source_files": int(df["src_file"].nunique()),
        "clips_per_fold": {int(k): int(v) for k, v in df.groupby("fold").size().items()},
        "clips_per_major_category": {str(k): int(v) for k, v in
                                     df.groupby("major_category", observed=True).size().items()},
        "esc10_clips": int(df["esc10"].sum()),
        "takes": {str(k): int(v) for k, v in df["take"].value_counts().sort_index().items()},
        "class_names": class_names(df),
    }
