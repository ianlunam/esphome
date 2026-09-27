import base64
import os
import re
import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Custom tags ESPHome yaml uses that plain PyYAML doesn't know about.
# We only need the file to *parse* for the syntax/secrets checks, so treat
# them as opaque scalars/nodes rather than teaching yaml their real meaning.
_ESPHOME_TAGS = ["!secret", "!lambda", "!include", "!extend", "!remove"]


class _PermissiveLoader(yaml.SafeLoader):
    pass


def _construct_passthrough(loader, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


for _tag in _ESPHOME_TAGS:
    _PermissiveLoader.add_constructor(_tag, _construct_passthrough)


def load_yaml_permissive(path: Path):
    """Parse an ESPHome yaml file, tolerating its custom !tags."""
    with open(path, encoding="utf-8") as f:
        return yaml.load(f, Loader=_PermissiveLoader)


def esphome_config_files():
    """Every top-level ESPHome device config in the repo."""
    return sorted(
        p
        for p in REPO_ROOT.glob("*.yaml")
        if p.name not in ("secrets.yaml", "secrets.yaml.example")
    )


def secret_names_used_in(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"!secret\s+([A-Za-z0-9_]+)", text))


def dummy_value_for_secret(name: str) -> str:
    """A syntactically-valid placeholder for each kind of secret we use."""
    if name == "api_encryption_key":
        return base64.b64encode(os.urandom(32)).decode()
    if name.endswith("_tlv"):
        return "0e08" + "ab" * 30  # even-length hex, well under the 254-byte cap
    return f"test-{name}"


@pytest.fixture
def esphome_available():
    if shutil.which("esphome") is None:
        pytest.skip("esphome CLI not installed")
    return True
