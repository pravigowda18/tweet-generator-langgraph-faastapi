from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, Annotated, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import operator
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import SystemMessage, HumanMessage
from core.config import settings
import os

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key = settings.GOOGLE_API_KEY,)

os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]



class MatchData(BaseModel):
    """Structured data extracted from a sports match report."""
    data_found: bool = Field(..., description="Set to true if the match data was successfully found, otherwise false.")
    match_result: str = Field(..., description="Concise outcome of the match including the winner and margin of victory (e.g., 'India won by 7 wickets').")
    teams: str = Field(..., description="The two teams that played, formatted as 'Team A vs. Team B'.")
    score: str = Field(..., description="The final score in detail (e.g., 'IND: 251/3, AUS: 250/10').")
    match_summary: str = Field(..., description="A brief 2–3 sentence summary of how the match unfolded, mentioning key phases or performances.")
    player_of_the_match: str = Field(..., description="The name of the player who was awarded 'Player of the Match'. If not available, state 'N/A'.")
    match_keyMoment: str = Field(..., description="The single most decisive or memorable moment of the match (e.g., 'Virat Kohli's century' or 'The final over thriller').")

structured_llm = llm.with_structured_output(MatchData)

class TweetState(TypedDict):
    topic: str
    match_result: str
    match_summary: str
    match_keyMoment: str
    tweet: str
    evaluation: Literal["post", "edit", "cancel"]
    feedback: Optional[str] = None
    tweet_history: Optional[Annotated[list[str], operator.add]] = None
    feedback_history: Optional[Annotated[list[str], operator.add]] = None

def create_workflow() -> StateGraph:
    def gen_match(state: TweetState):
        print("---SEARCHING FOR MATCH DATA---")
        
        # Explicitly perform search
        search_results = search_tool.invoke({"query": state['topic']})
    
        prompt = f"""
        You are an expert sports data researcher. Your goal is to find the latest, most accurate information
        for the following sports match query: "{state['topic']}".

        Here are the search results to analyze:
        {search_results}

        Based ONLY on the information from these search results, populate all the fields in the `MatchData` schema.
        If you cannot find relevant information, set `data_found` to false and fill other fields with "Data not available".
        """

        messages = [HumanMessage(content=prompt)]
        response = structured_llm.invoke(messages)

        if not response.data_found:
            return {
                "match_result": "Match data not found online.",
                "match_summary": "Could not retrieve a summary for the requested match.",
                "match_keyMoment": "N/A"
            }

        return {
            "match_result": response.match_result,
            "match_summary": f"{response.score}. {response.match_summary} Player of the Match: {response.player_of_the_match}.",
            "match_keyMoment": response.match_keyMoment
        }

    def gen_post(state: TweetState):
        feedback_text = ""
        if state.get('feedback'):
            feedback_text = f"\nUser Feedback: \"{state['feedback']}\"\n"
            feedback_text += "Please use this feedback to regenerate the tweet."
            
        messages = [
            SystemMessage(content="""
        You are a witty, concise, and insightful sports commentator who writes engaging Twitter posts.
        Your job is to turn cricket match details into viral-worthy tweets.
        Follow these rules:
        - Keep it under 280 characters
        - Make it punchy, thought-provoking, or celebratory
        - Avoid cliches like 'What a match!' or 'Unbelievable scenes'
        - Highlight the drama and energy of the game
        - You may use emojis sparingly ⚡🔥🏏 if it adds impact
        """),
            HumanMessage(content=f"""
        Generate a tweet based on the following match details:

        Match Result: \"{state['match_result']}\"
        Match Summary: \"{state['match_summary']}\"
        Key Moment: \"{state['match_keyMoment']}\"
        
        {feedback_text}
        
        Return ONLY the tweet text, no explanations.
        """)
        ]

        response = llm.invoke(messages).content

        return {
            "tweet": response,
            "tweet_history": state.get("tweet_history", []) + [response],
            "evaluation": None
        }

    def user_feedback(state: TweetState):
        feedback_history = state.get('feedback_history', [])
        if state.get('feedback'):
            feedback_history.append(state['feedback'])

        return {
            "current_tweet": state['tweet'],
            "tweet_history": state.get('tweet_history', []),
            "feedback_history": feedback_history
        }

    def route_evaluation(state: TweetState):
        evaluation = state.get("evaluation")
        if evaluation == 'post':
            return 'post'
        elif evaluation == 'edit':
            return 'edit'
        else:
            return 'cancel'

    def tweet_post(state: TweetState):
        # This could integrate with actual Twitter API in the future
        return {"status": "Tweet posted successfully"}

    # Create graph
    graph = StateGraph(TweetState)

    # Add nodes
    graph.add_node("gen_match", gen_match)
    graph.add_node("gen_post", gen_post)
    graph.add_node('user_feedback', user_feedback)
    graph.add_node('tweet_post', tweet_post)

    # Add edges
    graph.add_edge(START, "gen_match")
    graph.add_edge("gen_match", "gen_post")
    graph.add_edge("gen_post", "user_feedback")
    graph.add_conditional_edges(
        'user_feedback',
        route_evaluation,
        {
            'post': 'tweet_post',
            'edit': 'gen_post',
            'cancel': END
        }
    )
    graph.add_edge("tweet_post", END)

    return graph.compile()