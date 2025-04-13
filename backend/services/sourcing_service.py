import random

class SourcingAgent:
    def __init__(self):
        self.candidates = []

    def crawl_job_platforms(self):
        """Simulate crawling job platforms and internal databases."""
        candidates = [
            {"id": 1, "name": "John Doe", "skills": ["Python", "FastAPI"], "experience": 5},
            {"id": 2, "name": "Jane Smith", "skills": ["Streamlit", "Data Analysis"], "experience": 3},
            {"id": 3, "name": "Alice Johnson", "skills": ["Machine Learning", "NLP"], "experience": 7},
        ]
        return candidates

    def filter_candidates(self, candidates, job_description):
        """Filter candidates based on job description."""
        required_skills = set(job_description.get("skills", []))
        filtered = [
            candidate for candidate in candidates
            if required_skills.intersection(candidate["skills"])
        ]
        return filtered

    def rank_candidates(self, candidates):
        """Rank candidates based on experience and skill match."""
        for candidate in candidates:
            candidate["score"] = candidate["experience"] + random.uniform(0, 1) * len(candidate["skills"])
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def source_candidates(self, job_description):
        """Source candidates by crawling, filtering, and ranking."""
        candidates = self.crawl_job_platforms()
        filtered_candidates = self.filter_candidates(candidates, job_description)
        ranked_candidates = self.rank_candidates(filtered_candidates)
        return ranked_candidates