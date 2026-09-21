from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from app.db.database import Base

class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), index=True, nullable=False)
    clicked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)
    device_type = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_clicks_link_id_clicked_at", "link_id", "clicked_at"),
    )
