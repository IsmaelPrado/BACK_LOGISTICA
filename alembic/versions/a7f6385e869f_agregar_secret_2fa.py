"""Agregar secret_2fa

Revision ID: a7f6385e869f
Revises: 
Create Date: 2025-09-21 13:55:01.959806

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7f6385e869f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema: solo agrega la columna secret_2fa."""
    op.add_column(
        'usuarios',
        sa.Column('secret_2fa', sa.String(length=64), nullable=False, server_default="''")
    )


def downgrade() -> None:
    """Downgrade schema: elimina la columna secret_2fa."""
    op.drop_column('usuarios', 'secret_2fa')
