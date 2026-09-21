from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.schemas.user import UserCreate
from app.models.user import User
from app.repositories.user import UserRepository
from app.core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> User:
        user_exists = await self.repo.get_by_email(email=user_in.email)
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            password_hash=hashed_password
        )
        return await self.repo.create(user)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
