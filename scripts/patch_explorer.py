"""Patch explorer JSX data constants from explorer_data.json.

Finds // DATA:{key} and // END:{key} markers in the JSX and replaces
the content between them with updated data from explorer_data.json.

Only touches data blocks — never modifies UI code, styles, or layout.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DATA_PATH = _ROOT / "explorer_data.json"
_JSX_PATH = _ROOT / "explorer" / "src" / "App.jsx"

# Map JSON keys to JS variable names
_KEY_TO_VAR = {
    "paretoData": "paretoData",
    "shapData": "shapData",
    "bmGapData": "bmGapData",
    "stats": "stats",
}


def _json_to_js(key: str, value: object) -> str:
    """Convert a JSON value to a JS const declaration."""
    js_val = json.dumps(value, indent=2)
    # Convert JSON null → JS null (already compatible)
    # Convert JSON true/false → JS true/false
    js_val = js_val.replace('"true"', "true").replace('"false"', "false")
    return f"const {key} = {js_val};"


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

    jsx = _JSX_PATH.read_text()
    patched = 0

    for key in data:
        var_name = _KEY_TO_VAR.get(key, key)
        pattern = rf"(// DATA:{key}\n).*?(// END:{key})"

        if re.search(pattern, jsx, re.DOTALL):
            replacement = f"// DATA:{key}\n{_json_to_js(var_name, data[key])}\n// END:{key}"
            jsx = re.sub(pattern, replacement, jsx, flags=re.DOTALL)
            patched += 1
        else:
            # Marker not found — skip silently (marker may not be added yet)
            pass

    if patched > 0:
        _JSX_PATH.write_text(jsx)
        print(f"✓ Patched {patched} data blocks in {_JSX_PATH.name}")
    else:
        print("⚠ No DATA/END markers found in JSX. Add markers first:")
        print("  // DATA:paretoData")
        print("  const paretoData = [...];")
        print("  // END:paretoData")
        print(f"\nData saved to {_DATA_PATH} — patch manually or add markers.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
