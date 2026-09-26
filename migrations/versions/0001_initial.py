"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "markets",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("question", sa.Text()),
        sa.Column("slug", sa.String(length=512)),
        sa.Column("condition_id", sa.String(length=256)),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("start_date", sa.String(length=64)),
        sa.Column("end_date", sa.String(length=64)),
        sa.Column("resolution_source", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("outcomes_json", sa.Text(), nullable=False),
        sa.Column("token_ids_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("market_id", sa.String(length=128), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("volume_24h", sa.Float(), nullable=False),
        sa.Column("liquidity", sa.Float(), nullable=False),
        sa.Column("yes_probability", sa.Float()),
        sa.Column("research_priority", sa.Float()),
        sa.Column("outcome_prices_json", sa.Text(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_market_snapshots_market_id", "market_snapshots", ["market_id"])
    op.create_index("ix_market_snapshots_captured_at", "market_snapshots", ["captured_at"])
    op.create_index("ix_market_snapshots_market_captured", "market_snapshots", ["market_id", "captured_at"])

    op.create_table(
        "market_resolutions",
        sa.Column("market_id", sa.String(length=128), sa.ForeignKey("markets.id"), primary_key=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_market_resolutions_resolved_at", "market_resolutions", ["resolved_at"])

    op.create_table(
        "research_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("market_id", sa.String(length=128), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("probability", sa.Float()),
        sa.Column("raw_probability", sa.Float()),
        sa.Column("calibrated_probability", sa.Float()),
        sa.Column("calibration_applied", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("market_probability", sa.Float()),
        sa.Column("edge", sa.Float()),
        sa.Column("summary", sa.Text()),
        sa.Column("key_factors_json", sa.Text(), nullable=False),
        sa.Column("counter_factors_json", sa.Text(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
        sa.Column("error", sa.Text()),
    )
    op.create_index("ix_research_runs_market_id", "research_runs", ["market_id"])
    op.create_index("ix_research_runs_created_at", "research_runs", ["created_at"])
    op.create_index("ix_research_runs_market_created", "research_runs", ["market_id", "created_at"])

    op.create_table(
        "research_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("research_run_id", sa.Integer(), sa.ForeignKey("research_runs.id"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
    )
    op.create_index("ix_research_sources_research_run_id", "research_sources", ["research_run_id"])


def downgrade() -> None:
    op.drop_index("ix_research_sources_research_run_id", table_name="research_sources")
    op.drop_table("research_sources")
    op.drop_index("ix_research_runs_market_created", table_name="research_runs")
    op.drop_index("ix_research_runs_created_at", table_name="research_runs")
    op.drop_index("ix_research_runs_market_id", table_name="research_runs")
    op.drop_table("research_runs")
    op.drop_index("ix_market_resolutions_resolved_at", table_name="market_resolutions")
    op.drop_table("market_resolutions")
    op.drop_index("ix_market_snapshots_market_captured", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_captured_at", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_market_id", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_table("markets")
