"""Add Trainee model

Revision ID: e62ef014f94b
Revises: 063384b146fa
Create Date: 2025-07-02 15:31:52.617531
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e62ef014f94b'
down_revision = '063384b146fa'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'trainee',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trainer_unit_id', sa.Integer(), sa.ForeignKey('trainer_unit.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('grade', sa.String(length=10), nullable=False)
    )

def downgrade():
    op.drop_table('trainee')