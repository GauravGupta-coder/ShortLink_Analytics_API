from app.db.database import get_db
from app.db.redis import get_redis

# Re-exporting dependencies so they can be imported from app.api.dependencies
__all__ = ["get_db", "get_redis"]
