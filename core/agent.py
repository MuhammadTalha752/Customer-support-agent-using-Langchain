"""
LangChain version -- customer support agent.

Uses LangChain's newer create_agent() API.

Conversation history is stored permanently in the database
instead of being kept only in Python memory.
"""

import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
from knowledge.tools import ALL_TOOLS

from database.database import (
    get_session_messages,
    save_message,
)


SYSTEM_PROMPT = (
    "You are a customer support agent for AppInSnap, a software company. "
    "You have NO reliable knowledge of AppInSnap's services from your own training -- "
    "you MUST call search_services for ANY question about what the company does, offers, "
    "supports, or works on, even if you think you already know the answer. Never answer "
    "such questions from memory. Only state facts explicitly present in retrieved context; "
    "never invent additional services or capabilities. "

    "Use register_complaint for a NEW complaint. Do NOT call search_services when "
    "someone is just describing a problem to file as a complaint -- only call "
    "search_services for genuine questions about what the company offers. "

    "Use update_complaint_description to add detail to an EXISTING complaint number, "
    "not a new one. "

    "Use check_complaint_status to check status, and always state the status clearly "
    "in your reply. "

    "Use change_complaint_status only when the user explicitly asks to change/close/"
    "resolve a complaint."
)


# ============================================================
# LLM SETUP
# ============================================================

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0
)


# ============================================================
# AGENT SETUP
# ============================================================

agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT
)


# ============================================================
# LOAD DATABASE HISTORY
# ============================================================

def _load_history(session_id: str) -> list:
    """
    Load previous chat messages from the database
    and convert them into LangChain message format.
    """

    db_messages = get_session_messages(session_id)

    history = []

    for message in db_messages:

        if message.role == "user":
            history.append({
                "role": "user",
                "content": message.content
            })

        elif message.role == "assistant":
            history.append({
                "role": "assistant",
                "content": message.content
            })

    return history


# ============================================================
# HANDLE MESSAGE
# ============================================================

def handle_message(
    session_id: str,
    user_id: str,
    message: str
) -> dict:
    """
    Handle one user message.

    Chat history is loaded from the database using session_id,
    then the new message is sent to the LangChain agent.

    The user message and assistant response are saved
    permanently in the database.
    """

    # --------------------------------------------------------
    # 1. Load previous conversation
    # --------------------------------------------------------

    history = _load_history(session_id)


    # --------------------------------------------------------
    # 2. Add current user message
    # --------------------------------------------------------

    input_messages = history + [
        {
            "role": "user",
            "content": message
        }
    ]


    # --------------------------------------------------------
    # 3. Send conversation to LangChain agent
    # --------------------------------------------------------

    result = agent.invoke(
        {
            "messages": input_messages
        }
    )

    final_messages = result["messages"]


    # --------------------------------------------------------
    # 4. Get final assistant response
    # --------------------------------------------------------

    reply_text = final_messages[-1].content


    # --------------------------------------------------------
    # 5. Detect tools used in this turn
    # --------------------------------------------------------

    new_messages = final_messages[
        len(input_messages):
    ]

    tools_used = []

    for m in new_messages:

        if getattr(m, "tool_calls", None):

            for tc in m.tool_calls:

                tools_used.append(
                    tc["name"]
                )


    # --------------------------------------------------------
    # 6. Save user message
    # --------------------------------------------------------

    save_message(
        session_id=session_id,
        role="user",
        content=message
    )


    # --------------------------------------------------------
    # 7. Save assistant response
    # --------------------------------------------------------

    save_message(
        session_id=session_id,
        role="assistant",
        content=reply_text
    )


    # --------------------------------------------------------
    # 8. Return result to application
    # --------------------------------------------------------

    return {
        "reply": reply_text,
        "tool_used": (
            ", ".join(tools_used)
            if tools_used
            else None
        )
    }