from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sicav_checker.config import settings
from sicav_checker.services.project_service import ProjectService


@lru_cache(maxsize=1)
def get_project_service() -> ProjectService:
    return ProjectService(root_dir=Path("data/projects"), app_settings=settings)