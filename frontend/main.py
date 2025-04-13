import sys
from pathlib import Path
import os
import json
import datetime
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from postmarker.core import PostmarkClient

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import streamlit as st

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def send_email(to_email, subject, body):
    """Send an email using SMTP."""
    try:
        # Get email credentials from environment variables
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # Login
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        
        # Close connection
        server.quit()
        
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

# Generate email with HR details and position from job description
def generate_email(candidate_data, email_type, job_description, additional_notes=""):
    """Generate an email using OpenAI based on candidate data, email type, and job description."""
    try:
        # Default HR details from environment variables
        hr_name = os.getenv("HR_NAME")
        hr_email = os.getenv("EMAIL_USER")  # Corrected typo from EMAL_USER to EMAIL_USER
        company_name = os.getenv("COMPANY_NAME")

        st.write("HR_NAME:", os.getenv("HR_NAME"))
        st.write("HR_EMAIL:", os.getenv("EMAIL_USER"))
        st.write("COMPANY_NAME:", os.getenv("COMPANY_NAME"))

        # Extract position from job description
        position_name = job_description.get("title", "[Position Name]")

        # Prepare the prompt
        prompt = f"""
        Generate a professional {email_type} email for the following candidate:

        Name: {candidate_data.get('name', '')}
        Position Applied: {position_name}
        Additional Notes: {additional_notes}

        Please write a professional email that:
        1. Is personalized with the candidate's name
        2. Clearly communicates the {email_type} decision
        3. Maintains a professional and respectful tone
        4. Includes any relevant next steps or feedback
        5. Is concise but complete
        6. Ends with "Warm regards, {hr_name}, {hr_email}, {company_name}"
        """

        # Generate email using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional HR assistant helping to draft emails to candidates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating email: {str(e)}"

def send_email_to_candidate(candidate_email, email_subject, email_body):
    """Send an email to the candidate's email address using Postmark."""
    try:
        # Get Postmark server token from environment variables
        postmark_server_token = os.getenv("POSTMARK_SERVER_TOKEN")
        if not postmark_server_token:
            return False, "Postmark server token is not configured."

        # Initialize Postmark client
        client = PostmarkClient(server_token=postmark_server_token)

        # Send the email
        response = client.emails.send(
            From=os.getenv("EMAIL_USER"),
            To=candidate_email,
            Subject=email_subject,
            TextBody=email_body
        )

        # Check the response status
        if response['Message'] == 'OK':
            return True, "Email sent successfully!"
        else:
            return False, f"Failed to send email. Response: {response}"

    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def display_candidate_details(candidate_data):
    """Display candidate details in a structured format."""
    st.subheader("Candidate Details")
    
    # Display basic information
    st.write(f"**Name:** {candidate_data.get('name', 'N/A')}")
    
    # Display contact information
    st.write("**Contact Information:**")
    contact_info = candidate_data.get('contact_info', {})
    if contact_info:
        st.write(f"- Email: {contact_info.get('email', 'N/A')}")
        st.write(f"- Phone: {contact_info.get('phone', 'N/A')}")
        if 'address' in contact_info:
            st.write(f"- Address: {contact_info['address']}")
    
    # Display summary
    if candidate_data.get('summary'):
        st.write("**Summary:**")
        st.write(candidate_data['summary'])
    
    # Display education
    if candidate_data.get('education'):
        st.write("**Education:**")
        for edu in candidate_data['education']:
            st.write(f"- {edu.get('degree', '')}")
            if edu.get('institution'):
                st.write(f"  Institution: {edu['institution']}")
            if edu.get('year'):
                st.write(f"  Year: {edu['year']}")
            if edu.get('details'):
                for detail in edu['details']:
                    st.write(f"  {detail}")
    
    # Display experience
    if candidate_data.get('experience'):
        st.write("**Experience:**")
        for exp in candidate_data['experience']:
            st.write(f"- {exp.get('title', '')} at {exp.get('company', '')}")
            if exp.get('duration'):
                st.write(f"  Duration: {exp['duration']}")
            if exp.get('responsibilities'):
                st.write("  Responsibilities:")
                for resp in exp['responsibilities']:
                    st.write(f"  • {resp}")
    
    # Display skills
    if candidate_data.get('skills'):
        st.write("**Skills:**")
        for category, items in candidate_data['skills'].items():  # Iterate over the dictionary
            items_inline = ", ".join(items)  # Join items with commas
            st.write(f"**{category}:** {items_inline}")  # Display category and items inline # Render the list in Markdown

