from typing import List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    
class UserShow(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
        
        
class Token(BaseModel):
    access_token: str
    token_type: str
    