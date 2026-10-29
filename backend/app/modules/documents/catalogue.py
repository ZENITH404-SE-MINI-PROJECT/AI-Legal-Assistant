
import json
from pathlib import Path

from fastapi import HTTPException

# Project root / docs / template-catalogue.json
CATALOGUE_PATH = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "template-catalogue.json"
)


def load_templates() -> list[dict]:
    try:
        with CATALOGUE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

        templates = data.get("templates", [])

        if not isinstance(templates, list):
            raise HTTPException(
                status_code=500,
                detail="Invalid template catalogue format.",
            )

        return templates

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Template catalogue file not found.",
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Template catalogue contains invalid JSON.",
        )
