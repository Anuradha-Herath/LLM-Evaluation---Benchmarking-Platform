"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-21 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index(op.f('ix_datasets_id'), 'datasets', ['id'], unique=False)
    op.create_index(op.f('ix_datasets_version'), 'datasets', ['version'], unique=True)

    # 2. dataset_cases
    op.create_table(
        'dataset_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('input', sa.Text(), nullable=False),
        sa.Column('expected_behavior', sa.Text(), nullable=False),
        sa.Column('reference_answer', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_cases_case_id'), 'dataset_cases', ['case_id'], unique=False)
    op.create_index(op.f('ix_dataset_cases_category'), 'dataset_cases', ['category'], unique=False)
    op.create_index(op.f('ix_dataset_cases_dataset_id'), 'dataset_cases', ['dataset_id'], unique=False)

    # 3. prompts
    op.create_table(
        'prompts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_version'), 'prompts', ['version'], unique=False)

    # 4. model_configurations
    op.create_table(
        'model_configurations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('top_p', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('frequency_penalty', sa.Float(), nullable=False),
        sa.Column('presence_penalty', sa.Float(), nullable=False),
        sa.Column('extra_params', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_configurations_model'), 'model_configurations', ['model'], unique=False)
    op.create_index(op.f('ix_model_configurations_provider'), 'model_configurations', ['provider'], unique=False)

    # 5. evaluation_runs
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=True),
        sa.Column('prompt_id', sa.String(length=36), nullable=True),
        sa.Column('model_config_id', sa.String(length=36), nullable=True),
        sa.Column('dataset_version', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('total_cases', sa.Integer(), nullable=False),
        sa.Column('passed_cases', sa.Integer(), nullable=False),
        sa.Column('failed_cases', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_config_id'], ['model_configurations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )
    op.create_index(op.f('ix_evaluation_runs_dataset_version'), 'evaluation_runs', ['dataset_version'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_model'), 'evaluation_runs', ['model'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_provider'), 'evaluation_runs', ['provider'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_run_id'), 'evaluation_runs', ['run_id'], unique=True)
    op.create_index(op.f('ix_evaluation_runs_status'), 'evaluation_runs', ['status'], unique=False)

    # 6. evaluation_results
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_results_case_id'), 'evaluation_results', ['case_id'], unique=False)
    op.create_index(op.f('ix_evaluation_results_run_id'), 'evaluation_results', ['run_id'], unique=False)

    # 7. metric_results
    op.create_table(
        'metric_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('result_id', sa.String(length=36), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_version', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('judge_model', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['result_id'], ['evaluation_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metric_results_metric_name'), 'metric_results', ['metric_name'], unique=False)
    op.create_index(op.f('ix_metric_results_result_id'), 'metric_results', ['result_id'], unique=False)


def downgrade() -> None:
    op.drop_table('metric_results')
    op.drop_table('evaluation_results')
    op.drop_table('evaluation_runs')
    op.drop_table('model_configurations')
    op.drop_table('prompts')
    op.drop_table('dataset_cases')
    op.drop_table('datasets')
