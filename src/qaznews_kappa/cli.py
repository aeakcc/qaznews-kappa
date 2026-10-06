"""Command line: qaznews-kappa BATCH.csv [--min-kappa K] [--json]

Exit codes: 0 agreement is acceptable, 1 kappa is below --min-kappa, 2 the input is invalid.
"""

import argparse
import csv
import json
import sys

from . import __version__
from .agreement import load, report


def fmt(x):
    return "n/a" if x is None else f"{x:.3f}"


def text(r, path):
    lines = [
        f"batch       {path}",
        f"items       {r['items']} ({r['complete_items']} labelled by all annotators)",
        f"annotators  {', '.join(r['annotators'])}",
        f"labels      {', '.join(r['labels'])}",
        "",
        f"{'pair':<22}{'items':>6}{'observed':>10}{'kappa':>8}",
    ]
    for p in r["pairs"]:
        lines.append(
            f"{' ~ '.join(p['pair']):<22}{p['items']:>6}{p['observed']:>10.3f}{fmt(p['kappa']):>8}"
        )
    lines += [
        "",
        f"Light's kappa (mean pairwise Cohen)  {fmt(r['kappa'])}  {r['band']}",
        f"Fleiss' kappa                        {fmt(r['fleiss'])}",
    ]
    if r["confusions"]:
        lines.append(
            "most frequent disagreements: "
            + ", ".join(f"{a} / {b} ({n})" for a, b, n in r["confusions"])
        )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="qaznews-kappa", description="Inter-annotator agreement check for one labelled batch."
    )
    parser.add_argument("csv", help="CSV file with columns item, annotator, label")
    parser.add_argument(
        "--min-kappa",
        type=float,
        metavar="K",
        help="fail (exit code 1) if Light's kappa is below K",
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        r = report(load(args.csv))
    except (OSError, ValueError, csv.Error) as e:
        print(f"qaznews-kappa: error: {e}", file=sys.stderr)
        return 2

    passed = args.min_kappa is None or (r["kappa"] is not None and r["kappa"] >= args.min_kappa)
    if args.json:
        print(json.dumps({**r, "passed": passed}, indent=2, ensure_ascii=False))
    else:
        print(text(r, args.csv))
        if args.min_kappa is not None:
            verdict = "PASS" if passed else "FAIL"
            print(f"gate        kappa {fmt(r['kappa'])} vs minimum {args.min_kappa:.3f}: {verdict}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
