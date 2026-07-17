"""Command-line interface: `adsherlock ask "<question>"`."""

from __future__ import annotations

import argparse
import sys

from .analyst import Analyst
from .client import SpyFuClient
from .config import Settings


def _cmd_ask(args: argparse.Namespace) -> int:
    settings = Settings.load()
    if args.country:
        settings.default_country = args.country
    if args.model:
        settings.model = args.model

    # The analyst's reasoning always runs on Claude; --mock only swaps in offline
    # SpyFu data (so you can try the pipeline without SpyFu creds or live calls).
    if not settings.anthropic_api_key:
        print("error: ANTHROPIC_API_KEY is not set (the analyst reasons with Claude). "
              "Set it in your environment or .env. Offline SpyFu behavior is covered "
              "by the test suite (python tests/test_offline.py).", file=sys.stderr)
        return 2

    with SpyFuClient(settings, mock=args.mock) as spyfu:
        analyst = Analyst(
            spyfu,
            model=settings.model,
            default_country=settings.default_country,
            max_steps=args.max_steps,
        )
        result = analyst.ask(args.question)

    print(result.answer)
    if args.trace:
        print("\n--- evidence trace ---", file=sys.stderr)
        for i, call in enumerate(result.trace, 1):
            print(f"{i}. {call.name}({call.input}) -> {call.result_summary}", file=sys.stderr)
        print(f"({result.steps} model steps)", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="adsherlock",
        description="Ask marketing questions; get answers proven with competitive-intelligence data.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="Ask a marketing question.")
    ask.add_argument("question", help="e.g. 'How are people running ads in the dog food niche?'")
    ask.add_argument("--country", help="Two-letter market code (default US).")
    ask.add_argument("--model", help="Claude model id (default from ANALYST_MODEL).")
    ask.add_argument("--max-steps", type=int, default=8, help="Max tool-use rounds.")
    ask.add_argument("--trace", action="store_true", help="Print the tool-call trace to stderr.")
    ask.add_argument("--mock", action="store_true", help="Use offline mock SpyFu data.")
    ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
