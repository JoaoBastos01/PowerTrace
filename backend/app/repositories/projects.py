"""Project repository.

Keep route handlers thin. Put database reads/writes here once persistence is
chosen.
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import Generation, Project
from app.schemas.generation import GenerationCreateRequest, GenerationStatus
from app.schemas.project import ProjectCreateRequest


class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def list_by_owner(self, owner_id: str) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc(), Project.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def create(self, owner_id: str, request: ProjectCreateRequest) -> Project:
        project = Project(
            owner_id=owner_id,
            name=request.name,
            description=request.description,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_owned(self, owner_id: str, project_id: str) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def create_generation(
        self,
        owner_id: str,
        project_id: str,
        request: GenerationCreateRequest,
    ) -> Generation | None:
        if self.get_owned(owner_id, project_id) is None:
            return None

        generation = Generation(
            project_id=project_id,
            status=GenerationStatus.pending.value,
            input_json=request.model_dump_json(),
        )
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        return generation

    def mark_generation_generated(
        self,
        owner_id: str,
        project_id: str,
        generation_id: str,
        dxf_filename: str,
    ) -> Generation | None:
        generation = self.get_generation_owned(owner_id, project_id, generation_id)
        if generation is None:
            return None

        generation.status = GenerationStatus.generated.value
        generation.dxf_filename = dxf_filename
        generation.result_json = json.dumps({"dxf_filename": dxf_filename})
        generation.error_message = None
        self.db.commit()
        self.db.refresh(generation)
        return generation

    def mark_generation_failed(
        self,
        owner_id: str,
        project_id: str,
        generation_id: str,
        error_message: str,
    ) -> Generation | None:
        generation = self.get_generation_owned(owner_id, project_id, generation_id)
        if generation is None:
            return None

        generation.status = GenerationStatus.failed.value
        generation.error_message = error_message
        self.db.commit()
        self.db.refresh(generation)
        return generation

    def get_generation_owned(
        self,
        owner_id: str,
        project_id: str,
        generation_id: str,
    ) -> Generation | None:
        statement = (
            select(Generation)
            .join(Project, Project.id == Generation.project_id)
            .where(
                Generation.id == generation_id,
                Generation.project_id == project_id,
                Project.owner_id == owner_id,
            )
        )
        return self.db.scalar(statement)
