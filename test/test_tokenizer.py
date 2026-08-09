import pytest

from shipyard.error import InvalidInputError, UnknownCommandError
from shipyard.parser import create_parser, strip_prefix, tokenize
from shipyard.types import GrammarRegistry, TokenType


def test_tokenize_normalizes_words_flags_and_options():
    tokens = tokenize(
        ["shipyard", "roadmap", "--title", "Parser", "--force", "--tag=beta"]
    )

    assert tokens == [
        {"type": TokenType.word, "name": "roadmap", "value": None},
        {"type": TokenType.option, "name": "title", "value": "Parser"},
        {"type": TokenType.flag, "name": "force", "value": None},
        {"type": TokenType.option, "name": "tag", "value": "beta"},
    ]


@pytest.mark.parametrize(
    ("raw", "expected"), [("--force", "force"), ("-f", "f"), ("command", "command")]
)
def test_strip_prefix(raw, expected):
    assert strip_prefix(raw) == expected


def test_parser_delegates_to_child_then_parses_its_input():
    stream = create_parser(["shipyard", "roadmap", "--title=Parser", "--force"])

    root = stream.parse(GrammarRegistry(has_child=True, words={"roadmap"}))
    child = stream.parse(
        GrammarRegistry(options={"title"}, flags={"force"})
    )

    assert root.child == "roadmap"
    assert child.options == {"title": "Parser"}
    assert child.flags == {"force"}


def test_parser_rejects_an_unknown_child_with_a_suggestion():
    stream = create_parser(["shipyard", "docter"])

    with pytest.raises(UnknownCommandError, match="unknown command 'docter'"):
        stream.parse(GrammarRegistry(has_child=True, words={"doctor"}))


def test_parser_rejects_an_unknown_option():
    stream = create_parser(["shipyard", "--forse"])

    with pytest.raises(InvalidInputError, match="unknown flag '--forse'"):
        stream.parse(GrammarRegistry(flags={"force"}))
