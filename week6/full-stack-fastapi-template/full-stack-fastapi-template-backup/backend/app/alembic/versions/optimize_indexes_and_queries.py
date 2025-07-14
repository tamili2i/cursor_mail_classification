"""
Add optimal indexes for task, team member, and project queries
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Task indexes
    op.create_index('ix_task_project_id', 'task', ['project_id'])
    op.create_index('ix_task_assignee_id', 'task', ['assignee_id'])
    op.create_index('ix_task_status', 'task', ['status'])
    op.create_index('ix_task_due_date', 'task', ['due_date'])
    op.create_index('ix_task_parent_task_id', 'task', ['parent_task_id'])
    # TeamMember composite index
    op.create_index('ix_teammember_team_user', 'teammember', ['team_id', 'user_id'])
    # Project index
    op.create_index('ix_project_team_id', 'project', ['team_id'])

def downgrade():
    op.drop_index('ix_task_project_id', table_name='task')
    op.drop_index('ix_task_assignee_id', table_name='task')
    op.drop_index('ix_task_status', table_name='task')
    op.drop_index('ix_task_due_date', table_name='task')
    op.drop_index('ix_task_parent_task_id', table_name='task')
    op.drop_index('ix_teammember_team_user', table_name='teammember')
    op.drop_index('ix_project_team_id', table_name='project') 