"""Command-line entry points for the recommendation project."""

import argparse
import csv
import json
import sys
from importlib.resources import files
from pathlib import Path

from recsys.data import profile_ratings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recsys", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    profile = commands.add_parser("profile", help="Validate and summarize ratings CSV")
    source = profile.add_mutually_exclusive_group(required=True)
    source.add_argument("--ratings", type=Path, help="Path to MovieLens ratings.csv")
    source.add_argument("--sample", action="store_true", help="Use synthetic bundled data")
    profile.add_argument("--output", type=Path, help="Also save the JSON report")
    args = parser.parse_args(argv)
    try:
        if args.sample:
            resource = files("recsys").joinpath("fixtures/ratings.csv")
            with resource.open("r", encoding="utf-8", newline="") as stream:
                report = profile_ratings(stream)
            report["source"] = "bundled-synthetic-sample"
        else:
            if args.output and args.output.resolve() == args.ratings.resolve():
                raise ValueError("Output must not overwrite the ratings input")
            with args.ratings.open("r", encoding="utf-8-sig", newline="") as stream:
                report = profile_ratings(stream)
            report["source"] = str(args.ratings)
        payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"recsys: {exc}", file=sys.stderr)
        return 2
