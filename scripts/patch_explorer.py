"""Patch explorer JSX data constants from explorer_data.json.

Finds // DATA:{key} and // END:{key} markers in the JSX and replaces
the content between them with updated data from explorer_data.json.

The deployed app is canonical; the root explorer.jsx copy is synchronized
from it after every successful patch.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DATA_PATH = _ROOT / "explorer_data.json"
_JSX_PATH = _ROOT / "explorer" / "src" / "App.jsx"
_JSX_COPY_PATH = _ROOT / "explorer.jsx"

# Map JSON keys to JS variable names
_KEY_TO_VAR = {
    "paretoData": "paretoData",
    "shapData": "shapData",
    "shapContext": "shapContext",
    "bmGapData": "bmGapData",
    "findings": "findings",
    "papers": "papers",
    "formulations": "formulations",
    "lopocvFolds": "lopocvFolds",
    "stats": "stats",
    "coverageStats": "coverageStats",
    "labelDistribution": "labelDistribution",
    "sourceSummary": "sourceSummary",
    "validationSummary": "validationSummary",
}


def _json_to_js(key: str, value: object) -> str:
    """Convert a JSON value to a JS const declaration."""
    js_val = json.dumps(value, indent=2)
    return f"const {key} = {js_val};"


def patch_jsx(jsx: str, data: dict[str, object]) -> tuple[str, int, list[str]]:
    """Replace required generated-data blocks in JSX text."""
    patched = 0
    missing: list[str] = []
    for key, var_name in _KEY_TO_VAR.items():
        if key not in data:
            missing.append(f"data:{key}")
            continue
        pattern = rf"(// DATA:{re.escape(key)}\n).*?(// END:{re.escape(key)})"
        if not re.search(pattern, jsx, re.DOTALL):
            missing.append(f"marker:{key}")
            continue
        replacement = (
            f"// DATA:{key}\n{_json_to_js(var_name, data[key])}\n// END:{key}"
        )
        jsx = re.sub(
            pattern,
            lambda _match, replacement=replacement: replacement,
            jsx,
            count=1,
            flags=re.DOTALL,
        )
        patched += 1
    return jsx.replace(chr(0x2014), "-"), patched, missing


def main() -> int:
    """Patch explorer JSX with data from explorer_data.json."""
    if not _DATA_PATH.exists():
        print(f"✗ {_DATA_PATH} not found. Run extract_explorer_data.py first.")
        return 1

    if not _JSX_PATH.exists():
        print(f"✗ {_JSX_PATH} not found.")
        return 1

    with open(_DATA_PATH) as f:
        data = json.load(f)

    jsx, patched, missing = patch_jsx(_JSX_PATH.read_text(), data)
    if missing:
        print(f"✗ Missing required explorer blocks: {', '.join(missing)}")
        return 1

    _JSX_PATH.write_text(jsx)
    _JSX_COPY_PATH.write_text(jsx)
    print(f"✓ Patched {patched} data blocks in {_JSX_PATH.name}")
    print(f"✓ Synchronized {_JSX_COPY_PATH.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
