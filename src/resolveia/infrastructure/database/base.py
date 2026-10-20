"""Declarative base shared by SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for persistence-only ORM models."""
