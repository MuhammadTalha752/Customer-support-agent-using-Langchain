import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import random
import string
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL

from database.models import (
    Base,
    Complaint,
    User,
    ChatSession,
    ChatMessage,
)


# ============================================================
# DATABASE SETUP
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()


# ============================================================
# USER FUNCTIONS
# ============================================================

def user_exists(user_id: str) -> bool:
    """Check whether a user already exists."""

    db = get_session()

    try:
        user = (
            db.query(User)
            .filter_by(user_id=user_id)
            .first()
        )

        return user is not None

    finally:
        db.close()


def create_user(user_id: str, name: str | None = None) -> User:
    """Create a new user."""

    db = get_session()

    try:
        existing_user = (
            db.query(User)
            .filter_by(user_id=user_id)
            .first()
        )

        if existing_user:
            return existing_user

        user = User(
            user_id=user_id,
            name=name
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()


def get_user(user_id: str) -> User | None:
    """Get a user by User ID."""

    db = get_session()

    try:
        return (
            db.query(User)
            .filter_by(user_id=user_id)
            .first()
        )

    finally:
        db.close()


# ============================================================
# CHAT SESSION FUNCTIONS
# ============================================================

def create_chat_session(user_id: str) -> ChatSession:
    """Create a new chat session for a user."""

    db = get_session()

    try:
        session_id = str(uuid.uuid4())

        chat_session = ChatSession(
            session_id=session_id,
            user_id=user_id
        )

        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

        return chat_session

    finally:
        db.close()


def get_user_sessions(user_id: str) -> list[ChatSession]:
    """Get all chat sessions belonging to a user."""

    db = get_session()

    try:
        return (
            db.query(ChatSession)
            .filter_by(user_id=user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    finally:
        db.close()


def get_chat_session(session_id: str) -> ChatSession | None:
    """Get a specific chat session."""

    db = get_session()

    try:
        return (
            db.query(ChatSession)
            .filter_by(session_id=session_id)
            .first()
        )

    finally:
        db.close()


# ============================================================
# CHAT MESSAGE FUNCTIONS
# ============================================================

def save_message(
    session_id: str,
    role: str,
    content: str
) -> ChatMessage:
    """Save a user or assistant message."""

    db = get_session()

    try:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    finally:
        db.close()


def get_session_messages(
    session_id: str
) -> list[ChatMessage]:
    """Get all messages from a chat session in chronological order."""

    db = get_session()

    try:
        return (
            db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    finally:
        db.close()


# ============================================================
# COMPLAINT FUNCTIONS
# ============================================================

def _generate_complaint_number() -> str:
    suffix = "".join(
        random.choices(string.digits, k=6)
    )

    return f"SNP-{suffix}"


def create_complaint(
    user_id: str,
    description: str
) -> Complaint:

    db = get_session()

    try:
        number = _generate_complaint_number()

        # Ensure uniqueness
        while (
            db.query(Complaint)
            .filter_by(complaint_number=number)
            .first()
        ):
            number = _generate_complaint_number()

        complaint = Complaint(
            complaint_number=number,
            user_id=user_id,
            description=description,
            status="open",
        )

        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        return complaint

    finally:
        db.close()


def get_complaint_by_number(
    complaint_number: str
) -> Complaint | None:

    db = get_session()

    try:
        return (
            db.query(Complaint)
            .filter_by(
                complaint_number=complaint_number
            )
            .first()
        )

    finally:
        db.close()


def update_complaint_status(
    complaint_number: str,
    new_status: str
) -> Complaint | None:

    db = get_session()

    try:
        complaint = (
            db.query(Complaint)
            .filter_by(
                complaint_number=complaint_number
            )
            .first()
        )

        if not complaint:
            return None

        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(complaint)

        return complaint

    finally:
        db.close()


def append_complaint_description(
    complaint_number: str,
    additional_details: str
) -> Complaint | None:

    """
    Adds more detail to an existing complaint's description
    instead of creating a duplicate complaint.
    """

    db = get_session()

    try:
        complaint = (
            db.query(Complaint)
            .filter_by(
                complaint_number=complaint_number
            )
            .first()
        )

        if not complaint:
            return None

        timestamp = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        complaint.description = (
            f"{complaint.description}\n\n"
            f"[Update {timestamp}]: "
            f"{additional_details}"
        )

        complaint.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(complaint)

        return complaint

    finally:
        db.close()


def list_complaints_by_user(
    user_id: str
) -> list[Complaint]:

    db = get_session()

    try:
        return (
            db.query(Complaint)
            .filter_by(user_id=user_id)
            .all()
        )

    finally:
        db.close()