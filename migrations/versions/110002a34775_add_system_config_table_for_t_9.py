"""Add system_config table for T-9

Revision ID: 110002a34775
Revises: a5343bafda05
Create Date: 2025-06-15 14:57:47.440700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '110002a34775'
down_revision: Union[str, None] = 'a5343bafda05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create system_config table
    op.create_table('system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=20), nullable=False, default='string'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, default='general'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_readonly', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop system_config table
    op.drop_index(op.f('ix_system_config_key'), table_name='system_config')
    op.drop_table('system_config')
