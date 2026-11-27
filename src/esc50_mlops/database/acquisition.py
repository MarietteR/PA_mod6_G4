"""Acquisition of the raw ESC-50 dataset.

Downloads the archive of a pinned upstream commit, verifies its SHA-256 and
extracts it to ``data/raw/ESC-50-master``. Every step is idempotent: if the
verified archive or the extracted folder already exist, they are reused.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from esc50_mlops import config

log = logging.getLogger(__name__)

_CHUNK = 1 << 20  # 1 MiB


class ChecksumError(RuntimeError):
    """Raised when a downloaded archive does not match the expected SHA-256."""


def sha256sum(path: Path) -> str:
    """Return the hex SHA-256 digest of ``path``, read in 1 MiB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def download_archive(
    url: str = config.SOURCE_URL,
    dest: Path = config.DOWNLOAD_DIR / config.ARCHIVE_NAME,
    expected_sha256: str | None = config.SOURCE_SHA256,
    force: bool = False,
) -> Path:
    """Download ``url`` to ``dest`` and verify its checksum.

    The file is written to a temporary name and renamed only after the checksum
    matches, so an interrupted download never leaves a corrupt archive behind.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        if expected_sha256 is None or sha256sum(dest) == expected_sha256:
            log.info("Archive already present and verified: %s", dest)
            return dest
        log.warning("Cached archive has a wrong checksum, downloading again: %s", dest)

    tmp = dest.with_suffix(dest.suffix + ".part")
    log.info("Downloading %s", url)
    h = hashlib.sha256()
    done, next_report = 0, 50 * _CHUNK
    with urllib.request.urlopen(url) as resp, open(tmp, "wb") as out:  # fixed https URL from config
        for chunk in iter(lambda: resp.read(_CHUNK), b""):
            out.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if done >= next_report:
                log.info("  %.0f MB downloaded", done / 1e6)
                next_report += 50 * _CHUNK

    digest = h.hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        tmp.unlink(missing_ok=True)
        raise ChecksumError(f"SHA-256 mismatch for {url}: got {digest}, expected {expected_sha256}")
    tmp.replace(dest)
    log.info("Downloaded %.1f MB, SHA-256 %s", done / 1e6, digest)
    return dest


def _safe_extract(zf: zipfile.ZipFile, target: Path) -> None:
    """Extract ``zf`` into ``target`` refusing members that escape it (zip-slip)."""
    root = target.resolve()
    for member in zf.infolist():
        dest = (target / member.filename).resolve()
        if not dest.is_relative_to(root):
            raise RuntimeError(f"Unsafe path in archive: {member.filename}")
    zf.extractall(target)


def extract_archive(
    archive: Path,
    raw_dir: Path = config.RAW_DIR,
    dirname: str = config.DATASET_DIRNAME,
    force: bool = False,
) -> Path:
    """Extract ``archive`` and normalise its top folder to ``raw_dir / dirname``.

    GitHub archives contain a single top folder named ``ESC-50-<ref>``; it is
    renamed so downstream code never depends on the commit hash.
    """
    raw_dir = Path(raw_dir)
    final = raw_dir / dirname
    if final.exists():
        if not force:
            log.info("Dataset already extracted: %s", final)
            return final
        shutil.rmtree(final)

    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=raw_dir, prefix=".extract-") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(archive) as zf:
            _safe_extract(zf, tmp_path)
        tops = [p for p in tmp_path.iterdir() if p.is_dir()]
        if len(tops) != 1:
            raise RuntimeError(f"Expected one top-level folder in {archive}, found {len(tops)}")
        tops[0].rename(final)
    log.info("Extracted to %s", final)
    return final


def acquire(
    raw_dir: Path = config.RAW_DIR,
    download_dir: Path = config.DOWNLOAD_DIR,
    url: str = config.SOURCE_URL,
    expected_sha256: str | None = config.SOURCE_SHA256,
    archive: Path | None = None,
    force: bool = False,
) -> Path:
    """Download (or reuse ``archive``) and extract ESC-50. Returns the dataset folder."""
    if archive is None:
        archive = download_archive(url, Path(download_dir) / config.ARCHIVE_NAME,
                                   expected_sha256, force=force)
    elif expected_sha256 is not None and sha256sum(archive) != expected_sha256:
        raise ChecksumError(f"Provided archive {archive} does not match the pinned SHA-256")
    return extract_archive(archive, raw_dir, force=force)
