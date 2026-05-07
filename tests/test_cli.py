from __future__ import annotations

from hermes_timetree_sync.cli import build_parser


def test_parser_accepts_doctor_command() -> None:
    args = build_parser().parse_args(["doctor"])
    assert args.command == "doctor"
