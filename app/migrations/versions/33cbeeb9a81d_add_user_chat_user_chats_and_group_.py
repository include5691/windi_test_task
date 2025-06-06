"""Add user, chat, user_chats and group models

Revision ID: 33cbeeb9a81d
Revises: 
Create Date: 2025-04-05 16:43:36.923932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from argon2 import PasswordHasher

ph = PasswordHasher()

TEST_DATA = [
    {"email": "alice.wright87@example.com", "name": "Alice Wright", "password": "Zx7!pTn9vR"},
    {"email": "ben.stevens55@example.com", "name": "Ben Stevens", "password": "uJ2#kLo8bW"},
    {"email": "carla.james22@example.com", "name": "Carla James", "password": "M@5pQx3eTu"},
]

# revision identifiers, used by Alembic.
revision: str = '33cbeeb9a81d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('is_group', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('user_chats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_chats_user_id'), 'user_chats', ['user_id'], unique=False)
    # ### end Alembic commands ###

    ### create test data ###
    users_table = sa.table('users', sa.column('id'), sa.column('email'), sa.column('name'), sa.column('hashed_password'))
    user_chats_table = sa.table('user_chats', sa.column('id'), sa.column('user_id'), sa.column('chat_id'))
    chats_table = sa.table('chats', sa.column('id'), sa.column('name'), sa.column('is_group'))

    op.bulk_insert(
        users_table,
        [{
            'email': user['email'],
            'name': user['name'],
            'hashed_password': ph.hash(user['password']),
        } for user in TEST_DATA]
    )
    op.bulk_insert(
        chats_table,
        [{
            'name': f"Chat {i+1}",
            'is_group': False,
        } for i in range((len(TEST_DATA)) - 1)]
    )
    op.bulk_insert(
        user_chats_table,
        [{"user_id": 1, "chat_id": i + 1} for i in range(len(TEST_DATA) - 1)]
        + [{"user_id": i + 1, "chat_id": i} for i in range(1, len(TEST_DATA))],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_chats_user_id'), table_name='user_chats')
    op.drop_table('user_chats')
    op.drop_table('users')
    op.drop_table('chats')
    # ### end Alembic commands ###
