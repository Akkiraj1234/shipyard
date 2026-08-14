from pathlib import Path

import shipyard.core as core
from shipyard.core import Command, build_context, build_core_flag, command_help, execute, load_command
from shipyard.parser import create_parser
from shipyard.types import GrammarRegistry, ParseResult, RegistryData


class LeafCommand(Command):
    @property
    def metadata(self):
        return RegistryData("leaf", "", "")

    def grammar(self):
        return GrammarRegistry(flags={"force"})

    def get_child(self, name):
        raise AssertionError("leaf commands do not have children")

    def child_metadata(self):
        return {}

    def run(self, result):
        self.result = result
        return 7


class RootCommand(Command):
    def __init__(self, child):
        super().__init__({"dev": False}, "root")
        self.child = child

    @property
    def metadata(self):
        return RegistryData("root", "", "", child_path="children")

    def grammar(self):
        return GrammarRegistry(has_child=True, words={"leaf"})

    def get_child(self, name):
        assert name == "leaf"
        return self.child

    def child_metadata(self):
        return {"leaf": self.child.metadata}

    def run(self, result):
        raise AssertionError("root should delegate to its child")


class RegistryProbe(Command):
    @property
    def metadata(self):
        return RegistryData("probe", "", "")

    def grammar(self):
        return GrammarRegistry()

    def get_child(self, name):
        raise KeyError(name)

    def child_metadata(self):
        return {}

    def run(self, result):
        return 0


def test_execute_routes_once_then_runs_the_resolved_child():
    child = LeafCommand({}, "leaf")

    code = execute(create_parser(["shipyard", "leaf", "--force"]), RootCommand(child))

    assert code == 7
    assert child.result.flags == {"force"}


def test_build_core_flag_collects_only_recognized_root_flags():
    parser = create_parser(["shipyard", "--dev", "--only-json", "--unknown"])

    assert build_core_flag(parser) == {"dev": True, "only-json": True}
    assert parser.current["name"] == "unknown"


def test_build_context_and_command_help_expose_core_command_information(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "load_config", lambda: (tmp_path, {"project": {"name": "Demo"}}))
    command = LeafCommand({}, "leaf")

    assert build_context() == {"project": {"name": "Demo"}, "root_path": tmp_path}
    assert command_help(command) == ""


def test_command_registry_discovers_valid_metadata_and_keeps_going_after_errors(tmp_path):
    valid = tmp_path / "valid"
    valid.mkdir()
    (valid / "main.py").write_text("class TempCommand: pass\n", encoding="utf-8")
    (valid / "metadata.py").write_text(
        "from shipyard.types import RegistryData\n"
        "METADATA = RegistryData('valid', 'Valid command', 'help', entry_class='main:TempCommand')\n",
        encoding="utf-8",
    )
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "metadata.py").write_text("METADATA = 'not registry data'\n", encoding="utf-8")

    registry, errors = RegistryProbe({})._get_child_metadata(tmp_path)

    assert set(registry) == {"valid"}
    assert registry["valid"].entry_class == f"{(valid / 'main.py').resolve()}:TempCommand"
    assert len(errors) == 1
    assert errors[0].command == "broken"


def test_load_command_instantiates_a_declared_command_class(tmp_path):
    module_path = tmp_path / "command.py"
    module_path.write_text(
        "from shipyard.core import Command\n"
        "from shipyard.types import GrammarRegistry, RegistryData\n"
        "class TempCommand(Command):\n"
        "    @property\n"
        "    def metadata(self): return RegistryData('temp', '', '')\n"
        "    def grammar(self): return GrammarRegistry()\n"
        "    def get_child(self, name): raise KeyError(name)\n"
        "    def child_metadata(self): return {}\n"
        "    def run(self, result): return 0\n",
        encoding="utf-8",
    )
    metadata = RegistryData("temp", "", "", entry_class=f"{module_path}:TempCommand")
    root_ctx = {"dev": True}

    command = load_command(root_ctx, metadata)

    assert command.name == "temp"
    assert command.root_ctx is root_ctx
