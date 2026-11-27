"""Acquire, load and validate the raw ESC-50 dataset (data version v1).

Usage (from the repository root, inside the project environment):

    python scripts/data_acquisition/main.py                 # download + extract + validate
    python scripts/data_acquisition/main.py --archive x.zip # reuse a local copy of the archive
    python scripts/data_acquisition/main.py --skip-audio-check

Outputs:
    data/raw/ESC-50-master/            extracted dataset (DVC-tracked, not in Git)
    reports/data_acquisition.json      provenance, summary and validation results

Exit code is 1 if any validation check fails.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from care_sound_monitor import config
from care_sound_monitor.database import acquire, load_metadata, summarize, validate_dataset


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--raw-dir", type=Path, default=config.RAW_DIR,
                   help="Destination of the extracted dataset (default: %(default)s)")
    p.add_argument("--download-dir", type=Path, default=config.DOWNLOAD_DIR,
                   help="Cache folder for the downloaded archive (default: %(default)s)")
    p.add_argument("--archive", type=Path, default=None,
                   help="Use an already downloaded archive instead of downloading")
    p.add_argument("--force", action="store_true", help="Download and extract again")
    p.add_argument("--skip-audio-check", action="store_true",
                   help="Skip reading the header of each WAV file")
    p.add_argument("--report", type=Path, default=config.PROJECT_ROOT / "reports" / "data_acquisition.json",
                   help="Where to write the JSON report (default: %(default)s)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("data_acquisition")
    args = parse_args(argv)

    dataset_dir = acquire(raw_dir=args.raw_dir, download_dir=args.download_dir,
                          archive=args.archive, force=args.force)

    df = load_metadata(dataset_dir)
    log.info("Loaded metadata: %d rows x %d columns", *df.shape)

    report = validate_dataset(df, dataset_dir, check_audio=not args.skip_audio_check)
    print(report)

    summary = summarize(df)
    log.info("Clips per fold: %s", summary["clips_per_fold"])
    log.info("Clips per major category: %s", summary["clips_per_major_category"])

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"repo": config.SOURCE_REPO, "commit": config.SOURCE_COMMIT,
                   "url": config.SOURCE_URL, "sha256": config.SOURCE_SHA256},
        "dataset_dir": str(dataset_dir.relative_to(config.PROJECT_ROOT)
                           if dataset_dir.is_relative_to(config.PROJECT_ROOT) else dataset_dir),
        "summary": summary,
        "validation": report.to_dict(),
    }, indent=2, ensure_ascii=False) + "\n")
    log.info("Report written to %s", args.report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
