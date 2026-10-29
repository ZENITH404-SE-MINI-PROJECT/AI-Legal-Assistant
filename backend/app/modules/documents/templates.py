
from fastapi import APIRouter, HTTPException, Query

from .catalogue import load_templates

router = APIRouter(
    prefix="/api/templates",
    tags=["Document Templates"],
)


@router.get("/")
def list_templates(search: str | None = Query(default=None)):
    templates = load_templates()

    if not search or not search.strip():
        return {"templates": templates}

    term = search.strip().casefold()
    results = []

    for template in templates:
        keywords = template.get("keywords", [])

        searchable_text = " ".join([
            template.get("name", ""),
            template.get("category", ""),
            template.get("description", ""),
            " ".join(keywords),
        ]).casefold()

        if term in searchable_text:
            results.append(template)

    return {"templates": results}


@router.get("/{template_id}")
def get_template(template_id: str):
    for template in load_templates():
        if template.get("id") == template_id:
            return template

    raise HTTPException(
        status_code=404,
        detail="Template not found.",
    )
