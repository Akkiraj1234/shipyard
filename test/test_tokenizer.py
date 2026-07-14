from shipyard.parser import (
    tokenize, 
    TokenType, 
    strip_prefix,
    # classify_token_type, # we are not testing it because tokenize test already cover its test
)

import sys
import pytest


TOKENIZER_TEST_CASES = [
    {
        "query": ["shipyard"],
        "expected": []
    },
    {
        "query": ["shipyard", "roadmap"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "add"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "add",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "done", "SHP-001"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "done",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "SHP-001",
            }
        ]
    },
    {
        "query": ["shipyard", "task", "show", "TASK-100"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "task",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "show",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "TASK-100",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "--help"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "help",
            }
        ]
    },
    {
        "query": ["shipyard", "release", "--force", "--draft", "--verbose"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "release",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "force",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "draft",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "verbose",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "done", "SHP-001", "--status", "finished"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "done",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "SHP-001",
            },
            {
                "type": TokenType.option,
                "name": "status",
                "value": "finished",
            }
        ],
    },
    {
        "query": ["shipyard", "release", "--version", "1.0.0"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "release",
            },
            {
                "type": TokenType.option,
                "name": "version",
                "value": "1.0.0",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "add", "SHP-100", "--title", "Parser", "--priority", "high", "--assign", "Akki"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "add",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "SHP-100",
            },
            {
                "type": TokenType.option,
                "name": "title",
                "value": "Parser",
            },
            {
                "type": TokenType.option,
                "name": "priority",
                "value": "high",
            },
            {
                "type": TokenType.option,
                "name": "assign",
                "value": "Akki",
            }
        ],
    },
    {
        "query": ["shipyard", "release", "--version", "1.2.0", "--tag", "beta", "--author", "Akki"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "release",
            },
            {
                "type": TokenType.option,
                "name": "version",
                "value": "1.2.0",
            },
            {
                "type": TokenType.option,
                "name": "tag",
                "value": "beta",
            },
            {
                "type": TokenType.option,
                "name": "author",
                "value": "Akki",
            }
        ]
    },
    {
        "query": ["shipyard", "release", "--version=1.0.0"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "release",
            },
            {
                "type": TokenType.option,
                "name": "version",
                "value": "1.0.0",
            },
        ]
    },
    {
        "query": ["shipyard", "update", "--description","Fix parser and tokenizer",],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "update",
            },
            {
                "type": TokenType.option,
                "name": "description",
                "value": "Fix parser and tokenizer",
            },
        ]
    },
    {
        "query": ["shipyard", "roadmap", "add", "SHP-100", "--title", "Parser", "--priority", "high", "--assign", "Akki", "--force"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "add",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "SHP-100",
            },
            {
                "type": TokenType.option,
                "name": "title",
                "value": "Parser",
            },
            {
                "type": TokenType.option,
                "name": "priority",
                "value": "high",
            },
            {
                "type": TokenType.option,
                "name": "assign",
                "value": "Akki",
            },
            {
                 "type": TokenType.flag,
                "name": None,
                "value": "force",
            }
        ]
    },
    {
        "query": ["shipyard", "add", "../docs/ROADMAP.md"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "add",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "../docs/ROADMAP.md",
            }
        ],
    },
    {
        "query": ["shipyard", "roadmap", "done", "README.md"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "done",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "README.md",
            }
        ],
    },
    # fix the error -- become option adn hello become value fix the issue its not valid option so its should fall back to flag 
    # or simple raise syntax error flag cant be empty or option cant be empty
    pytest.param(
        {
            "query": ["shipyard", "--=hello", "-=hello"],
            "expected": [
                {
                    "type": TokenType.flag,
                    "name": None,
                    "value": "=hello",
                },
                {
                    "type": TokenType.flag,
                    "name": None,
                    "value": "=hello",
                }
            ]
        },
        marks=pytest.mark.xfail(reason="Not implemented yet")
    ),
    {
        "query": ["shipyard", "----force"],
        "expected": [
            {
                "type": TokenType.flag,
                "name": None,
                "value": "--force",
            }
        ]
    },
    {
        "query": ["shipyard", "-abc"],
        "expected": [
            {
                "type": TokenType.flag,
                "name": None,
                "value": "abc",
            }
        ]
    },
    {
        "query": ["shipyard", "roadmap", "add", "SHP-999", "--title", "Complete parser", "--priority=critical", "--assign", "Akki", "--message", "Implement grammar parser", "--force", "--verbose"],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "roadmap",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "add",
            },
            {
                "type": TokenType.word,
                "name": None,
                "value": "SHP-999",
            },
            {
                "type": TokenType.option,
                "name": "title",
                "value": "Complete parser",
            },
            {
                "type": TokenType.option,
                "name": "priority",
                "value": "critical",
            },
            {
                "type": TokenType.option,
                "name": "assign",
                "value": "Akki",
            },
            {
                "type": TokenType.option,
                "name": "message",
                "value": "Implement grammar parser",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "force",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "verbose",
            }
        ]
    },
    # the test case has no real life use because 
    # in sys never takes empty "" value but just to test
    # behavior we have implemented it.
    {
        "query": ["shipyard", "release", "--message", ""],
        "expected": [
            {
                "type": TokenType.word,
                "name": None,
                "value": "release",
            },
            {
                "type": TokenType.option,
                "name": "message",
                "value": "",
            }
        ]
    },
    {
        "query": ["shipyard", "--force", "--force"],
        "expected": [
            {
                "type": TokenType.flag,
                "name": None,
                "value": "force",
            },
            {
                "type": TokenType.flag,
                "name": None,
                "value": "force",
            },
        ],
    },
    {
        "query": ["shipyard", "--version", "1", "--version", "2"],
        "expected": [
            {
                "type": TokenType.option,
                "name": "version",
                "value": "1",
            },
            {
                "type": TokenType.option,
                "name": "version",
                "value": "2",
            },
        ],
    },
    {
        "query": ["shipyard", "--message", "a=b=c"],
        "expected": [
            {
                "type": TokenType.option,
                "name": "message",
                "value": "a=b=c",
            },
        ],
    },
    pytest.param(
        {
            "query": ["shipyard", ""],
            "expected": [
                {
                    "type": TokenType.word,
                    "name": None,
                    "value": "",
                },
            ],
        }
    ),
    # its should fail
    {
        "query": ["shipyard", "--"],
        "expected": [
            {
                "type": TokenType.flag,
                "name": None,
                "value": "",
            },
        ],
    },
    pytest.param(
        {
            "query": ["shipyard", "--="],
            "expected": [
                {
                    "type": TokenType.flag,
                    "name": None,
                    "value": "=",
                },
            ],
        },
        marks=pytest.mark.xfail(reason="Not implemented yet"),
    ),
    pytest.param(
        {
            "query": ["shipyard", "--=hello"],
            "expected": [
                {
                    "type": TokenType.flag,
                    "name": None,
                    "value": "=hello",
                },
            ],
        },
        marks=pytest.mark.xfail(reason="Not implemented yet"),
    ),
    {
        "query": ["shipyard", "--title="],
        "expected": [
            {
                "type": TokenType.option,
                "name": "title",
                "value": "",
            },
        ],
    },
]


