"""
Auth endpoints — register and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service
from app.api.v1.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.service.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = await auth_svc.register(
            email=body.email,
            username=body.username,
            password=body.password,
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UsernameAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
        token=TokenResponse(access_token=token),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
)
async def login(
    body: LoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = await auth_svc.login(
            email=body.email,
            password=body.password,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )

    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
        token=TokenResponse(access_token=token),
    )
