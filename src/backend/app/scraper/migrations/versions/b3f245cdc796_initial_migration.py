"""Initial migration

Revision ID: b3f245cdc796
Revises: 
Create Date: 2022-08-13 07:11:34.942801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f245cdc796'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rtpi_store_id',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.BigInteger(), nullable=True),
    sa.Column('store_name', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('store_name')
    )
    op.create_index(op.f('ix_rtpi_store_id_id'), 'rtpi_store_id', ['id'], unique=False)
    op.create_index(op.f('ix_rtpi_store_id_store_id'), 'rtpi_store_id', ['store_id'], unique=False)
    op.create_table('rtpiprice',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('web_price_id', sa.BigInteger(), nullable=True),
    sa.Column('date_observe', sa.TIMESTAMP(), nullable=True),
    sa.Column('stock_status', sa.Text(), nullable=True),
    sa.Column('current_price', sa.BigInteger(), nullable=True),
    sa.Column('crosssed_price', sa.BigInteger(), nullable=True),
    sa.Column('contributor_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('web_price_id', 'date_observe', name='web_price_id_date_observe_unique')
    )
    op.create_index(op.f('ix_rtpiprice_id'), 'rtpiprice', ['id'], unique=False)
    op.create_index(op.f('ix_rtpiprice_stock_status'), 'rtpiprice', ['stock_status'], unique=False)
    op.create_index(op.f('ix_rtpiprice_web_price_id'), 'rtpiprice', ['web_price_id'], unique=False)
    op.create_table('rtpipricepage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('web_price_id', sa.BigInteger(), nullable=True),
    sa.Column('price_name', sa.Text(), nullable=True),
    sa.Column('price_url', sa.Text(), nullable=True),
    sa.Column('date_add', sa.TIMESTAMP(), nullable=True),
    sa.Column('date_last_in_stock', sa.TIMESTAMP(), nullable=True),
    sa.Column('rosstat_id', sa.Integer(), nullable=True),
    sa.Column('contributor_id', sa.Integer(), nullable=True),
    sa.Column('store_id', sa.Integer(), nullable=True),
    sa.Column('date_last_crawl', sa.TIMESTAMP(), nullable=True),
    sa.Column('city_code', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rtpipricepage_id'), 'rtpipricepage', ['id'], unique=False)
    op.create_index(op.f('ix_rtpipricepage_web_price_id'), 'rtpipricepage', ['web_price_id'], unique=True)
    op.create_table('rtpiproductname',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('web_price_id', sa.BigInteger(), nullable=True),
    sa.Column('product_name', sa.Text(), nullable=True),
    sa.Column('contributor_id', sa.Integer(), nullable=True),
    sa.Column('moment', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('web_price_id', 'moment', name='web_price_id_moment_unique')
    )
    op.create_index(op.f('ix_rtpiproductname_id'), 'rtpiproductname', ['id'], unique=False)
    op.create_index(op.f('ix_rtpiproductname_web_price_id'), 'rtpiproductname', ['web_price_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rtpiproductname_web_price_id'), table_name='rtpiproductname')
    op.drop_index(op.f('ix_rtpiproductname_id'), table_name='rtpiproductname')
    op.drop_table('rtpiproductname')
    op.drop_index(op.f('ix_rtpipricepage_web_price_id'), table_name='rtpipricepage')
    op.drop_index(op.f('ix_rtpipricepage_id'), table_name='rtpipricepage')
    op.drop_table('rtpipricepage')
    op.drop_index(op.f('ix_rtpiprice_web_price_id'), table_name='rtpiprice')
    op.drop_index(op.f('ix_rtpiprice_stock_status'), table_name='rtpiprice')
    op.drop_index(op.f('ix_rtpiprice_id'), table_name='rtpiprice')
    op.drop_table('rtpiprice')
    op.drop_index(op.f('ix_rtpi_store_id_store_id'), table_name='rtpi_store_id')
    op.drop_index(op.f('ix_rtpi_store_id_id'), table_name='rtpi_store_id')
    op.drop_table('rtpi_store_id')
    # ### end Alembic commands ###
