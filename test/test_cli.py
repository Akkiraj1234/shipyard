import shipyard.cli as cli


def test_cli_bootstraps_executes_and_cleans_up(monkeypatch):
    stream = object()
    command = object()
    calls = []

    monkeypatch.setattr(cli, "create_parser", lambda argv: stream)
    monkeypatch.setattr(cli, "build_core_flag", lambda parser: {"dev": True})
    monkeypatch.setattr(cli, "ShipyardCommand", lambda ctx: command)
    monkeypatch.setattr(cli, "execute", lambda parsed, root: calls.append((parsed, root)) or 0)
    monkeypatch.setattr(cli, "cleanup", lambda root, ctx: calls.append((root, ctx)))

    assert cli.main() == 0
    assert calls == [(stream, command), (command, {"dev": True})]


def test_cli_sends_execution_errors_to_the_error_renderer_and_still_cleans_up(monkeypatch):
    command = object()
    cleaned = []
    received = []

    monkeypatch.setattr(cli, "create_parser", lambda argv: object())
    monkeypatch.setattr(cli, "build_core_flag", lambda parser: {})
    monkeypatch.setattr(cli, "ShipyardCommand", lambda ctx: command)
    monkeypatch.setattr(cli, "execute", lambda parsed, root: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(cli, "shipyard_error_print", lambda error, ctx: received.append((error, ctx)) or 2)
    monkeypatch.setattr(cli, "cleanup", lambda root, ctx: cleaned.append((root, ctx)))

    assert cli.main() == 2
    assert isinstance(received[0][0], RuntimeError)
    assert cleaned == [(command, {})]
