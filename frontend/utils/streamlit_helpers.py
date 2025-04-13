import streamlit as st
import time
def custom_button(label, key=None):
    """Creates a custom button with the specified label."""
    return st.button(label, key=key)

def display_candidate_info(candidate):
    """Displays candidate information in a structured format."""
    st.subheader(candidate['name'])
    st.write(f"Skills: {', '.join(candidate['skills'])}")
    st.write(f"Experience: {candidate['experience']} years")
    st.write(f"Cultural Fit: {candidate['cultural_fit']}")

def show_loading_spinner():
    """Displays a loading spinner while processing."""
    with st.spinner('Loading...'):
        time.sleep(2)  # Simulate a delay for loading

def create_candidate_card(candidate):
    """Creates a card layout for displaying candidate information."""
    with st.card():
        display_candidate_info(candidate)
        if custom_button("Contact", key=candidate['id']):
            st.success(f"Contacting {candidate['name']}...")