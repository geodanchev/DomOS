"""account_based_system

Revision ID: e6a58feb3c22
Revises: c6068e1a480f
Create Date: 2026-06-21 21:17:25.499658

Миграция към Account-based система:
1. Създава apartment_accounts и account_transactions таблици
2. Мигрира съществуващите данни: баланс = плащания - задължения
3. Премахва amount_paid и status от obligations
4. Преименува amount_due на amount
"""
from typing import Sequence, Union
from decimal import Decimal

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'e6a58feb3c22'
down_revision: Union[str, None] = 'c6068e1a480f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Create enum types for the new tables (only if they don't exist)
    # Check if transactiontype exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'transactiontype'
        )
    """)).scalar()
    if not result:
        postgresql.ENUM('CREDIT', 'DEBIT', name='transactiontype').create(conn)
    
    # Check if transactionreference exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'transactionreference'
        )
    """)).scalar()
    if not result:
        postgresql.ENUM('PAYMENT', 'OBLIGATION', 'ADJUSTMENT', 'MIGRATION', name='transactionreference').create(conn)
    
    # 2. Create apartment_accounts table
    op.create_table('apartment_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('apartment_id', sa.Integer(), nullable=False, comment='ID на апартамента'),
        sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00', comment='Текущ баланс в лева (отрицателен = дължи)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата на създаване'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата на последна промяна'),
        sa.ForeignKeyConstraint(['apartment_id'], ['apartments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apartment_accounts_apartment_id'), 'apartment_accounts', ['apartment_id'], unique=True)
    
    # 3. Create account_transactions table
    op.create_table('account_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='ID на сметката'),
        sa.Column('type', postgresql.ENUM('CREDIT', 'DEBIT', name='transactiontype', create_type=False), nullable=False, comment='Тип на транзакцията (credit/debit)'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Сума на транзакцията в лева'),
        sa.Column('reference_type', postgresql.ENUM('PAYMENT', 'OBLIGATION', 'ADJUSTMENT', 'MIGRATION', name='transactionreference', create_type=False), nullable=False, comment='Тип на източника (payment/obligation/adjustment)'),
        sa.Column('reference_id', sa.Integer(), nullable=True, comment='ID на свързания запис (payment_id, obligation_id и т.н.)'),
        sa.Column('balance_after', sa.Numeric(precision=10, scale=2), nullable=False, comment='Баланс на сметката след транзакцията'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание на транзакцията'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата на създаване'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата на последна промяна'),
        sa.ForeignKeyConstraint(['account_id'], ['apartment_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_account_transactions_account_id'), 'account_transactions', ['account_id'], unique=False)
    
    # 4. Migrate data: Create accounts for all apartments with calculated balance
    # Balance = sum(payments) - sum(obligations.amount_due)
    conn = op.get_bind()
    
    # Get all apartments
    apartments = conn.execute(text("SELECT id FROM apartments")).fetchall()
    
    for (apt_id,) in apartments:
        # Calculate total payments for this apartment
        payments_result = conn.execute(
            text("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE apartment_id = :apt_id"),
            {"apt_id": apt_id}
        ).scalar()
        total_payments = Decimal(str(payments_result))
        
        # Calculate total obligations for this apartment
        obligations_result = conn.execute(
            text("SELECT COALESCE(SUM(amount_due), 0) FROM obligations WHERE apartment_id = :apt_id"),
            {"apt_id": apt_id}
        ).scalar()
        total_obligations = Decimal(str(obligations_result))
        
        # Calculate balance: payments - obligations
        balance = total_payments - total_obligations
        
        # Create account for this apartment
        conn.execute(
            text("""
                INSERT INTO apartment_accounts (apartment_id, balance, created_at, updated_at)
                VALUES (:apt_id, :balance, now(), now())
            """),
            {"apt_id": apt_id, "balance": balance}
        )
        
        # Get the account ID we just created
        account_id = conn.execute(
            text("SELECT id FROM apartment_accounts WHERE apartment_id = :apt_id"),
            {"apt_id": apt_id}
        ).scalar()
        
        # Create migration transaction record
        conn.execute(
            text("""
                INSERT INTO account_transactions 
                (account_id, type, amount, reference_type, reference_id, balance_after, description, created_at, updated_at)
                VALUES (:account_id, :tx_type, :amount, 'MIGRATION', NULL, :balance, :description, now(), now())
            """),
            {
                "account_id": account_id,
                "tx_type": "CREDIT" if balance >= 0 else "DEBIT",
                "amount": abs(balance),
                "balance": balance,
                "description": f"Миграция от стара система: плащания={total_payments}, задължения={total_obligations}"
            }
        )
    
    # 5. Add amount column to obligations (copy from amount_due)
    op.add_column('obligations', sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True, comment='Сума на задължението в лева'))
    
    # Copy amount_due to amount
    conn.execute(text("UPDATE obligations SET amount = amount_due"))
    
    # Make amount NOT NULL
    op.alter_column('obligations', 'amount', nullable=False)
    
    # 6. Drop old columns from obligations
    op.drop_index(op.f('ix_obligations_status'), table_name='obligations')
    op.drop_column('obligations', 'status')
    op.drop_column('obligations', 'amount_paid')
    op.drop_column('obligations', 'amount_due')
    
    # 7. Drop legacy tables if they still exist
    # Check if monthly_charges exists before dropping
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'monthly_charges'
        )
    """)).scalar()
    
    if result:
        op.drop_index(op.f('ix_monthly_charges_apartment_id'), table_name='monthly_charges')
        op.drop_index(op.f('ix_monthly_charges_month'), table_name='monthly_charges')
        op.drop_table('monthly_charges')
    
    # Check if custom_charges exists before dropping
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'custom_charges'
        )
    """)).scalar()
    
    if result:
        op.drop_index(op.f('ix_custom_charges_apartment_id'), table_name='custom_charges')
        op.drop_table('custom_charges')


def downgrade() -> None:
    # Restore obligations columns
    op.add_column('obligations', sa.Column('amount_due', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True, comment='Дължима сума в лева'))
    op.add_column('obligations', sa.Column('amount_paid', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True, server_default='0', comment='Платена сума в лева'))
    op.add_column('obligations', sa.Column('status', postgresql.ENUM('PAID', 'PARTIAL', 'UNPAID', name='obligationstatus'), autoincrement=False, nullable=True, server_default='UNPAID', comment='Статус на задължението'))
    
    # Copy amount back to amount_due
    conn = op.get_bind()
    conn.execute(text("UPDATE obligations SET amount_due = amount, amount_paid = 0, status = 'UNPAID'"))
    
    # Make columns NOT NULL
    op.alter_column('obligations', 'amount_due', nullable=False)
    op.alter_column('obligations', 'amount_paid', nullable=False)
    op.alter_column('obligations', 'status', nullable=False)
    
    # Create index
    op.create_index(op.f('ix_obligations_status'), 'obligations', ['status'], unique=False)
    
    # Drop amount column
    op.drop_column('obligations', 'amount')
    
    # Drop account tables
    op.drop_index(op.f('ix_account_transactions_account_id'), table_name='account_transactions')
    op.drop_table('account_transactions')
    op.drop_index(op.f('ix_apartment_accounts_apartment_id'), table_name='apartment_accounts')
    op.drop_table('apartment_accounts')
    
    # Drop enum types
    sa.Enum(name='transactiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='transactionreference').drop(op.get_bind(), checkfirst=True)
