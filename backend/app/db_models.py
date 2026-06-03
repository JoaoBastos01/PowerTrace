"""SQLAlchemy ORM models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    owner_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Generation(Base):
    __tablename__ = "generations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    project_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    input_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    dxf_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    json_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    

    
