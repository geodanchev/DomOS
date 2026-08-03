"""Add user profile fields: email, phone, avatar_url.

Revision ID: h8i9j0k1l2m3
Revises: g2h3i4j5k6l7
Create Date: 2026-08-03 22:07:00.000000

Адд нови полета за потребителски профил:
- email: Email адрес за нотификации (уникален)
- phone: Телефонен номер
- avatar_url: URL към профилна снимка
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g2h3i4j5k6l7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email, phone, and avatar_url columns to users table."""
    # Add email column (unique, indexed)
    op.add_column(
        'users',
        sa.Column(
            'email',
            sa.String(255),
            nullable=True,
            comment='Email адрес за нотификации'
        )
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Add phone column
    op.add_column(
        'users',
        sa.Column(
            'phone',
            sa.String(20),
            nullable=True,
            comment='Телефонен номер'
        )
    )
    
    # Add avatar_url column
    op.add_column(
        'users',
        sa.Column(
            'avatar_url',
            sa.String(500),
            nullable=True,
            comment='URL към профилна снимка'
        )
    )


def downgrade() -> None:
    """Remove email, phone, and avatar_url columns from users table."""
    op.drop_index('ix_users_email', table_name='users')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'email')
