"""Initial KickNow production schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-18 15:40:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlmodel import SQLModel
import backend.app.models.schema  # noqa: F401

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    SQLModel.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    SQLModel.metadata.drop_all(bind=bind)
