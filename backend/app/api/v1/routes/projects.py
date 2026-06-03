"""Project, generation, and download routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.db_models import Project
from app.database import get_db
from app.repositories.projects import ProjectRepository

from app.dependencies.auth import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.generation import (
    GenerationCreateRequest,
    GenerationCreatedResponse,
    GenerationDetailResponse,
)
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)],
)

def to_project_response(project: Project) -> ProjectResponse:
    """Convert a Project ORM model into an API response."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectListResponse:
    repo = ProjectRepository(db)
    projects = repo.list_by_owner(current_user.id)

    return ProjectListResponse(
        items=[to_project_response(project) for project in projects]
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = repo.create(current_user.id, request)

    return to_project_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = repo.get_owned(current_user.id, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return to_project_response(project)


@router.post(
    "/{project_id}/generations",
    response_model=GenerationCreatedResponse,
    status_code=status.HTTP_200_OK,
)
def generate_project_plant(
    project_id: str,
    request: GenerationCreateRequest,
) -> GenerationCreatedResponse:
    """Generate a plant from the form data."""
    # TODO: Validate project ownership.
    # TODO: Convert request.rooms into the generator/program input.
    # TODO: Keep TUG calculation fixed in the electrical domain layer.
    # TODO: Apply TUE overrides from request.rooms[*].specific_outlets.
    # TODO: Execute generator and save DXF metadata in persistence.
    # TODO: Return generated status and download_url on success.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="TODO: generate project plant.",
    )


@router.get(
    "/{project_id}/generations/{generation_id}",
    response_model=GenerationDetailResponse,
)
def get_generation(project_id: str, generation_id: str) -> GenerationDetailResponse:
    """Return generation status/details for the result page."""
    # TODO: Validate project ownership.
    # TODO: Return status, output filename, errors, and download_url.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"TODO: load generation {generation_id} for project {project_id}.",
    )


@router.get("/{project_id}/generations/{generation_id}/download")
def download_generation(project_id: str, generation_id: str) -> FileResponse:
    """Download the generated DXF file."""
    # TODO: Validate project ownership.
    # TODO: Resolve the output path from persisted generation metadata.
    # TODO: Return FileResponse(path, filename=..., media_type=...).
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"TODO: download generation {generation_id} for project {project_id}.",
    )
