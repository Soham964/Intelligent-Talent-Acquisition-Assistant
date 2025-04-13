import streamlit as st

def home_page():
    st.title("Intelligent Talent Acquisition Assistant")
    
    st.header("Candidate Sourcing")
    st.write("Automate your candidate sourcing process with our intelligent assistant.")
    
    st.header("Screening Results")
    st.write("View the results of candidate screenings and evaluations.")
    
    st.header("Engagement Status")
    st.write("Track the engagement status of candidates throughout the hiring process.")
    
if __name__ == "__main__":
    home_page()