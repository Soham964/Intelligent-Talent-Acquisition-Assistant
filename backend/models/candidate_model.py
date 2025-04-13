class Candidate:
    def __init__(self, id, name, skills, experience, cultural_fit):
        self.id = id
        self.name = name
        self.skills = skills
        self.experience = experience
        self.cultural_fit = cultural_fit

    def validate(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Invalid name")
        if not isinstance(self.skills, list):
            raise ValueError("Skills must be a list")
        if not isinstance(self.experience, int) or self.experience < 0:
            raise ValueError("Experience must be a non-negative integer")
        if not isinstance(self.cultural_fit, bool):
            raise ValueError("Cultural fit must be a boolean")

    def transform(self):
        return {
            "id": self.id,
            "name": self.name,
            "skills": ", ".join(self.skills),
            "experience": self.experience,
            "cultural_fit": self.cultural_fit
        }