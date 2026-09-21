from pydantic import BaseModel
from typing import List

class AnalyticsResponse(BaseModel):
    link_id: int
    total_clicks: int
    clicks_today: int
    clicks_last_7_days: int
    clicks_last_30_days: int
    recent_clicks: List[dict]  # list of recent click data

class TimelineResponse(BaseModel):
    link_id: int
    timeline: List[dict]  # List of {"date": "YYYY-MM-DD", "clicks": int}
