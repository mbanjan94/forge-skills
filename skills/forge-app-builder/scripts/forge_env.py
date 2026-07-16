"""Build an environment for Forge CLI subprocesses with skill attribution."""

import os
import re

_ATTRIBUTION_PREFIX = "ATL_FORGE_ATTRIBUTION_"
_VALUE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_MAX_LEN = 128


def _is_valid_value(value):
    return (
        isinstance(value, str)
        and 0 < len(value) <= _MAX_LEN
        and _VALUE_RE.fullmatch(value) is not None
    )


def forge_env(skill_name="forge-app-builder", extra=None, base=None):
    """Return a copied environment with valid attribution fields stamped in."""
    env = dict(os.environ if base is None else base)
    fields = dict(extra or {})
    fields["SKILL_NAME"] = skill_name

    for key, value in fields.items():
        if _is_valid_value(value):
            env[_ATTRIBUTION_PREFIX + key.upper()] = value
    return env
