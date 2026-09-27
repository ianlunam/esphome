"""Static checks that don't need the esphome CLI or network access."""

import yaml

from conftest import (
    REPO_ROOT,
    esphome_config_files,
    load_yaml_permissive,
    secret_names_used_in,
)


def test_at_least_one_config_exists():
    assert esphome_config_files(), (
        "expected to find ESPHome yaml files in the repo root"
    )


def test_yaml_files_parse():
    for path in esphome_config_files():
        load_yaml_permissive(path)  # raises yaml.YAMLError on bad syntax


def test_every_secret_reference_is_documented():
    example = REPO_ROOT / "secrets.yaml.example"
    assert example.exists(), "secrets.yaml.example is missing"
    documented = set(yaml.safe_load(example.read_text(encoding="utf-8")) or {})

    for path in esphome_config_files():
        used = secret_names_used_in(path)
        missing = used - documented
        assert not missing, (
            f"{path.name} references !secret {sorted(missing)} "
            f"which {example.name} doesn't define"
        )


def test_no_unused_secrets_in_example():
    example = REPO_ROOT / "secrets.yaml.example"
    documented = set(
        yaml.safe_load(example.read_text(encoding="utf-8")) or {}
    )

    used = set()
    for path in esphome_config_files():
        used |= secret_names_used_in(path)

    unused = documented - used
    assert not unused, (
        f"{example.name} defines {sorted(unused)}, which no yaml file "
        "references anymore — remove it so it doesn't look load-bearing"
    )


def test_secrets_yaml_is_gitignored():
    gitignore_text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    gitignore = gitignore_text.splitlines()
    assert "secrets.yaml" in [line.strip() for line in gitignore], (
        "secrets.yaml must stay out of git, or a real device's wifi "
        "password / API key will end up in the repo history"
    )


def test_configs_declare_a_friendly_name():
    for path in esphome_config_files():
        config = load_yaml_permissive(path)
        subs = config.get("substitutions", {})
        assert subs.get("name"), f"{path.name} is missing substitutions.name"
        assert subs.get("friendly_name"), (
            f"{path.name} is missing substitutions.friendly_name"
        )
