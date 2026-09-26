"""${message}"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

${up_revision = repr(up_revision) if up_revision else None}
${down_revision = repr(down_revision) if down_revision else None}
${branch_labels = repr(branch_labels) if branch_labels else None}
${depends_on = repr(depends_on) if depends_on else None}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
