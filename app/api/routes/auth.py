from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate
from app.schemas.token import Token
from app.services.user import UserService
from app.core.security import create_access_token
from app.core.config import settings
from app.core.rate_limit import RateLimiter

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_REGISTER, seconds=60))])
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Registers a new user in the ShortLink Analytics system.

    - Requires a unique email address.
    - Passwords are automatically hashed via bcrypt.
    - Fails if the email is already registered.
    """
    user_service = UserService(db)
    return await user_service.register_user(user_in)

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_LOGIN, seconds=60))])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Authenticates a user and returns a JSON Web Token (JWT).

    - Use this token in the `Authorization: Bearer <token>` header for protected endpoints.
    - Subject to IP-based rate limiting to prevent brute-force attacks.
    """
    user_service = UserService(db)
    user = await user_service.authenticate_user(email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieves the currently authenticated user's profile information.
    """
    return current_user