@pytest.mark.parametrize("test", TOKENIZER_TEST_CASES)
def test_different_input(test, monkeypatch):
    token = tokenize(test["query"])
    assert token == test["expected"]
     

def test_remove_flag_prefix():
    assert strip_prefix("--help") == "help"
    assert strip_prefix("-h") == "h"
    assert strip_prefix("---help") == "-help"
    assert strip_prefix("-=-help") == "=-help"
    assert strip_prefix("roadmap") == "roadmap"
    
    


# from shipyard.parser import ParserStream
#      2 +from shipyard.types import TokenType
#      3 +from shipyard.utils import ListStream
#      4 +
#      5 +
#      6 +def test_list_stream_str_marks_current_item():
#      7 +    stream = ListStream(["roadmap", "--help"])
#      8 +
#      9 +    assert str(stream) == "\n".join(
#     10 +        [
#     11 +            "ListStream",
#     12 +            "├── roadmap  <- curr",
#     13 +            "└── --help",
#     14 +        ]
#     15 +    )
#     16 +
#     17 +
#     18 +def test_list_stream_str_marks_eof():
#     19 +    stream = ListStream(["roadmap"], 1)
#     20 +
#     21 +    assert str(stream) == "\n".join(
#     22 +        [
#     23 +            "ListStream",
#     24 +            "└── roadmap",
#     25 +            "└── <EOF>  <- curr",
#     26 +        ]
#     27 +    )
#     28 +
#     29 +
#     30 +def test_parser_stream_str_wraps_token_stream():
#     31 +    stream = ParserStream(
#     32 +        [
#     33 +            {
#     34 +                "type": TokenType.word,
#     35 +                "name": None,
#     36 +                "value": "roadmap",
#     37 +            }
#     38 +        ]
#     39 +    )
#     40 +
#     41 +    assert str(stream) == "\n".join(
#     42 +        [
#     43 +            "ParserStream(",
#     44 +            "ListStream",
#     45 +            "└── {'type': <TokenType.word: 0>, 'name': None, 'value': 'roadmap'}  <- curr",
#     46 +            ")",
#     47 +        ]
#     48 +    )