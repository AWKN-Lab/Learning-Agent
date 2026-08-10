from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.store import Store  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete expired Learning-Agent demo sessions safely."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report candidates without deleting them.",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=None,
        help="Keep at most this many newest sessions after expired cleanup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_sessions is not None and args.max_sessions < 0:
        raise SystemExit("--max-sessions must be >= 0")

    result = Store().cleanup_sessions(
        max_sessions=args.max_sessions,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
