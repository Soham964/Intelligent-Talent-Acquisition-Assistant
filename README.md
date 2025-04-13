# Intelligent Talent Acquisition Assistant

## Overview
The Intelligent Talent Acquisition Assistant is a project designed to automate candidate sourcing, screening, and initial outreach using a combination of a Flask API for the backend and a Streamlit application for the frontend. This system aims to streamline the recruitment process, making it more efficient and effective.

## Project Structure
The project is organized into two main directories: `backend` and `frontend`.

### Backend
- **app.py**: Entry point for the Flask API. Initializes the app, sets up routes, and configures middleware.
- **models/candidate_model.py**: Defines the Candidate class with properties such as id, name, skills, experience, and cultural fit.
- **routes/api.py**: Defines API endpoints for candidate sourcing, screening, and engagement.
- **services/sourcing_service.py**: Implements methods to crawl job platforms and filter candidates based on job descriptions.
- **utils/helpers.py**: Provides utility functions for data formatting, logging, and error handling.
- **requirements.txt**: Lists dependencies required for the backend.

### Frontend
- **app.py**: Entry point for the Streamlit application. Initializes the app and sets up the main layout.
- **components/candidate_display.py**: Streamlit component for displaying candidate information.
- **pages/home.py**: Defines the home page of the Streamlit app with sections for sourcing and screening results.
- **utils/streamlit_helpers.py**: Provides utility functions specific to Streamlit.
- **requirements.txt**: Lists dependencies required for the frontend.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd intelligent-talent-acquisition-assistant
   ```

2. Set up the backend:
   - Navigate to the `backend` directory.
   - Create a virtual environment and activate it:
     ```
     python -m venv venv
     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
     ```
   - Install the required packages:
     ```
     pip install -r requirements.txt
     ```

3. Set up the frontend:
   - Navigate to the `frontend` directory.
   - Install the required packages:
     ```
     pip install -r requirements.txt
     ```

4. Run the backend:
   ```
   python app.py
   ```

5. Run the frontend:
   ```
   streamlit run app.py
   ```

## Usage Guidelines
- Access the Streamlit application through the web browser at `http://localhost:8501`.
- Use the application to source candidates, view screening results, and manage outreach efforts.

## System Architecture
The system is designed with a clear separation of concerns, utilizing Flask for the backend API and Streamlit for the user interface. This architecture allows for scalability and maintainability, enabling future enhancements and integrations.