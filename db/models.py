import uuid
from sqlalchemy import Column, UUID, String, TIMESTAMP, text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from db.connection import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    
    workflows = relationship("Workflow", back_populates="owner")
    
    
    
class Workflow(Base):
    __tablename__ = "workflows"

    thread_id = Column(String, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    state = Column(JSONB, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    last_update_time = Column(TIMESTAMP, server_default=text("now()"), onupdate=text("now()"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    
    owner = relationship("User", back_populates="workflows")