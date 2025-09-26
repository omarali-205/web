# backend/models.py
from pydantic import BaseModel
from typing import Optional

class ResourceIn(BaseModel):
    url: str
    section_name: str
    level: Optional[str] = None

class ResourceOut(BaseModel):
    id: str
    url: str
    title: str
    description: Optional[str]
    thumbnail: Optional[str]
    level: Optional[str]
    similarity: Optional[float]
    suitable: Optional[bool]
