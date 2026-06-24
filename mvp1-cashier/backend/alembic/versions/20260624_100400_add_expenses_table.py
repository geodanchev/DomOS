"""add expenses table

Revision ID: a1b2c3d4e5f6
Revises: e6a58feb3c22
Create Date: 2026-06-24 10:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e6a58feb3c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create expenses table for tracking building fund expenses."""
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('expense_type', sa.Enum(
            'repair', 'maintenance', 'utility', 'administrative',
            'cleaning', 'elevator', 'security', 'insurance', 'other',
            name='expensetype'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'pending', 'paid', 'cancelled',
            name='expensestatus'
        ), nullable=False),
        sa.Column('expense_date', sa.DateTime(), nullable=False),
        sa.Column('paid_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('vendor', sa.String(255), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)


def downgrade() -> None:
    """Drop expenses table."""
    op.drop_index(op.f('ix_expenses_id'), table_name='expenses')
    op.drop_table('expenses')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS expensetype')
    op.execute('DROP TYPE IF EXISTS expensestatus')
