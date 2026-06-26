from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility for local/dev runs.
    import tomli as tomllib  # type: ignore[no-redef]


def loads(text: str) -> dict[str, object]:
    return tomllib.loads(text)
