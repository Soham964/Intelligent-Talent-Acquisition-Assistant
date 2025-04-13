def format_candidate_data(candidate):
    formatted_data = {
        "ID": candidate.id,
        "Name": candidate.name,
        "Skills": ", ".join(candidate.skills),
        "Experience": f"{candidate.experience} years",
        "Cultural Fit": "Yes" if candidate.cultural_fit else "No"
    }
    return formatted_data

def log_error(error_message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{error_message}\n")

def validate_candidate_data(candidate_data):
    required_fields = ["name", "skills", "experience"]
    for field in required_fields:
        if field not in candidate_data:
            raise ValueError(f"Missing required field: {field}")
    return True