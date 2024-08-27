"""Add Image model and relationship with User

Revision ID: ca5b788cc7fb
Revises: <revision_id>
Create Date: 2024-08-27 13:43:58.482717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ca5b788cc7fb'
down_revision: Union[str, None] = '<revision_id>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the images table
    op.create_table(
        'images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('prompt', sa.String(), nullable=False),
        sa.Column('refinedPrompt', sa.String(), nullable=True),
        sa.Column('aspectRatio', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False)
    )


def downgrade():
    # Drop the images table
    op.drop_table('images')