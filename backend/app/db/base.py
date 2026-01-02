"""
SQLAlchemy declarative base and common model mixins.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base, declared_attr


class CustomBase:
    """
    Custom base class with common functionality for all models.
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        Converts CamelCase to snake_case.
        """
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.
        Excludes SQLAlchemy internal attributes.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


Base = declarative_base(cls=CustomBase)


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    """
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
