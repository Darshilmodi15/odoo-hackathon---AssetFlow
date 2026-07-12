"""add allocation transfer and booking workflows

Revision ID: 7086c3895342
Revises: 20260712_0001
Create Date: 2026-07-12 13:14:45.091450

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "7086c3895342"
down_revision: Union[str, None] = "20260712_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This revision was already present as an empty no-op migration.
    pass


def downgrade() -> None:
    pass
