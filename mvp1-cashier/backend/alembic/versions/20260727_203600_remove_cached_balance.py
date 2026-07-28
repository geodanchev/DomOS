"""Remove cached balance from apartment_accounts.

Revision ID: g2h3i4j5k6l7
Revises: f7g8h9i0j1k2
Create Date: 2026-07-27 20:36:00.000000

ARCHITECTURE CHANGE: Remove cached balance anti-pattern.

Changes:
- Remove `balance` column from `apartment_accounts` table
- Make `balance_after` nullable in `account_transactions` table

After this migration:
- Balance is calculated dynamically as: sum(active payments) - sum(obligations)
- No cached balance means no sync issues with direct DB operations
- AccountTransaction.balance_after is kept for historical audit records but not calculated for new transactions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f7g8h9i0j1k2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove cached balance column and make balance_after nullable."""
    
    # 1. Make balance_after nullable in account_transactions
    # This allows new transactions to not store balance (since it's calculated dynamically)
    op.alter_column(
        'account_transactions',
        'balance_after',
        existing_type=sa.Numeric(10, 2),
        nullable=True,
        comment='Баланс на сметката след транзакцията (legacy, за одит)'
    )
    
    # 2. Remove balance column from apartment_accounts
    # Balance is now calculated dynamically from payments and obligations
    op.drop_column('apartment_accounts', 'balance')
    
    print("Migration complete: Removed cached balance column.")
    print("Balance is now calculated dynamically as: sum(active payments) - sum(obligations)")


def downgrade() -> None:
    """Restore cached balance column (data will need manual recalculation)."""
    
    # 1. Re-add balance column to apartment_accounts
    op.add_column(
        'apartment_accounts',
        sa.Column(
            'balance',
            sa.Numeric(10, 2),
            nullable=False,
            server_default='0.00',
            comment='Текущ баланс в лева (отрицателен = дължи)'
        )
    )
    
    # 2. Make balance_after non-nullable again
    # NOTE: This will fail if there are NULL values in balance_after
    # You may need to update NULL values to 0 before running this
    op.alter_column(
        'account_transactions',
        'balance_after',
        existing_type=sa.Numeric(10, 2),
        nullable=False,
        comment='Баланс на сметката след транзакцията'
    )
    
    # Remove server default after column is added
    op.alter_column(
        'apartment_accounts',
        'balance',
        server_default=None
    )
    
    print("Downgrade complete: Restored cached balance column.")
    print("WARNING: Balance values need to be recalculated manually!")
