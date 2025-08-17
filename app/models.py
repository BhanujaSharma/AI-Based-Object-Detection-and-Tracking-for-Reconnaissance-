# app/models.py
from pydantic import BaseModel
from typing import List

class User(BaseModel):
    username: str
    password: str  # plain password for registration only
    role: str      # admin | zone_officer | viewer
    zones: List[str]
