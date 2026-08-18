from datetime import date

from ajan_ordusu import config
from ajan_ordusu.main import _auto_output_filename, apply_bulletin_auto_defaults, build_parser


def test_auto_output_filename_is_deterministic():
    assert _auto_output_filename("PL", today=date(2026, 8, 18)) == "bulten_PL_2026-08-18.md"


def test_bulletin_auto_fills_in_next_n_and_output():
    parser = build_parser()
    args = parser.parse_args(["--bulletin-auto", "--competition", "TR1"])

    apply_bulletin_auto_defaults(args, parser)

    assert args.bulletin is True
    assert args.next_n == config.DEFAULT_AUTO_BULLETIN_NEXT_N
    assert args.output == _auto_output_filename("TR1")


def test_bulletin_auto_respects_explicit_next_and_output():
    parser = build_parser()
    args = parser.parse_args(
        ["--bulletin-auto", "--competition", "TR1", "--next", "5", "--output", "ozel.md"]
    )

    apply_bulletin_auto_defaults(args, parser)

    assert args.next_n == 5
    assert args.output == "ozel.md"


def test_bulletin_auto_without_competition_is_rejected():
    parser = build_parser()
    args = parser.parse_args(["--bulletin-auto"])

    try:
        apply_bulletin_auto_defaults(args, parser)
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("--bulletin-auto --competition olmadan kabul edilmemeli")


def test_bulletin_auto_is_noop_without_the_flag():
    parser = build_parser()
    args = parser.parse_args(["--demo"])
    apply_bulletin_auto_defaults(args, parser)  # çökmemeli, hiçbir şeyi değiştirmemeli
    assert args.bulletin is False
    assert args.output is None
