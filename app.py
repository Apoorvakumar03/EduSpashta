import streamlit as st
from phi.assistant import Assistant
from phi.document.reader.pdf import PDFReader
from phi.utils.log import logger
from assistant import get_groq_assistant
from db_utils import create_user_table, add_user, verify_user  # Import login-related functions
import io
import os
import hashlib
import sqlite3

# Environment variables
os.environ['GROQ_API_KEY'] = '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'

# Set up page configuration
st.set_page_config(page_title="Examination Correction App")

# Initialize the SQLite user database for login functionality
try:
    create_user_table()
except Exception as e:
    st.error(f"Error initializing database: {e}")
    st.stop()

# Login page function
def login_page():
    st.title("Login")

    # Input fields for username and password
    username = st.text_input("Username", value=st.session_state.get("username", ""))
    password = st.text_input("Password", type="password")

    # Login button
    if st.button("Login"):
        try:
            user = verify_user(username, password)
            if user:
                st.success("Login successful!")
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.rerun()  # Reload the page
            else:
                st.error("Invalid username or password")
        except Exception as e:
            st.error(f"Error during login: {e}")

# Signup page function
def signup_page():
    st.title("Create an Account")

    # Input fields for new user registration
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")

    # Signup button
    if st.button("Sign Up"):
        try:
            add_user(new_username, new_password)
            st.success("Account created successfully!")
        except sqlite3.IntegrityError:
            st.error("Username already taken, please choose another one.")
        except Exception as e:
            st.error(f"Error during signup: {e}")

# Main function to handle login and signup logic
def user_authentication():
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        # Create two columns for buttons
        col1, col2 = st.columns([2, 1])
        col1.write(f"Logged in as: {st.session_state['username']}")
        if col2.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""  # Clear username on logout
            st.rerun()  # Reload the page on logout
    else:
        choice = st.sidebar.selectbox("Login or Sign Up", ["Login", "Sign Up"])
        if choice == "Login":
            login_page()
        else:
            signup_page()

# Core grading functionality
def main_app():
    # Dropdown options for LLM and embeddings models
    llm_options = ["llama3-70b-8192"]
    embeddings_options = ["nomic-embed-text"]

    # LLM model selection
    llm_model = st.sidebar.selectbox("Select LLM Model", options=llm_options)
    embeddings_model = st.sidebar.selectbox("Select Embeddings Model", options=embeddings_options)

    # Store selected models in session state
    st.session_state["llm_model"] = llm_model
    st.session_state["embeddings_model"] = embeddings_model

    assistant: Assistant
    if "assistant" not in st.session_state or st.session_state["assistant"] is None:
        assistant = get_groq_assistant(llm_model=llm_model, embeddings_model=embeddings_model)
        st.session_state["assistant"] = assistant
    else:
        assistant = st.session_state["assistant"]

    try:
        st.session_state["assistant_run_id"] = assistant.create_run()
    except Exception as e:
        st.warning(f"Could not create assistant: {e}")
        return

    # Upload model answer PDF
    model_answer_pdf = st.file_uploader("Upload Model Answer PDF", type="pdf")
    model_answers = []
    if model_answer_pdf:
        reader = PDFReader()
        model_documents = reader.read(io.BytesIO(model_answer_pdf.read()))
        model_answers = [doc.content for doc in model_documents]

    # Upload student answer PDF
    student_answer_pdf = st.file_uploader("Upload Student Answer PDF", type="pdf")
    student_answers = []
    if student_answer_pdf:
        reader = PDFReader()
        student_documents = reader.read(io.BytesIO(student_answer_pdf.read()))
        student_answers = [doc.content for doc in student_documents]

    # Grade answers
    if st.button("Grade Answers"):
        if model_answers and student_answers:
            grades = []
            prompt = f"Grade the following student answer based on the model answer:\n\nModel Answer: {[doc.content for doc in model_documents]}\n\nStudent Answer: {[doc.content for doc in student_documents]}"
            try:
                response_generator = assistant.run(prompt)
                response = ''.join(list(response_generator))
                grades.append(response)
                for i, grade in enumerate(grades, 1):
                    st.write(f"Grade {i}: {grade}")
            except Exception as e:
                st.error(f"Error during grading: {e}")
        else:
            st.warning("Please upload both Model Answer PDF and Student Answer PDF")

# Main function that integrates login and main app logic
def main():
    user_authentication()
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        main_app()

if __name__ == '__main__':
    main()
