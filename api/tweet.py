from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import uuid4

from db.connection import get_db
from db.models import Workflow
from schemas.tweet import TweetRequest, TweetResponse, FeedbackRequest, GetTweet
from schemas.user import UserShow
from security.Oauth import get_current_user
from langgraph.graph import StateGraph, START, END
from core.tweet_workflow import create_workflow

router = APIRouter(prefix="/tweet", tags=["tweet"])

@router.post("/generate", response_model=TweetResponse)
async def generate_tweet(
    request: TweetRequest,
    db: Session = Depends(get_db),
    current_user: UserShow = Depends(get_current_user)
):
    
    
    # Create initial state
    initial_state = {
        'topic': request.topic,
        'tweet_history': [],
        'feedback_history': []
    }
    
    # Generate thread_id
    thread_id = str(uuid4())
    
    # Initialize workflow
    workflow = create_workflow()
    
    # Run workflow until user_feedback

    state = workflow.invoke(
        initial_state,
        config={"configurable": {"interrupt_before": ["user_feedback"]}}
    )
    
    # Create workflow record in database
    db_workflow = Workflow(
        thread_id=thread_id,
        user_id=current_user.user_id,
        state=state,  # Remove .state as invoke() returns the state directly
        is_completed=False
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    return TweetResponse(
        thread_id=thread_id,
        current_tweet=state['tweet'],
        tweet_history=state.get('tweet_history', []),
        feedback_history=state.get('feedback_history', [])
    )

@router.post("/{thread_id}/feedback", response_model=TweetResponse)
async def provide_feedback(
    thread_id: str,
    feedback_request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: UserShow = Depends(get_current_user)
):
    # Get workflow from database
    workflow_state = db.query(Workflow).filter(
        Workflow.thread_id == thread_id,
        Workflow.user_id == current_user.user_id
    ).first()
    
    print("Workflow State:", workflow_state)
    
    if not workflow_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow_state.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow already completed"
        )
    
    # Update state with feedback
    state_dict = workflow_state.state
    state_dict['feedback'] = feedback_request.feedback
    state_dict['evaluation'] = feedback_request.evaluation
    
    # Continue workflow
    workflow = create_workflow()
    result = workflow.invoke(state_dict,
                             config={"configurable": {"interrupt_before": ["user_feedback"]}}
                             )
    
    # Update workflow in database
    workflow_state.state = result
    workflow_state.is_completed = feedback_request.evaluation in ['post', 'cancel']
    db.commit()
    
    return TweetResponse(
    thread_id=thread_id,
    current_tweet=result['tweet'],   # ✅ access dict keys with []
    tweet_history=result.get('tweet_history', []),
    feedback_history=result.get('feedback_history', [])
    )
    
    
@router.get('/workflow',response_model=GetTweet)
async def user_workflow(
    db: Session = Depends(get_db),
    current_user: UserShow = Depends(get_current_user)
    ):
    
    tweets = db.query(Workflow).filter(Workflow.user_id == current_user.user_id).all
    print(tweets)
    
    
    return GetTweet(
        thread_id = tweets.thread_id
    )



@router.get("/", response_model=Dict[str, Any])
def get_user_workflows(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserShow = Depends(get_current_user)
):
    """
    Get all tweets for the current user, with their thread_id and last updated time.
    """
    try:
        # This service call is assumed to return a dict with a list of Workflow objects and a total count
        # e.g., {'workflows': [WorkflowModel, ...], 'total': 15}
        workflow_data = db.query(Workflow).filter(Workflow.user_id == current_user.user_id).all
        
        tweets_summary = []
        for workflow in workflow_data.get("workflows", []):
            # The state field is JSONB, which is a dict in Python
            state = workflow.state if workflow.state else {}
            tweets_summary.append({
                "thread_id": workflow.thread_id,
                "last_updated": str(workflow.last_update_time),
                "tweet": state.get("tweet")
            })

        response_data = {
            "tweets": tweets_summary,
            "total": len(workflow_data)
        }
        
        return {
            "success": True,
            "data": response_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflows: {str(e)}"
        )
