"""User persistence and authentication queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import User
from app.schemas.auth import RegisterRequest
from app.security import hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == normalize_email(email))
        return self.db.scalar(statement)

    def create(self, request: RegisterRequest) -> User:
        user = User(
            email=normalize_email(str(request.email)),
            name=request.name,
            password_hash=hash_password(request.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
