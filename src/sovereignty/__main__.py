from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .packet import validate_packet_dict
from .policy import SovereigntyPolicyError
from .redaction import redact_model_metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sovereignty")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a review packet JSON file")
    validate_parser.add_argument("path", help="Path to packet JSON")

    redact_parser = subparsers.add_parser("redact", help="Redact model metadata JSON")
    redact_parser.add_argument("path", help="Path to metadata JSON")

    args = parser.parse_args(argv)

    try:
        data = _read_json(args.path)
        if args.command == "validate":
            packet = validate_packet_dict(data)
            _print_json({"ok": True, "packet": packet.to_dict()})
            return 0
        if args.command == "redact":
            _print_json(redact_model_metadata(data))
            return 0
    except (OSError, json.JSONDecodeError, SovereigntyPolicyError, TypeError) as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 1

    _print_json({"ok": False, "error": f"unsupported command: {args.command}"})
    return 1


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text())


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
