"""
Shelf CRUD endpoints — nested under /libraries/{library_id}/shelves.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_id, get_shelf_service
from app.api.v1.schemas.shelf import ShelfCreate, ShelfListResponse, ShelfResponse
from app.service.shelf_service import ShelfNotFoundError, ShelfService

router = APIRouter(prefix="/libraries/{library_id}/shelves", tags=["Shelves"])


@router.post(
    "/",
    response_model=ShelfResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shelf in a library",
)
async def create_shelf(
    library_id: UUID,
    body: ShelfCreate,
    user_id: str = Depends(get_current_user_id),
    shelf_svc: ShelfService = Depends(get_shelf_service),
) -> ShelfResponse:
    try:
        shelf = await shelf_svc.create_shelf(
            user_id=user_id,
            library_id=library_id,
            name=body.name,
            description=body.description,
        )
    except ShelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ShelfResponse(
        id=shelf.id,
        library_id=shelf.library_id,
        user_id=UUID(shelf.user_id),
        name=shelf.name,
        description=shelf.description,
        created_at=shelf.created_at,
        updated_at=shelf.updated_at,
    )


@router.get(
    "/",
    response_model=ShelfListResponse,
    summary="List all shelves in a library",
)
async def list_shelves(
    library_id: UUID,
    user_id: str = Depends(get_current_user_id),
    shelf_svc: ShelfService = Depends(get_shelf_service),
) -> ShelfListResponse:
    try:
        shelves = await shelf_svc.list_shelves(library_id, user_id)
    except ShelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ShelfListResponse(
        shelves=[
            ShelfResponse(
                id=s.id,
                library_id=s.library_id,
                user_id=UUID(s.user_id),
                name=s.name,
                description=s.description,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in shelves
        ],
        total=len(shelves),
    )


@router.get(
    "/{shelf_id}",
    response_model=ShelfResponse,
    summary="Get a shelf by ID",
)
async def get_shelf(
    library_id: UUID,
    shelf_id: UUID,
    user_id: str = Depends(get_current_user_id),
    shelf_svc: ShelfService = Depends(get_shelf_service),
) -> ShelfResponse:
    try:
        shelf = await shelf_svc.get_shelf(shelf_id, user_id)
    except ShelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ShelfResponse(
        id=shelf.id,
        library_id=shelf.library_id,
        user_id=UUID(shelf.user_id),
        name=shelf.name,
        description=shelf.description,
        created_at=shelf.created_at,
        updated_at=shelf.updated_at,
    )


@router.delete(
    "/{shelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a shelf (books move to library root)",
)
async def delete_shelf(
    library_id: UUID,
    shelf_id: UUID,
    user_id: str = Depends(get_current_user_id),
    shelf_svc: ShelfService = Depends(get_shelf_service),
) -> None:
    try:
        await shelf_svc.delete_shelf(shelf_id, user_id)
    except ShelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
