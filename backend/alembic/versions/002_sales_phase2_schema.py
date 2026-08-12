"""Update sales table for Phase 2 schema: Numeric money, Date sale_date, ML features & unique constraint

Revision ID: 002_sales_phase2_schema
Revises: 001_initial_schema
Create Date: 2026-08-12 21:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_sales_phase2_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update Products money columns to Numeric(10, 2)
    op.alter_column('products', 'cost_price',
               type_=sa.Numeric(precision=10, scale=2),
               existing_type=sa.Float(),
               nullable=False,
               postgresql_using='cost_price::numeric(10,2)')
    op.alter_column('products', 'selling_price',
               type_=sa.Numeric(precision=10, scale=2),
               existing_type=sa.Float(),
               nullable=False,
               postgresql_using='selling_price::numeric(10,2)')

    # 2. Update Sales table columns
    op.alter_column('sales', 'sale_date',
               type_=sa.Date(),
               existing_type=sa.DateTime(timezone=True),
               nullable=False,
               postgresql_using='sale_date::date')
    op.alter_column('sales', 'total_amount',
               type_=sa.Numeric(precision=10, scale=2),
               existing_type=sa.Float(),
               nullable=False,
               postgresql_using='total_amount::numeric(10,2)')

    op.add_column('sales', sa.Column('selling_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))
    op.add_column('sales', sa.Column('promotion', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sales', sa.Column('holiday', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sales', sa.Column('festival', sa.String(length=100), nullable=True))
    op.add_column('sales', sa.Column('stock_available', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('sales', sa.Column('is_stockout', sa.Boolean(), nullable=True))

    op.create_index(op.f('ix_sales_is_stockout'), 'sales', ['is_stockout'], unique=False)
    op.create_index('idx_sales_business_product_date', 'sales', ['business_id', 'product_id', 'sale_date'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_sales_business_product_date', table_name='sales')
    op.drop_index(op.f('ix_sales_is_stockout'), table_name='sales')
    op.drop_column('sales', 'is_stockout')
    op.drop_column('sales', 'stock_available')
    op.drop_column('sales', 'festival')
    op.drop_column('sales', 'holiday')
    op.drop_column('sales', 'promotion')
    op.drop_column('sales', 'selling_price')

    op.alter_column('sales', 'total_amount',
               type_=sa.Float(),
               existing_type=sa.Numeric(precision=10, scale=2),
               nullable=False)
    op.alter_column('sales', 'sale_date',
               type_=sa.DateTime(timezone=True),
               existing_type=sa.Date(),
               nullable=False)
    op.alter_column('products', 'selling_price',
               type_=sa.Float(),
               existing_type=sa.Numeric(precision=10, scale=2),
               nullable=False)
    op.alter_column('products', 'cost_price',
               type_=sa.Float(),
               existing_type=sa.Numeric(precision=10, scale=2),
               nullable=False)
