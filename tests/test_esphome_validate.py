"""Runs `esphome config` on every device file to catch real schema errors
(bad pins, conflicting components, invalid keys, etc.) that the static
checks in test_config_files.py can't see.

Needs the `esphome` CLI, and network access for any file using a `packages:`
github import. A network failure is reported as a skip, not a failure, since
that's an environment limitation rather than a bug in the config.
"""

import subprocess

import pytest

from conftest import (
    REPO_ROOT,
    dummy_value_for_secret,
    esphome_config_files,
    secret_names_used_in,
)

_NETWORK_ERROR_HINTS = (
    "Couldn't resolve host",
    "Failed to establish a new connection",
    "Temporary failure in name resolution",
    "CERTIFICATE_VERIFY_FAILED",
    "Connection timed out",
    "Cloning",
)


@pytest.mark.parametrize(
    "config_path", esphome_config_files(), ids=lambda p: p.name
)
def test_config_validates(config_path, esphome_available, tmp_path):
    # Copy just this file into an isolated dir with a throwaway
    # secrets.yaml, so this never touches a real secrets.yaml the user
    # may have alongside it.
    work_file = tmp_path / config_path.name
    work_file.write_text(
        config_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    needed_secrets = secret_names_used_in(config_path)
    secrets_yaml = "\n".join(
        f"{name}: {dummy_value_for_secret(name)!r}"
        for name in sorted(needed_secrets)
    )
    (tmp_path / "secrets.yaml").write_text(secrets_yaml, encoding="utf-8")

    result = subprocess.run(
        ["esphome", "config", str(work_file)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
    )

    combined = result.stdout + result.stderr

    if result.returncode != 0:
        if any(hint in combined for hint in _NETWORK_ERROR_HINTS):
            pytest.skip(
                f"network unavailable while validating {config_path.name}"
            )
        pytest.fail(f"`esphome config {config_path.name}` failed:\n{combined}")

    assert "Configuration is valid!" in combined


def test_no_secret_values_committed_to_repo():
    """Guard against accidentally committing a real secrets.yaml."""
    assert not (REPO_ROOT / "secrets.yaml").exists(), (
        "a real secrets.yaml exists in the repo working tree — make sure it's "
        "never `git add`-ed (it's gitignored, but double-check `git status`)"
    )
