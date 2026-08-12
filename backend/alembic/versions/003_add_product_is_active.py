"""Add is_active column to products table for soft deactivation

Revision ID: 003_add_product_is_active
Revises: 002_sales_phase2_schema
Create Date: 2026-08-12 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_product_is_active'
down_revision: Union[str, None] = '002_sales_phase2_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('products', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.create_index(op.f('ix_products_is_active'), 'products', ['is_active'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_products_is_active'), table_name='products')
    op.drop_column('products', 'is_active')
