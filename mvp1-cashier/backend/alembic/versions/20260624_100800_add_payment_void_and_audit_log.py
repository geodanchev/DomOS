"""Add payment void fields and audit_logs table.

Revision ID: f7g8h9i0j1k2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 10:08:00.000000

Changes:
- Add status, voided_at, voided_by_id, void_reason fields to payments table
- Create audit_logs table for immutable audit trail
- Add VOID to transaction_reference enum
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f7g8h9i0j1k2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 1. Add payment void fields ===
    
    # Add status column with default 'active'
    op.add_column('payments', sa.Column(
        'status',
        sa.String(20),
        nullable=False,
        server_default='active',
        comment='Статус: active, voided, refunded'
    ))
    
    # Add voided_at column
    op.add_column('payments', sa.Column(
        'voided_at',
        sa.DateTime(),
        nullable=True,
        comment='Кога е анулирано плащането'
    ))
    
    # Add voided_by_id column with foreign key
    op.add_column('payments', sa.Column(
        'voided_by_id',
        sa.Integer(),
        nullable=True,
        comment='ID на потребителя анулирал плащането'
    ))
    op.create_foreign_key(
        'fk_payments_voided_by_id',
        'payments', 'users',
        ['voided_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add void_reason column
    op.add_column('payments', sa.Column(
        'void_reason',
        sa.Text(),
        nullable=True,
        comment='Причина за анулиране (задължително)'
    ))
    
    # Add index on status for filtering
    op.create_index('ix_payments_status', 'payments', ['status'])
    
    # === 2. Create audit_logs table ===
    
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True,
                  comment='Exact timestamp when action occurred'),
        sa.Column('action', sa.String(100), nullable=False, index=True,
                  comment='Type of action performed'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='User who performed the action'),
        sa.Column('user_email', sa.String(255), nullable=True,
                  comment='Email at time of action (denormalized)'),
        sa.Column('entity_type', sa.String(100), nullable=True, index=True,
                  comment='Type of entity affected'),
        sa.Column('entity_id', sa.Integer(), nullable=True, index=True,
                  comment='ID of affected entity'),
        sa.Column('apartment_id', sa.Integer(), sa.ForeignKey('apartments.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Apartment context if applicable'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Human-readable description'),
        sa.Column('state_before', sa.JSON(), nullable=True,
                  comment='State before action'),
        sa.Column('state_after', sa.JSON(), nullable=True,
                  comment='State after action'),
        sa.Column('metadata', sa.JSON(), nullable=True,
                  comment='Additional context'),
        sa.Column('ip_address', sa.String(45), nullable=True,
                  comment='IP address'),
        sa.Column('is_critical', sa.Boolean(), nullable=False, default=False, index=True,
                  comment='Critical action flag'),
    )
    
    # === 3. Update transaction_reference enum to add VOID ===
    # Note: For SQLite (used in tests), we use String columns not real ENUMs
    # For PostgreSQL, we would need to alter the enum type
    # The enum is stored as String in current implementation, so no migration needed


def downgrade() -> None:
    # === Remove audit_logs table ===
    op.drop_table('audit_logs')
    
    # === Remove payment void fields ===
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_constraint('fk_payments_voided_by_id', 'payments', type_='foreignkey')
    op.drop_column('payments', 'void_reason')
    op.drop_column('payments', 'voided_by_id')
    op.drop_column('payments', 'voided_at')
    op.drop_column('payments', 'status')
