from app.db.database import Base
from app.models.user import User
from app.models.link import Link
from app.models.analytics import Click

# Re-export Base for Alembic to easily import all models
__all__ = ["Base", "User", "Link", "Click"]
