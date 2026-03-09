"""fix_rental_repair_optinal_pri_key

Revision ID: 2c30fad835d9
Revises: 5a868649d90b
Create Date: 2026-02-19 20:53:13.040341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2c30fad835d9'
down_revision: Union[str, Sequence[str], None] = '5a868649d90b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('rental', 'rental_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    op.alter_column('repair', 'repair_id',
                    existing_type=sa.Integer(), 
                    nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('rental', 'rental_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    op.alter_column('repair', 'repair_id',
                    existing_type=sa.Integer(),
                    nullable=True)
