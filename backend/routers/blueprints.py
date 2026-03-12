"""
Blueprint listing router.

Prefix: /api/blueprints
Scans the blueprints directory and returns validated metadata.
"""

import logging
import os

import yaml
from fastapi import APIRouter
from pydantic import ValidationError

from engine.blueprint_schema import BlueprintDef

router = APIRouter(prefix="/api/blueprints", tags=["blueprints"])
logger = logging.getLogger(__name__)

BLUEPRINTS_DIR = "/app/blueprints"


@router.get("/")
async def list_blueprints():
    """Return metadata for every valid blueprint YAML in the blueprints dir."""
    results: list[dict] = []

    try:
        filenames = os.listdir(BLUEPRINTS_DIR)
    except FileNotFoundError:
        logger.warning("Blueprints directory %s not found", BLUEPRINTS_DIR)
        return results

    for filename in sorted(filenames):
        # Amendment 5: skip non-YAML files (e.g. .gitkeep)
        if not filename.endswith((".yaml", ".yml")):
            continue

        filepath = os.path.join(BLUEPRINTS_DIR, filename)
        try:
            with open(filepath, "r") as f:
                yaml_data = yaml.safe_load(f)
            blueprint = BlueprintDef.model_validate(yaml_data)
            results.append({
                "id": filename,
                "name": blueprint.name,
                "description": blueprint.description,
            })
        except (yaml.YAMLError, ValidationError, Exception) as e:
            logger.warning("Skipping invalid blueprint %s: %s", filename, e)
            continue

    return results
