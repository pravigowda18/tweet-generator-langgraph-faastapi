from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from uuid import UUID

class WorkflowStart(BaseModel):
    topic: str = Field(..., description="The topic for the tweet.")

class WorkflowStateResponse(BaseModel):
    workflow_id: UUID
    user_id: UUID
    topic: str
    match_result: Optional[str] = None
    match_summary: Optional[str] = None
    match_keyMoment: Optional[str] = None
    tweet: Optional[str] = None
    evaluation: Optional[Literal["post", "edit", "cancel"]] = None
    feedback: Optional[str] = None
    is_completed: bool

class WorkflowHumanInput(BaseModel):
    evaluation: Literal["post", "edit", "cancel"] = Field(..., description="User's decision on the generated tweet.")
    feedback: Optional[str] = Field(None, description="Additional feedback for the AI.")

class TweetRequest(BaseModel):
    topic: str = Field(..., description="Topic or match details to generate tweet about")

class TweetResponse(BaseModel):
    thread_id: str
    current_tweet: str
    tweet_history: List[str]
    feedback_history: List[str]

class FeedbackRequest(BaseModel):
    feedback: Optional[str] = None
    evaluation: str = Field(..., description="Must be one of: post, edit, cancel")
    
    
class GetTweet(BaseModel):
    thread_id: str
    tweet: str
    last_update_time: str
    
