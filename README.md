# 🚀 Tweeter: AI Sports Tweet Generator

**Tweeter** is a sophisticated, AI-powered backend built with FastAPI that generates creative, context-aware sports tweets. It uses a stateful, interactive **LangGraph** workflow, allowing users to provide a topic (like a match name), receive an AI-generated tweet, and intelligently refine it with feedback until it's perfect.

The entire system is built on a secure, scalable backend featuring JWT authentication, a PostgreSQL-compatible database, and a clear separation of concerns.

## ✨ Key Features

* **Interactive AI Workflow:** Built with **LangGraph**, the AI doesn't just give a one-shot answer. It moves through a state machine: searching for match data, drafting a tweet, and *pausing* to wait for user feedback ("edit," "post," or "cancel").
* **Stateful Conversations:** Each tweet-generation process is a unique, stateful thread. The entire workflow state is saved as a `JSONB` object in the database, allowing users to pause and resume at any time.
* **Web-Augmented Generation:** Uses **Tavily Search** to find real-time sports match data (scores, key moments, summaries) *before* generating a tweet.
* **Structured AI Output:** Leverages **Google Gemini** and Pydantic schemas to extract structured data from web searches, ensuring reliable information for the tweet generator.
* **Secure Authentication:** Complete, token-based authentication using **FastAPI**, **OAuth2**, and **JWT**. All passwords are securely hashed with **Passlib (bcrypt)**.
* **Modern API Stack:** Built with **FastAPI** for high performance, **Pydantic** for
    data validation, and **SQLAlchemy** for ORM-based database interaction.

## 🛠️ Tech Stack

* **Backend:** **FastAPI**
* **AI Workflow:** **LangGraph**
* **LLM:** **Google Gemini (gemini-2.0-flash)**
* **Web Search:** **Tavily Search**
* **Database:** **SQLAlchemy** (Designed for PostgreSQL with `JSONB` support)
* **Validation:** **Pydantic**
* **Authentication:** **JWT**, **OAuth2**, **Passlib (bcrypt)**

---

## ⚙️ Architecture & AI Workflow

This project's core is the stateful AI agent in `tweet_workflow.py`. The API in `api/tweet.py` acts as the interface to this agent.

### The LangGraph Workflow

1.  **Start (`/tweet/generate`):** A logged-in user sends a `topic` (e.g., "Man City vs. Real Madrid"). A new, unique `thread_id` (UUID) is created.
2.  **State 1: Search (`gen_match`):** The workflow uses the **Tavily Search** API to find live data about the match.
3.  **State 2: Extract:** **Gemini** reads the search results and populates a structured `MatchData` Pydantic model (score, summary, key moments).
4.  **State 3: Generate (`gen_post`):** A second prompt instructs **Gemini** to write a catchy, 280-character tweet using the structured match data.
5.  **State 4: Interrupt (`user_feedback`):** The workflow is *interrupted*. Its entire state is saved to the `Workflow` table in the database, and the first generated tweet is sent to the user.
6.  **Feedback (`/tweet/{thread_id}/feedback`):** The user provides feedback (e.g., `evaluation: "edit"`, `feedback: "make it more exciting"`).
7.  **State 5: Resume & Route:** The API loads the workflow's state from the database, adds the user's feedback, and `invoke`s the graph. The `route_evaluation` function routes the workflow:
    * **"edit"**: Loops back to `gen_post` to re-generate the tweet using the new feedback.
    * **"post"**: Moves to the `tweet_post` node (a placeholder for a future Twitter API call) and marks the workflow as `is_completed=True`.
    * **"cancel"**: Ends the workflow and marks it as completed.
8.  **Repeat:** The workflow continues to loop between `gen_post` and `user_feedback` until the user chooses "post" or "cancel."

### Database Schema

* **User Table:** Stores `user_id`, `username`, `email`, and `hashed_password`.
* **Workflow Table:** Stores `thread_id`, `user_id` (Foreign Key), `is_completed`, and the entire agent `state` in a `JSONB` column. This creates a one-to-many relationship (one user can have many tweet workflows).

---

## 📂 Project Structure

```
TWEETER/ 
├── api/ 
│ ├── init.py 
│ ├── auth.py # User registration & login (JWT) 
│ └── tweet.py # Tweet generation/feedback endpoints 
├── core/ 
│ ├── init.py 
│ ├── config.py # Pydantic settings (.env loading) 
│ └── tweet_workflow.py # The core LangGraph AI agent 
├── db/ 
│ ├── init.py 
│ ├── connection.py # SQLAlchemy engine & get_db session 
│ └── models.py # User & Workflow table (ORM models) 
├── schemas/ 
│ ├── init.py 
│ ├── tweet.py # Pydantic models for tweet I/O 
│ └── user.py # Pydantic models for user I/O 
├── security/ 
│ ├── init.py 
│ ├── hashing.py # Passlib (bcrypt) for passwords 
│ ├── JWTToken.py # JWT token creation 
│ └── Oauth.py # get_current_user dependency 
├── .env # API keys & secrets 
├── .gitignore 
├── main.py # FastAPI app entrypoint 
└── README.md

```

---
## 🔑 Key API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Creates a new user account. | ✕ No |
| `POST` | `/auth/token` | Logs in a user, returns a JWT token. | ✕ No |
| `GET` | `/auth/users/{id}` | Gets public details for a user. | ✓ Yes |
| `POST` | `/tweet/generate` | Starts a new tweet workflow from a topic. | ✓ Yes |
| `POST` | `/tweet/{thread_id}/feedback` | Submits feedback to refine a tweet. | ✓ Yes |

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.9+
* A PostgreSQL database
* [Google AI Studio API Key](https://aistudio.google.com/)
* [Tavily API Key](https://tavily.com/)

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/pravigowda18/tweet-generator-langgraph-faastapi.git](https://github.com/pravigowda18/tweet-generator-langgraph-faastapi.git)
    cd TWEETER
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your credentials:
    ```.env
    # Database
    DATABASE_URL="postgresql://USERNAME:PASSWORD@localhost/DB_NAME"
    
    # JWT Security
    JWT_SECRET_KEY="YOUR_SUPER_SECRET_KEY"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    
    # API Keys
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    ```

5.  **Initialize the Database:**
    * When you first run the app, SQLAlchemy will create the tables defined in `db/models.py`.

### 3. Running the Application

1.  **Start the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```
2.  **Access the API:**
    * Open your browser and go to `http://127.0.0.1:8000/docs` to see the interactive Swagger UI and test the endpoints.

---

## 🤝 How to Contribute

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/NewFeature`)
3.  Commit your Changes (`git commit -m 'Add some NewFeature'`)
4.  Push to the Branch (`git push origin feature/NewFeature`)
5.  Open a Pull Request

## 📧 Contact

Praveen S - [pravisb0002@gmail.com](mailto:pravisb0002@gmail.com)

Project Link: [https://github.com/pravigowda18/tweet-generator-langgraph-faastapi.git](https://github.com/pravigowda18/tweet-generator-langgraph-faastapi.git)