def screen_resume(resume_data, job_description):
    """Screen a resume against a job description."""
    # Flatten and normalize resume skills
    resume_skills = set()
    if isinstance(resume_data.get('skills'), dict):  # Handle categorized skills
        for category, skills in resume_data['skills'].items():
            resume_skills.update(skill.strip().lower() for skill in skills)
    elif isinstance(resume_data.get('skills'), list):  # Handle flat list of skills
        resume_skills = set(skill.strip().lower() for skill in resume_data['skills'])
    elif isinstance(resume_data.get('skills'), str):  # Handle comma-separated string
        resume_skills = set(skill.strip().lower() for skill in resume_data['skills'].split(','))

    # Normalize and process required skills from job description
    required_skills = set()
    if isinstance(job_description.get('required_skills'), list):
        required_skills = set(skill.strip().lower() for skill in job_description['required_skills'])
    elif isinstance(job_description.get('required_skills'), str):
        required_skills = set(skill.strip().lower() for skill in job_description['required_skills'].split(','))

    # Calculate matching score
    matched_skills = resume_skills.intersection(required_skills)
    score = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0

    return {
        "score": score,
        "matched_skills": list(matched_skills),
        "missing_skills": list(required_skills - resume_skills)
    }

def format_candidate_name(filename):
    """Format the JSON filename into a readable candidate name."""
    # Remove .json extension and replace underscores with spaces
    name = filename.replace('.json', '').replace('_Resume', '').replace('_', ' ')
    return name

