"""job exception text

Revision ID: 9a68c1d7c904
Revises: a7750480c429
Create Date: 2022-08-30 16:56:03.927563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a68c1d7c904'
down_revision = 'a7750480c429'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('exception_text', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('job', 'exception_text')
    # ### end Alembic commands ###