from shipyard.shipyard import ShipyardCommand


def test_root_command_discovers_registered_commands_and_exposes_them_as_words():
    command = ShipyardCommand({})

    registry = command.child_metadata()
    grammar = command.grammar()

    assert set(registry) == {"doctor", "init"}
    assert grammar.has_child is True
    assert grammar.words == {"doctor", "init"}


def test_root_command_loads_only_the_requested_child():
    command = ShipyardCommand({})

    child = command.get_child("init")

    assert child.name == "init"
    assert child.__class__.__name__ == "InitCommand"
