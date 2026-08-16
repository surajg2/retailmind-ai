"""Phase 4B: Forecast persistence schema

Revision ID: 004_forecast_persistence
Revises: 003_add_product_is_active
Create Date: 2026-08-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_forecast_persistence'
down_revision = '003_add_product_is_active'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new columns (initially nullable to handle existing rows)
    op.add_column('predictions', sa.Column('forecast_date', sa.Date(), nullable=True))
    op.add_column('predictions', sa.Column('predicted_units', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('predictions', sa.Column('model_name', sa.String(length=50), nullable=False, server_default='XGBoost'))
    op.add_column('predictions', sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('predictions', sa.Column('training_cutoff_date', sa.Date(), nullable=True))
    op.add_column('predictions', sa.Column('horizon_days', sa.Integer(), nullable=False, server_default='7'))
    op.add_column('predictions', sa.Column('actual_units', sa.Numeric(precision=10, scale=2), nullable=True))

    # 2. Populate new columns for any pre-existing rows
    op.execute("UPDATE predictions SET forecast_date = CAST(prediction_date AS DATE) WHERE forecast_date IS NULL AND prediction_date IS NOT NULL")
    op.execute("UPDATE predictions SET predicted_units = CAST(predicted_demand AS NUMERIC(10, 2)) WHERE predicted_units IS NULL AND predicted_demand IS NOT NULL")
    op.execute("UPDATE predictions SET training_cutoff_date = COALESCE(forecast_date, CURRENT_DATE) WHERE training_cutoff_date IS NULL")

    # Fallbacks for any remaining NULLs
    op.execute("UPDATE predictions SET forecast_date = CURRENT_DATE WHERE forecast_date IS NULL")
    op.execute("UPDATE predictions SET predicted_units = 0.00 WHERE predicted_units IS NULL")

    # 3. Alter columns to NOT NULL
    op.alter_column('predictions', 'forecast_date', nullable=False)
    op.alter_column('predictions', 'predicted_units', nullable=False)
    op.alter_column('predictions', 'training_cutoff_date', nullable=False)

    # 4. Drop legacy columns
    op.drop_column('predictions', 'predicted_demand')
    op.drop_column('predictions', 'prediction_date')

    # 5. Create indexes and unique constraint
    op.create_index(op.f('ix_predictions_forecast_date'), 'predictions', ['forecast_date'], unique=False)
    op.create_index(
        'idx_predictions_business_product_date_version',
        'predictions',
        ['business_id', 'product_id', 'forecast_date', 'model_version'],
        unique=True
    )


def downgrade() -> None:
    # 1. Drop indexes
    op.drop_index('idx_predictions_business_product_date_version', table_name='predictions')
    op.drop_index(op.f('ix_predictions_forecast_date'), table_name='predictions')

    # 2. Add legacy columns back
    op.add_column('predictions', sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('predictions', sa.Column('predicted_demand', sa.Float(), nullable=True))

    # Populate legacy columns
    op.execute("UPDATE predictions SET prediction_date = CAST(forecast_date AS TIMESTAMP WITH TIME ZONE)")
    op.execute("UPDATE predictions SET predicted_demand = CAST(predicted_units AS FLOAT)")

    # 3. Drop new columns
    op.drop_column('predictions', 'actual_units')
    op.drop_column('predictions', 'horizon_days')
    op.drop_column('predictions', 'training_cutoff_date')
    op.drop_column('predictions', 'generated_at')
    op.drop_column('predictions', 'model_name')
    op.drop_column('predictions', 'predicted_units')
    op.drop_column('predictions', 'forecast_date')