def main():
    # Initialize database at the start
    from database import InterviewDatabase
    if 'db' not in st.session_state:
        st.session_state.db = InterviewDatabase()

    st.title("Intelligent Talent Acquisition Assistant")

    # Get all JSON files from the directory
    json_dir = project_root / "extracted_indian_resumes"
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

    if not json_files:
        st.warning("No candidate resumes found in the extracted_indian_resumes directory.")
        return

    # Create a single dropdown for candidate selection at the top
    name_to_file = {format_candidate_name(f): f for f in json_files}
    selected_name = st.selectbox("Select a candidate:", sorted(name_to_file.keys()))
    selected_file = name_to_file[selected_name]

    # Load candidate data
    try:
        with open(json_dir / selected_file, 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
    except Exception as e:
        st.error(f"Error loading candidate data: {str(e)}")
        return

    # Create tabs for different sections
    tabs = st.tabs(["📋 Candidate Details", "🔍 Resume Screening", "📅 Interview Scheduling", "💬 Engagement"])

    # Tab 1: Candidate Details
    with tabs[0]:
        st.header("Candidate Details")
        display_candidate_details(candidate_data)

    # Tab 2: Resume Screening
    with tabs[1]:
        st.header("Resume Screening")
        
        # Create two columns for better organization
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            st.subheader("💼 Job Requirements")
            with st.expander("Enter Job Details", expanded=True):
                job_title = st.text_input("Job Title", help="Enter the position title")
                required_skills = st.text_area(
                    "Required Skills",
                    help="Enter skills separated by commas (e.g., Python, JavaScript, SQL)"
                )
                job_description = {
                    "title": job_title,
                    "required_skills": [skill.strip() for skill in required_skills.split(',') if skill.strip()]
                }
        
        with right_col:
            st.subheader("🎯 Screening Results")
            if st.button("🔍 Screen Resume", type="primary"):
                try:
                    # Screen the resume
                    screening_result = screen_resume(candidate_data, job_description)
                    
                    # Create a container for results
                    results_container = st.container()
                    
                    with results_container:
                        # Display overall score with a progress bar
                        st.markdown("### Overall Match")
                        score = screening_result['score']
                        st.progress(score / 100)
                        st.markdown(f"**Match Score:** {score:.1f}%")
                        
                        # Display skills comparison
                        st.markdown("### Skills Analysis")
                        skills_col1, skills_col2 = st.columns(2)
                        
                        with skills_col1:
                            st.markdown("✅ **Matched Skills**")
                            if screening_result['matched_skills']:
                                for skill in screening_result['matched_skills']:
                                    st.success(skill)
                            else:
                                st.info("No matched skills found")
                        
                        with skills_col2:
                            st.markdown("❌ **Missing Skills**")
                            if screening_result['missing_skills']:
                                for skill in screening_result['missing_skills']:
                                    st.error(skill)
                            else:
                                st.success("No missing skills!")
                        
                        # Add recommendation based on score
                        st.markdown("### 📋 Recommendation")
                        if score >= 80:
                            st.success("Strong match! Consider proceeding with the interview process.")
                        elif score >= 60:
                            st.warning("Moderate match. May need additional screening or skills verification.")
                        else:
                            st.error("Low match. Candidate may not meet minimum requirements.")
                
                except Exception as e:
                    st.error(f"Error screening resume: {str(e)}")

    # Tab 3: Interview Scheduling
    with tabs[2]:
        st.header("Interview Scheduling")
        st.markdown("---")
        
        # Create three columns for better organization
        date_col, time_col, status_col = st.columns([1, 1, 1])
        
        with date_col:
            st.subheader("1. Select Date")
            selected_date = st.date_input(
                "Interview Date",
                min_value=datetime.date.today(),
                help="Choose a date for the interview",
                key="interview_date"
            )
        
        # Get available and booked slots from database
        available_times = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"]
        booked_slots = st.session_state.db.get_booked_slots()
        
        # Convert available times to 24-hour format for comparison
        def convert_to_24hr(time_str):
            try:
                return datetime.datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
            except ValueError:
                return time_str
        
        with time_col:
            st.subheader("2. Select Time")
            # Filter available slots for selected date
            date_str = selected_date.strftime("%Y-%m-%d")
            booked_times = [convert_to_24hr(slot.split()[1]) for slot in booked_slots.keys() if slot.split()[0] == date_str]
            available_slots = [
                f"{date_str} {time}" 
                for time in available_times 
                if convert_to_24hr(time) not in booked_times
            ]
            
            selected_slot = st.selectbox(
                "Available Time Slots",
                options=available_slots,
                help="Select an available time slot",
                format_func=lambda x: x.split()[1] if x else ""
            )
        
        with status_col:
            st.subheader("3. Confirm Booking")
            if st.button("📅 Schedule Interview", type="primary"):
                if selected_slot:
                    # Schedule interview in database
                    date_str, time_str = selected_slot.split(" ", 1)
                    success, message = st.session_state.db.schedule_interview(
                        candidate_name=selected_name,
                        interview_date=date_str,
                        interview_time=time_str
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("⚠️ Please select an available time slot")
        
        # Display booked slots
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📋 Scheduled Interviews")
        with col2:
            if st.button("🗑️ Clear All", type="secondary"):
                if st.session_state.db.clear_all_interviews():
                    st.success("All interview slots cleared successfully!")
                    st.rerun()
                else:
                    st.error("Failed to clear interview slots")
        
        if booked_slots:
            # Create a modern looking table for bookings
            bookings_by_date = {}
            for slot, booking in booked_slots.items():
                date = slot.split()[0]
                if date not in bookings_by_date:
                    bookings_by_date[date] = []
                bookings_by_date[date].append((slot.split()[1], booking['candidate_name']))
            
            # Display bookings in an organized table format
            for date in sorted(bookings_by_date.keys()):
                st.markdown(f"**📅 {date}**")
                for time, candidate in sorted(bookings_by_date[date]):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(time)
                    with col2:
                        st.write(candidate)
                    with col3:
                        if st.button("🗑️", key=f"delete_{date}_{time}_{candidate}"):
                            try:
                                success = st.session_state.db.delete_interview(candidate, date, time)
                                if success:
                                    st.success("Interview slot deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Interview slot not found or already deleted.")
                            except Exception as e:
                                st.error(f"Error deleting interview slot: {str(e)}")
        else:
            st.info("No interviews scheduled yet")

    # Tab 4: Engagement
    with tabs[3]:
        st.header("Candidate Engagement")
        
        # Create subtabs for different engagement features
        subtabs = st.tabs(["💬 Chat Assistant", "✉️ Email Communication"])
        
        # Subtabs[0]: Chat Assistant
        with subtabs[0]:
            st.subheader("AI Assistant Chat")
            
            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display chat messages
            for message in reversed(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input area
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col1:
                prompt = st.text_input("Type your message here:", key="chat_input", placeholder="Ask about the candidate or request assistance...")
            with col2:
                send_button = st.button("📤 Send", use_container_width=True)

            # Revert to the previous implementation for handling all candidates
            if send_button and prompt:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Check if the user is asking about candidates, interviews, summaries, or resume scores
                if "candidates" in prompt.lower() or "interviews" in prompt.lower() or "summary" in prompt.lower() or "resume scores" in prompt.lower():
                    try:
                        # Fetch scheduled interviews
                        scheduled_interviews = st.session_state.db.get_all_scheduled_interviews()
                        selected_candidates = [
                            {
                                'name': interview['candidate_name'],
                                'date': interview['interview_date'],
                                'time': interview['interview_time']
                            }
                            for interview in scheduled_interviews
                        ]

                        # Load all candidate names and data from JSON files
                        json_dir = project_root / "extracted_indian_resumes"
                        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
                        all_candidates = [
                            format_candidate_name(f) for f in json_files
                        ]

                        # Define a sample job description for scoring
                        job_description = {
                            "title": "Backend Developer",
                            "required_skills": ["Python", "NodeJS", "MongoDB", "AWS", "System Design"]
                        }

                        # Calculate resume scores for all candidates
                        candidate_scores = []
                        for candidate_name, candidate_file in zip(all_candidates, json_files):
                            try:
                                with open(json_dir / candidate_file, 'r', encoding='utf-8') as f:
                                    candidate_data = json.load(f)

                                screening_result = screen_resume(candidate_data, job_description)
                                score = screening_result['score']
                                candidate_scores.append({
                                    'name': candidate_name,
                                    'score': score,
                                    'matched_skills': screening_result['matched_skills'],
                                    'missing_skills': screening_result['missing_skills']
                                })
                            except Exception as e:
                                candidate_scores.append({
                                    'name': candidate_name,
                                    'score': "Error",
                                    'error': str(e)
                                })

                        # Determine unselected candidates
                        selected_names = {candidate['name'] for candidate in selected_candidates}
                        unselected_candidates = [
                            name for name in all_candidates if name not in selected_names
                        ]

                        # Generate response based on the query
                        response_text = ""
                        if "summary" in prompt.lower():
                            total_candidates = len(all_candidates)
                            total_selected = len(selected_candidates)
                            total_scheduled = len(scheduled_interviews)

                            response_text += "Summary of Candidates:\n"
                            response_text += f"- Total Candidates: {total_candidates}\n"
                            response_text += f"- Selected Candidates: {total_selected}\n"
                            response_text += f"- Scheduled Interviews: {total_scheduled}\n\n"

                        if "selected" in prompt.lower():
                            response_text += "Selected Candidates with Scheduled Interviews:\n"
                            if selected_candidates:
                                for candidate in selected_candidates:
                                    response_text += f"- {candidate['name']} (Interview: {candidate['date']} at {candidate['time']})\n"
                            else:
                                response_text += "No candidates have been selected yet.\n"

                        if "unselected" in prompt.lower():
                            response_text += "\nUnselected Candidates:\n"
                            if unselected_candidates:
                                for name in unselected_candidates:
                                    response_text += f"- {name}\n"
                            else:
                                response_text += "All candidates have been selected.\n"

                        if "resume scores" in prompt.lower():
                            response_text += "\nResume Scores:\n"
                            for candidate in candidate_scores:
                                response_text += f"- {candidate['name']}: {candidate['score']}%\n"
                                response_text += "  Matched Skills: " + ", ".join(candidate.get('matched_skills', [])) + "\n"
                                response_text += "  Missing Skills: " + ", ".join(candidate.get('missing_skills', [])) + "\n"

                        # Add the response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        st.rerun()

                    except Exception as e:
                        response_text = f"Error processing your request: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        st.rerun()
                else:
                    # Generate AI response for other queries
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an AI assistant helping with talent acquisition. You can help with reviewing resumes, scheduling interviews, and providing feedback on candidates."},
                                {"role": "user", "content": f"User request: {prompt}"}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        response_text = response.choices[0].message.content.strip()
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        st.rerun()
                    except Exception as e:
                        error_msg = f"Error generating response: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

        # Subtabs[1]: Email Communication
        with subtabs[1]:
            st.subheader("Email Communication")
            
            # Email template selection
            email_type = st.selectbox(
                "Select Email Type",
                ["Application Update", "Interview Invitation", "Follow-up", "Offer Letter", "Rejection Letter"],
                key="email_type"
            )
            
            # Additional notes for email
            additional_notes = st.text_area(
                "Additional Notes",
                placeholder="Add any specific details or instructions...",
                key="email_notes"
            )
            
            # Restore the "Send Email" button and remove redundant "Body:" text
            if st.button("📝 Preview Email"):
                try:
                    # Generate the email subject dynamically
                    email_subject = f"{email_type} - {os.getenv('COMPANY_NAME', 'ABC Corp')}"

                    # Generate the email body dynamically
                    email_body = f"""
Subject: {email_subject}

Dear {candidate_data.get('name', 'Candidate')},

I hope this message finds you well. I wanted to personally reach out to update you on the status of your application for the {job_description.get('title', '[Position Applied]')} role at {os.getenv('COMPANY_NAME', 'ABC Corp')}.

After careful consideration and review of all applicants, we regret to inform you that we have chosen to move forward with other candidates whose qualifications more closely match our current needs.

We sincerely appreciate the time and effort you put into your application and want to thank you for your interest in joining our team. Your skills and experience are impressive, and we encourage you to keep an eye on our career page for future opportunities that align with your expertise.

If you would like specific feedback on your application or have any questions, please feel free to reach out to me directly at {os.getenv('EMAIL_USER')}.

Thank you once again for your interest in our company. We wish you all the best in your job search and future endeavors.

Warm regards,

Jensen Huang
{os.getenv('EMAIL_USER')}
{os.getenv('COMPANY_NAME', 'ABC Corp')}
"""

                    # Display the email preview
                    st.markdown("### Email Preview")
                    st.info(f"**Subject:** {email_subject}")
                    st.markdown(email_body.replace('\n', '<br>'), unsafe_allow_html=True)

                    # Add detailed debugging logs to verify email-sending functionality
                    if st.button("✉️ Send Email"):
                        try:
                            # Get the selected candidate's email
                            candidate_email = candidate_data.get('contact_info', {}).get('email', '')
                            if not candidate_email:
                                st.error("❌ Candidate email address not found.")
                            else:
                                # Generate the email body dynamically
                                email_subject = f"Application Update"
                                email_body = f"""
Subject: {email_subject}

Dear Candidate,

I hope this message finds you well. I wanted to personally reach out to update you on the status of your application for the {job_description.get('title', '[Position Applied]')} role at {os.getenv('COMPANY_NAME', 'ABC Corp')}.

After careful consideration and review of all applicants, we regret to inform you that we have chosen to move forward with other candidates whose qualifications more closely match our current needs.

We sincerely appreciate the time and effort you put into your application and want to thank you for your interest in joining our team. Your skills and experience are impressive, and we encourage you to keep an eye on our career page for future opportunities that align with your expertise.

If you would like specific feedback on your application or have any questions, please feel free to reach out to me directly at {os.getenv('EMAIL_USER')}.

Thank you once again for your interest in our company. We wish you all the best in your job search and future endeavors.

Warm regards,

Jensen Huang
{os.getenv('EMAIL_USER')}
{os.getenv('COMPANY_NAME', 'ABC Corp')}
"""

                                # Debugging logs
                                st.write("Debugging: Sending email...")
                                st.write("Recipient Email:", candidate_email)
                                st.write("Email Subject:", email_subject)
                                st.write("Email Body:", email_body)
                                st.write("Postmark Server Token:", os.getenv("POSTMARK_SERVER_TOKEN"))

                                # Send the email
                                success, message = send_email_to_candidate(candidate_email, email_subject, email_body)
                                if success:
                                    st.success("✅ Email sent successfully!")
                                else:
                                    st.error(f"❌ {message}")
                                    st.write("Debugging: Postmark API response:", message)
                        except Exception as e:
                            st.error(f"❌ Error sending email: {str(e)}")
                            st.write("Debugging error:", str(e))
                except Exception as e:
                    st.error(f"❌ Error generating email preview: {str(e)}")

if __name__ == "__main__":
    main()