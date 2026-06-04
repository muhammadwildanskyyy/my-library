"""
Library CRUD endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_id, get_library_service
from app.api.v1.schemas.library import (
    LibraryCreate,
    LibraryListResponse,
    LibraryResponse,
)
from app.service.library_service import LibraryNotFoundError, LibraryService

router = APIRouter(prefix="/libraries", tags=["Libraries"])


@router.post(
    "/",
    response_model=LibraryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new library",
)
async def create_library(
    body: LibraryCreate,
    user_id: str = Depends(get_current_user_id),
    library_svc: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    library = await library_svc.create_library(
        user_id=user_id, name=body.name, description=body.description
    )
    return LibraryResponse(
        id=library.id,
        user_id=UUID(library.user_id),
        name=library.name,
        description=library.description,
        created_at=library.created_at,
        updated_at=library.updated_at,
    )


@router.get(
    "/",
    response_model=LibraryListResponse,
    summary="List all libraries for the current user",
)
async def list_libraries(
    user_id: str = Depends(get_current_user_id),
    library_svc: LibraryService = Depends(get_library_service),
) -> LibraryListResponse:
    libraries = await library_svc.list_libraries(user_id)
    return LibraryListResponse(
        libraries=[
            LibraryResponse(
                id=lib.id,
                user_id=UUID(lib.user_id),
                name=lib.name,
                description=lib.description,
                created_at=lib.created_at,
                updated_at=lib.updated_at,
            )
            for lib in libraries
        ],
        total=len(libraries),
    )


@router.get(
    "/{library_id}",
    response_model=LibraryResponse,
    summary="Get a library by ID",
)
async def get_library(
    library_id: UUID,
    user_id: str = Depends(get_current_user_id),
    library_svc: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    try:
        library = await library_svc.get_library(library_id, user_id)
    except LibraryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return LibraryResponse(
        id=library.id,
        user_id=UUID(library.user_id),
        name=library.name,
        description=library.description,
        created_at=library.created_at,
        updated_at=library.updated_at,
    )


@router.delete(
    "/{library_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a library and all its contents",
)
async def delete_library(
    library_id: UUID,
    user_id: str = Depends(get_current_user_id),
    library_svc: LibraryService = Depends(get_library_service),
) -> None:
    try:
        await library_svc.delete_library(library_id, user_id)
    except LibraryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
