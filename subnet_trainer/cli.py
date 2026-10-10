"""Command-line interface: quiz, calc and stats."""

from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Callable

from . import __version__, core, stats
from .questions import ALL_TOPICS, CONCEPT_TOPICS, SUBNET_TOPICS, generate


def _colour(enabled: bool):
    def paint(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if enabled else text
    return paint


def run_quiz(
    topics: list[str],
    count: int,
    difficulty: str,
    rng: random.Random,
    ask: Callable[[str], str] = input,
    out: Callable[[str], None] = print,
    colour: bool = False,
) -> list[tuple[str, bool]]:
    paint = _colour(colour)
    results: list[tuple[str, bool]] = []
    start = time.monotonic()
    out(f"{count} questions. Type 'q' to stop early.\n")
    for n in range(1, count + 1):
        q = generate(topics, rng, difficulty)
        try:
            response = ask(f"[{n}/{count}] {q.prompt}\n> ")
        except EOFError:
            break
        if response.strip().lower() in {"q", "quit", "exit"}:
            break
        ok = q.check(response)
        results.append((q.topic, ok))
        if ok:
            out(paint("Correct.", "32") + "\n")
        else:
            out(paint(f"Not quite. Answer: {q.answer}", "31"))
            out(f"  {q.explanation}\n")
    if results:
        right = sum(ok for _, ok in results)
        secs = time.monotonic() - start
        out(f"Score: {right}/{len(results)} ({100 * right / len(results):.0f}%) "
            f"in {secs:.0f}s")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="subnet-trainer",
        description="Drill subnetting, OSI layers and ports for Network+ / CCNA.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    quiz = sub.add_parser("quiz", help="answer randomly generated questions")
    quiz.add_argument("-n", "--count", type=int, default=10)
    quiz.add_argument("-d", "--difficulty", choices=["easy", "medium", "hard"], default="medium")
    quiz.add_argument(
        "-t", "--topics",
        help=f"comma-separated; 'subnet', 'concepts' or any of: {', '.join(ALL_TOPICS)}",
        default="subnet",
    )
    quiz.add_argument("--seed", type=int, help="repeat the same set of questions")
    quiz.add_argument("--no-save", action="store_true", help="don't record stats")

    calc = sub.add_parser("calc", help="break down an address, e.g. 10.4.77.130/27")
    calc.add_argument("address", nargs="+")

    sub.add_parser("stats", help="show accuracy per topic, weakest first")

    args = parser.parse_args(argv)

    if args.command == "calc":
        try:
            print(core.describe(" ".join(args.address)))
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    if args.command == "stats":
        print(stats.report(stats.load()))
        return 0

    topics: list[str] = []
    for t in args.topics.split(","):
        t = t.strip()
        if t == "subnet":
            topics += list(SUBNET_TOPICS)
        elif t == "concepts":
            topics += list(CONCEPT_TOPICS)
        elif t == "all":
            topics += list(ALL_TOPICS)
        elif t in ALL_TOPICS:
            topics.append(t)
        else:
            parser.error(f"unknown topic {t!r}")
    if args.count < 1:
        parser.error("--count must be at least 1")

    rng = random.Random(args.seed)
    try:
        results = run_quiz(topics, args.count, args.difficulty, rng, colour=sys.stdout.isatty())
    except KeyboardInterrupt:
        print()
        return 130
    if results and not args.no_save:
        stats.record(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
