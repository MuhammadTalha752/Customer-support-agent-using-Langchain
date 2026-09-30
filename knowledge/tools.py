"""
LangChain equivalent of knowledge/tools.py
Reuses your EXISTING database.py functions -- only the "wrapper" changes
to LangChain's @tool decorator instead of a manual TOOL_DEFINITIONS list.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool
from database.database import (
    create_complaint,
    get_complaint_by_number,
    append_complaint_description,
    update_complaint_status,
)
from knowledge.rag import retrieve_answer_lc

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}


@tool
def search_services(query: str, broad: bool = False) -> str:
    """Search AppInSnap's service knowledge base to answer questions about
    what services they offer, industries served, etc. Set broad=True for
    'list everything' style questions."""
    top_k = 15 if broad else 3
    results = retrieve_answer_lc(query, top_k=top_k)
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(f"[{r['topic']}]\n{r['content']}" for r in results)


@tool
def register_complaint(user_id: str, description: str) -> str:
    """File a new customer complaint and generate a complaint number for tracking."""
    c = create_complaint(user_id=user_id, description=description)
    return f"Complaint registered successfully. Your complaint number is {c.complaint_number}. Status: {c.status}."


@tool
def check_complaint_status(complaint_number: str) -> str:
    """Check the current status of an existing complaint using its complaint number."""
    c = get_complaint_by_number(complaint_number)
    if not c:
        return f"No complaint found with number {complaint_number}."
    return (f"Complaint {c.complaint_number} | Status: {c.status} | "
            f"Description: {c.description} | Created: {c.created_at}")


@tool
def update_complaint_description(complaint_number: str, additional_details: str) -> str:
    """Add more detail to an EXISTING complaint instead of creating a new one."""
    c = append_complaint_description(complaint_number, additional_details)
    if not c:
        return f"No complaint found with number {complaint_number}."
    return f"Added your additional details to complaint {complaint_number}.\nUpdated description:\n{c.description}"


@tool
def change_complaint_status(complaint_number: str, new_status: str) -> str:
    """Change an EXISTING complaint's status. Valid values: open, in_progress, resolved, closed."""
    normalized = new_status.strip().lower().replace(" ", "_")
    if normalized not in VALID_STATUSES:
        return f"'{new_status}' isn't valid. Valid options: open, in_progress, resolved, closed."
    c = update_complaint_status(complaint_number, normalized)
    if not c:
        return f"No complaint found with number {complaint_number}."
    return f"Complaint {complaint_number} status changed to {c.status}."


ALL_TOOLS = [
    search_services,
    register_complaint,
    check_complaint_status,
    update_complaint_description,
    change_complaint_status,
]