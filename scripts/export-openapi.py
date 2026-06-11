from __future__ import annotations

import json
from pathlib import Path

from trustfacechain.api import create_app


def main() -> int:
    app = create_app(
        db_path="data/runtime/openapi-preview.db",
        key_path="data/runtime/openapi-preview.key",
    )
    output = Path("build/openapi/trustfacechain.openapi.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

