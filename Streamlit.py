"""
LangChain Customer Support Chat UI.

Features:
- User ID login
- New user registration
- Previous chat sessions
- Continue an old chat
- Start a new chat
- Persistent chat history
"""

import streamlit as st

from core.agent import handle_message

from database.database import (
    init_db,
    user_exists,
    create_user,
    get_user,
    create_chat_session,
    get_user_sessions,
    get_session_messages,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AppInSnap Support (LangChain)",
    page_icon="🦜",
    layout="centered"
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_register" not in st.session_state:
    st.session_state.show_register = False


# ============================================================
# HELPER: LOAD CHAT HISTORY
# ============================================================

def load_chat_history(session_id: str):
    """
    Load messages from the database and convert them
    into the format used by Streamlit.
    """

    db_messages = get_session_messages(session_id)

    messages = []

    for msg in db_messages:

        messages.append({
            "role": msg.role,
            "content": msg.content,
        })

    return messages


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.title("🦜 AppInSnap Support")

    st.subheader("Login")

    user_id_input = st.text_input(
        "Enter your User ID",
        placeholder="Example: user_1001"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Login",
            use_container_width=True
        ):

            user_id_input = user_id_input.strip()

            if not user_id_input:

                st.warning("Please enter a User ID.")

            elif user_exists(user_id_input):

                # ------------------------------------------------
                # Existing user
                # ------------------------------------------------

                st.session_state.user_id = user_id_input
                st.session_state.logged_in = True
                st.session_state.show_register = False

                # Get existing sessions
                sessions = get_user_sessions(user_id_input)

                if sessions:

                    # Don't automatically create another session.
                    # User will select an existing chat or create new one.

                    st.session_state.session_id = None
                    st.session_state.messages = []

                else:

                    # User exists but has no previous chat.
                    new_session = create_chat_session(
                        user_id_input
                    )

                    st.session_state.session_id = (
                        new_session.session_id
                    )

                    st.session_state.messages = []

                st.rerun()

            else:

                st.session_state.show_register = True
                st.rerun()

    with col2:

        if st.button(
            "Register",
            use_container_width=True
        ):

            st.session_state.show_register = True
            st.rerun()


    # ========================================================
    # USER NOT FOUND / REGISTRATION
    # ========================================================

    if st.session_state.show_register:

        st.divider()

        st.subheader("Create New User")

        st.info(
            "This User ID does not exist. "
            "Please register to start a new conversation."
        )

        register_user_id = st.text_input(
            "User ID",
            value=user_id_input if user_id_input else "",
            key="register_user_id"
        )

        name = st.text_input(
            "Name",
            placeholder="Enter your name"
        )

        reg_col1, reg_col2 = st.columns(2)

        with reg_col1:

            if st.button(
                "Create Account",
                use_container_width=True
            ):

                register_user_id = register_user_id.strip()
                name = name.strip()

                if not register_user_id:

                    st.warning("Please enter a User ID.")

                elif user_exists(register_user_id):

                    st.error(
                        "This User ID already exists. "
                        "Please login instead."
                    )

                else:

                    # --------------------------------------------
                    # Create user
                    # --------------------------------------------

                    create_user(
                        user_id=register_user_id,
                        name=name if name else None
                    )

                    # --------------------------------------------
                    # Create first chat session
                    # --------------------------------------------

                    new_session = create_chat_session(
                        register_user_id
                    )

                    # --------------------------------------------
                    # Login user
                    # --------------------------------------------

                    st.session_state.user_id = register_user_id
                    st.session_state.session_id = (
                        new_session.session_id
                    )
                    st.session_state.messages = []
                    st.session_state.logged_in = True
                    st.session_state.show_register = False

                    st.success(
                        "Account created successfully!"
                    )

                    st.rerun()

        with reg_col2:

            if st.button(
                "Back",
                use_container_width=True
            ):

                st.session_state.show_register = False
                st.rerun()


# ============================================================
# USER IS LOGGED IN
# ============================================================

else:

    user_id = st.session_state.user_id

    user = get_user(user_id)

    st.title("🦜 AppInSnap Support Chat")

    if user and user.name:

        st.caption(
            f"Welcome, {user.name} | User ID: {user_id}"
        )

    else:

        st.caption(
            f"User ID: {user_id}"
        )


    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.header("💬 Your Chats")

        st.write(
            f"User ID: `{user_id}`"
        )

        st.divider()

        sessions = get_user_sessions(user_id)


        # ----------------------------------------------------
        # NEW CHAT BUTTON
        # ----------------------------------------------------

        if st.button(
            "➕ New Chat",
            use_container_width=True
        ):

            new_session = create_chat_session(user_id)

            st.session_state.session_id = (
                new_session.session_id
            )

            st.session_state.messages = []

            st.rerun()


        st.divider()


        # ----------------------------------------------------
        # PREVIOUS SESSIONS
        # ----------------------------------------------------

        if sessions:

            st.subheader("Previous Chats")

            for index, chat_session in enumerate(sessions):

                session_messages = get_session_messages(
                    chat_session.session_id
                )

                # --------------------------------------------
                # Create a simple chat title
                # --------------------------------------------

                title = f"Chat {len(sessions) - index}"

                if session_messages:

                    first_user_message = next(
                        (
                            msg.content
                            for msg in session_messages
                            if msg.role == "user"
                        ),
                        None
                    )

                    if first_user_message:

                        title = first_user_message[:30]

                        if len(first_user_message) > 30:
                            title += "..."


                # --------------------------------------------
                # Session button
                # --------------------------------------------

                if st.button(
                    title,
                    key=f"session_{chat_session.session_id}",
                    use_container_width=True
                ):

                    st.session_state.session_id = (
                        chat_session.session_id
                    )

                    st.session_state.messages = (
                        load_chat_history(
                            chat_session.session_id
                        )
                    )

                    st.rerun()

        else:

            st.info("No previous chats found.")


        st.divider()


        # ----------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------

        if st.button(
            "Logout",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.session_id = None
            st.session_state.messages = []

            st.rerun()


    # ========================================================
    # SESSION CHECK
    # ========================================================

    if st.session_state.session_id is None:

        st.info(
            "Select a previous chat from the sidebar "
            "or click 'New Chat' to start a conversation."
        )

        st.stop()


    # ========================================================
    # LOAD CURRENT CHAT
    # ========================================================

    if not st.session_state.messages:

        st.session_state.messages = load_chat_history(
            st.session_state.session_id
        )


    # ========================================================
    # CHAT HEADER
    # ========================================================

    st.caption(
        f"Session: {st.session_state.session_id}"
    )


    # ========================================================
    # DISPLAY CHAT HISTORY
    # ========================================================

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):

            st.markdown(msg["content"])

            if msg.get("tool_used"):

                st.caption(
                    f"🔧 used: {msg['tool_used']}"
                )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    if user_input := st.chat_input(
        "Type your message..."
    ):

        # ----------------------------------------------------
        # Display user message immediately
        # ----------------------------------------------------

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):

            st.markdown(user_input)


        # ----------------------------------------------------
        # Get agent response
        # ----------------------------------------------------

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                result = handle_message(
                    session_id=st.session_state.session_id,
                    user_id=user_id,
                    message=user_input,
                )

            st.markdown(
                result["reply"]
            )

            if result.get("tool_used"):

                st.caption(
                    f"🔧 used: {result['tool_used']}"
                )


        # ----------------------------------------------------
        # Store assistant response in Streamlit state
        # ----------------------------------------------------

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["reply"],
            "tool_used": result.get("tool_used"),
        })