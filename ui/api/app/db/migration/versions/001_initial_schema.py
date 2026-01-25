"""
First migration: Create initial tables (User and Post)

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-24

This is an example migration. Replace with your actual migration after running:
alembic revision --autogenerate -m "Initial schema"
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade() -> None:
    """Upgrade database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Index('ix_users_username', 'username'),
        sa.Index('ix_users_email', 'email'),
        sa.Index('ix_users_created_at', 'created_at'),
    )
    
    # Create posts table
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='fk_posts_author_id'),
        sa.Index('ix_posts_title', 'title'),
        sa.Index('ix_posts_author_id', 'author_id'),
        sa.Index('ix_posts_created_at', 'created_at'),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop posts table
    op.drop_table('posts')
    
    # Drop users table
    op.drop_table('users')
