"""Offline tests for ESC-50 acquisition and loading.

They build a tiny synthetic copy of the ESC-50 layout (no download needed), so
they run in CI and on any laptop in a few seconds.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from esc50_mlops import config
from esc50_mlops.database import (
    acquire,
    class_names,
    extract_archive,
    fold_split,
    load_clip,
    load_metadata,
    sha256sum,
    validate_dataset,
)
from esc50_mlops.database.acquisition import ChecksumError

# 2 classes x 5 folds x 1 clip = 10 clips, each 0.01 s of noise.
N_FRAMES = 441
SMALL = {"expected_clips": 10, "expected_classes": 2, "expected_per_class": 5,
         "expected_per_fold": 2, "expected_esc10_classes": 1}


def _make_dataset(root: Path) -> Path:
    ds = root / "ESC-50-deadbeef"
    (ds / "audio").mkdir(parents=True)
    (ds / "meta").mkdir()
    rng = np.random.default_rng(0)
    rows = []
    for target, category in [(0, "dog"), (1, "rooster")]:
        for fold in range(1, 6):
            src = f"{100 + 10 * target + fold}"
            fn = f"{fold}-{src}-A-{target}.wav"
            sf.write(ds / "audio" / fn, rng.uniform(-0.5, 0.5, N_FRAMES).astype("float32"), 44_100)
            rows.append({"filename": fn, "fold": fold, "target": target, "category": category,
                         "esc10": target == 0, "src_file": src, "take": "A"})
    pd.DataFrame(rows).to_csv(ds / "meta" / "esc50.csv", index=False)
    return ds


@pytest.fixture()
def dataset(tmp_path: Path) -> Path:
    ds = _make_dataset(tmp_path / "src")
    final = tmp_path / "raw" / config.DATASET_DIRNAME
    final.parent.mkdir()
    ds.rename(final)
    return final


@pytest.fixture()
def archive(tmp_path: Path) -> Path:
    ds = _make_dataset(tmp_path / "build")
    zpath = tmp_path / "esc50.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for p in ds.rglob("*"):
            zf.write(p, p.relative_to(ds.parent))
    return zpath


# --------------------------------------------------------------------------- acquisition
def test_sha256sum_matches_hashlib(tmp_path: Path) -> None:
    f = tmp_path / "x.bin"
    f.write_bytes(b"esc50" * 1000)
    assert sha256sum(f) == hashlib.sha256(b"esc50" * 1000).hexdigest()


def test_extract_normalises_top_folder_and_is_idempotent(archive: Path, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    out = extract_archive(archive, raw)
    assert out == raw / config.DATASET_DIRNAME
    assert (out / "meta" / "esc50.csv").exists()
    marker = out / "marker"
    marker.touch()
    assert extract_archive(archive, raw) == out and marker.exists()  # reused, not re-extracted
    assert not list(raw.glob(".extract-*"))  # temp folder cleaned


def test_extract_rejects_zip_slip(tmp_path: Path) -> None:
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("../evil.txt", "x")
    with pytest.raises(RuntimeError, match="Unsafe path"):
        extract_archive(bad, tmp_path / "raw")


def test_acquire_with_local_archive_checks_hash(archive: Path, tmp_path: Path) -> None:
    with pytest.raises(ChecksumError):
        acquire(raw_dir=tmp_path / "raw", archive=archive, expected_sha256="0" * 64)
    out = acquire(raw_dir=tmp_path / "raw", archive=archive, expected_sha256=sha256sum(archive))
    assert (out / "audio").is_dir()


# --------------------------------------------------------------------------- loading
def test_load_metadata_types_and_paths(dataset: Path) -> None:
    df = load_metadata(dataset)
    assert len(df) == 10
    assert set(config.METADATA_COLUMNS) <= set(df.columns)
    assert df["fold"].dtype == "int8" and df["esc10"].dtype == bool
    assert all(Path(p).exists() for p in df["path"])
    assert class_names(df) == ["dog", "rooster"]
    assert df["major_category"].iloc[0] == "Animals"


def test_load_metadata_missing_csv(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="data_acquisition"):
        load_metadata(tmp_path)


def test_load_clip_returns_float_mono(dataset: Path) -> None:
    y, sr = load_clip(next((dataset / "audio").glob("*.wav")))
    assert sr == 44_100 and y.dtype == np.float32 and y.shape == (N_FRAMES,)
    assert -1.0 <= y.min() and y.max() <= 1.0


def test_fold_split_is_disjoint_and_complete(dataset: Path) -> None:
    df = load_metadata(dataset)
    s = fold_split(df)
    assert sum(len(v) for v in s.values()) == len(df)
    assert set(s["train"]["fold"]) == {1, 2, 3} and set(s["test"]["fold"]) == {5}
    with pytest.raises(ValueError, match="overlap"):
        fold_split(df, train_folds=(1, 2), val_folds=(2,))


# --------------------------------------------------------------------------- validation
def test_validation_passes_on_clean_data(dataset: Path) -> None:
    rep = validate_dataset(load_metadata(dataset), dataset, check_audio=False, **SMALL)
    assert rep.passed, str(rep)
    assert not rep.warnings


def test_validation_detects_wrong_audio_format(dataset: Path) -> None:
    # Clips are 0.01 s instead of 5 s, so the format check must fail.
    rep = validate_dataset(load_metadata(dataset), dataset, check_audio=True, **SMALL)
    assert not rep.passed
    assert [c.name for c in rep.checks if not c.passed] == ["audio format 44100 Hz / mono / 5 s"]


def test_validation_detects_missing_file_and_label_mismatch(dataset: Path) -> None:
    df = load_metadata(dataset)
    Path(df.loc[0, "path"]).unlink()
    df.loc[1, "target"] = 1  # filename says class 0
    rep = validate_dataset(df, dataset, check_audio=False, **SMALL)
    failed = {c.name for c in rep.checks if not c.passed}
    assert {"all audio files exist", "filename matches fold/target/take"} <= failed


def test_validation_flags_leakage(dataset: Path) -> None:
    df = load_metadata(dataset)
    # Same class, same source file in two folds -> error.
    df.loc[df["target"] == 0, "src_file"] = "999"
    rep = validate_dataset(df, dataset, check_audio=False, **SMALL)
    assert not rep.passed


def test_cross_class_source_reuse_is_only_a_warning(dataset: Path) -> None:
    df = load_metadata(dataset)
    # One recording used by two different classes in different folds (as in real ESC-50).
    df.loc[(df["target"] == 0) & (df["fold"] == 1), "src_file"] = "777"
    df.loc[(df["target"] == 1) & (df["fold"] == 2), "src_file"] = "777"
    rep = validate_dataset(df, dataset, check_audio=False, **SMALL)
    assert rep.passed and len(rep.warnings) == 1 and "777" in rep.warnings[0].detail
