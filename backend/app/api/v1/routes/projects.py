"""Project, persisted generation, and DXF download routes."""

import logging
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.db_models import Generation, Project
from app.dependencies.auth import get_current_user
from app.repositories.projects import ProjectRepository
from app.schemas.auth import AuthenticatedUser
from app.schemas.generation import (
    GenerationCreateRequest,
    GenerationCreatedResponse,
    GenerationDetailResponse,
    GenerationResult,
    GenerationStatus,
)
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
)
from app.services import generation as generation_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])
GENERIC_GENERATION_ERROR = "An unexpected error occurred while generating the floor plan."


def to_project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def resource_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found.",
    )


def generation_download_url(project_id: str, generation_id: str) -> str:
    return (
        f"/api/v1/projects/{project_id}/generations/{generation_id}/download"
    )


def generation_response(
    *,
    project_id: str,
    generation_id: str,
    generation_status: GenerationStatus,
    seed: int,
    message: str,
    download_url: str | None = None,
    error_message: str | None = None,
) -> GenerationCreatedResponse:
    return GenerationCreatedResponse(
        project_id=project_id,
        generation_id=generation_id,
        status=generation_status,
        seed=seed,
        message=message,
        download_url=download_url,
        error_message=error_message,
    )


def error_json(
    response: GenerationCreatedResponse,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )


def mark_failed_safely(
    repo: ProjectRepository,
    db: Session,
    owner_id: str,
    project_id: str,
    generation_id: str,
    error_message: str,
) -> None:
    try:
        db.rollback()
        repo.mark_generation_failed(
            owner_id,
            project_id,
            generation_id,
            error_message,
        )
    except Exception:
        logger.exception("Could not persist failed generation state.")


def load_generation_input(generation: Generation) -> GenerationCreateRequest:
    if not generation.input_json:
        raise RuntimeError("Generation input metadata is missing.")
    request = GenerationCreateRequest.model_validate_json(generation.input_json)
    if request.seed is None:
        raise RuntimeError("Generation effective seed is missing.")
    return request


def load_generation_result(generation: Generation) -> GenerationResult | None:
    if not generation.result_json:
        return None
    return GenerationResult.model_validate_json(generation.result_json)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectListResponse:
    projects = ProjectRepository(db).list_by_owner(current_user.id)
    return ProjectListResponse(
        items=[to_project_response(project) for project in projects]
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectResponse:
    project = ProjectRepository(db).create(current_user.id, request)
    return to_project_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectResponse:
    project = ProjectRepository(db).get_owned(current_user.id, project_id)
    if project is None:
        raise resource_not_found()
    return to_project_response(project)


@router.post(
    "/{project_id}/generations",
    response_model=GenerationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": GenerationCreatedResponse,
            "description": "The generator could not produce a valid floor plan.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": GenerationCreatedResponse,
            "description": "The generation failed unexpectedly.",
        },
    },
)
def generate_project_plant(
    project_id: str,
    request: GenerationCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GenerationCreatedResponse | JSONResponse:
    """Generate and persist one project DXF synchronously."""
    repo = ProjectRepository(db)
    if repo.get_owned(current_user.id, project_id) is None:
        raise resource_not_found()

    effective_seed = request.seed if request.seed is not None else secrets.randbits(32)
    normalized_request = request.model_copy(update={"seed": effective_seed})
    generation = repo.create_generation(
        current_user.id,
        project_id,
        normalized_request,
    )
    if generation is None:
        raise resource_not_found()

    try:
        result = generation_service.generate_project_artifact(
            normalized_request,
            generation.id,
        )
    except generation_service.FloorPlanGenerationError as exc:
        error_message = str(exc)
        mark_failed_safely(
            repo,
            db,
            current_user.id,
            project_id,
            generation.id,
            error_message,
        )
        return error_json(
            generation_response(
                project_id=project_id,
                generation_id=generation.id,
                generation_status=GenerationStatus.failed,
                seed=effective_seed,
                message="Floor plan generation failed.",
                error_message=error_message,
            ),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    except Exception:
        logger.exception("Unexpected project generation failure.")
        mark_failed_safely(
            repo,
            db,
            current_user.id,
            project_id,
            generation.id,
            GENERIC_GENERATION_ERROR,
        )
        return error_json(
            generation_response(
                project_id=project_id,
                generation_id=generation.id,
                generation_status=GenerationStatus.failed,
                seed=effective_seed,
                message="Floor plan generation failed.",
                error_message=GENERIC_GENERATION_ERROR,
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        persisted = repo.mark_generation_generated(
            current_user.id,
            project_id,
            generation.id,
            result,
        )
        if persisted is None:
            raise RuntimeError("Generation record disappeared before completion.")
    except Exception:
        logger.exception("Could not persist generated artifact metadata.")
        (Path(settings.output_dir) / result.dxf_filename).unlink(missing_ok=True)
        mark_failed_safely(
            repo,
            db,
            current_user.id,
            project_id,
            generation.id,
            GENERIC_GENERATION_ERROR,
        )
        return error_json(
            generation_response(
                project_id=project_id,
                generation_id=generation.id,
                generation_status=GenerationStatus.failed,
                seed=effective_seed,
                message="Floor plan generation failed.",
                error_message=GENERIC_GENERATION_ERROR,
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return generation_response(
        project_id=project_id,
        generation_id=generation.id,
        generation_status=GenerationStatus.generated,
        seed=effective_seed,
        message="Floor plan generated successfully.",
        download_url=generation_download_url(project_id, generation.id),
    )


@router.get(
    "/{project_id}/generations/{generation_id}",
    response_model=GenerationDetailResponse,
)
def get_generation(
    project_id: str,
    generation_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GenerationDetailResponse:
    generation = ProjectRepository(db).get_generation_owned(
        current_user.id, project_id, generation_id
    )
    if generation is None:
        raise resource_not_found()

    try:
        request = load_generation_input(generation)
        result = load_generation_result(generation)
    except (ValueError, RuntimeError):
        logger.exception("Invalid persisted generation metadata.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generation metadata is invalid.",
        )

    download_url = None
    if generation.status == GenerationStatus.generated.value and generation.dxf_filename:
        download_url = generation_download_url(project_id, generation_id)

    return GenerationDetailResponse(
        project_id=project_id,
        generation_id=generation.id,
        status=GenerationStatus(generation.status),
        seed=request.seed,
        dxf_filename=generation.dxf_filename,
        error_message=generation.error_message,
        download_url=download_url,
        result=result,
    )


@router.get("/{project_id}/generations/{generation_id}/download")
def download_generation(
    project_id: str,
    generation_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> FileResponse:
    generation = ProjectRepository(db).get_generation_owned(
        current_user.id, project_id, generation_id
    )
    if generation is None:
        raise resource_not_found()
    if generation.status != GenerationStatus.generated.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The generated file is not available for this generation.",
        )
    if not generation.dxf_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated file not found.",
        )

    output_dir = Path(settings.output_dir).resolve()
    file_path = (output_dir / Path(generation.dxf_filename).name).resolve()
    if file_path.parent != output_dir or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated file not found.",
        )
    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type="application/dxf",
    )
