from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database.connection import DB_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"


def create_backup(
    source_path: Path = DB_PATH,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    keep: int = 14,
) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(
            f"База данных не найдена: {source_path}"
        )

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d-%H%M%S")

    target = backup_dir / f"eden-{stamp}.db"

    source = sqlite3.connect(
        source_path
    )
    destination = sqlite3.connect(
        target
    )

    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    backups = sorted(
        backup_dir.glob("eden-*.db"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[max(1, keep):]:
        old_backup.unlink(
            missing_ok=True
        )

    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Создать безопасную копию data/eden.db",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=14,
        help="Сколько последних копий хранить",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Каталог для резервных копий",
    )

    args = parser.parse_args()

    target = create_backup(
        backup_dir=args.directory,
        keep=args.keep,
    )

    print(f"Backup created: {target}")


if __name__ == "__main__":
    main()
