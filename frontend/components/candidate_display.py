from typing import List, Dict
import streamlit as st

def display_candidate(candidate: Dict) -> None:
    st.subheader(candidate['name'])
    st.write(f"**ID:** {candidate['id']}")
    st.write(f"**Skills:** {', '.join(candidate['skills'])}")
    st.write(f"**Experience:** {candidate['experience']} years")
    st.write(f"**Cultural Fit:** {'Yes' if candidate['cultural_fit'] else 'No'}")
    st.write("---")

def display_candidates(candidates: List[Dict]) -> None:
    if candidates:
        for candidate in candidates:
            display_candidate(candidate)
    else:
        st.write("No candidates found.")