import os
import re
import sys
import PyPDF2
import nltk
import traceback
from datetime import datetime
from pathlib import Path
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import spacy
import logging
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import fitz  # PyMuPDF
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = find_dotenv()
if not env_path:
    logger.error("No .env file found")
    raise ValueError("No .env file found. Please create one with required environment variables.")
load_dotenv(env_path)

# Verify and initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key not configured in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('words', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)

class ResumeParser:
    def __init__(self):
        self.logger = logger
        self.logger.info("Initializing ResumeParser with GPT-3.5-turbo integration...")
        
        try:
            # Verify spaCy model installation
            try:
                self.nlp = spacy.load('en_core_web_sm')
                self.logger.info("Loaded spaCy model successfully")
            except OSError:
                self.logger.error("spaCy model 'en_core_web_sm' not found. Attempting to download...")
                os.system(f"{sys.executable} -m spacy download en_core_web_sm")
                self.nlp = spacy.load('en_core_web_sm')
                self.logger.info("Successfully downloaded and loaded spaCy model")
            
            # Enhanced skill patterns with categories
            self.skill_patterns = {
                'programming_languages': [
                    'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
                    'scala', 'r', 'golang', 'perl', 'typescript'
                ],
                'web_technologies': [
                    'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'express.js',
                    'django', 'flask', 'spring', 'asp.net', 'jquery', 'bootstrap'
                ],
                'databases': [
                    'sql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'redis', 'elasticsearch',
                    'cassandra', 'dynamodb', 'firebase'
                ],
                'cloud_devops': [
                    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'terraform',
                    'ansible', 'circleci', 'travis', 'prometheus', 'grafana'
                ],
                'data_science_ml': [
                    'machine learning', 'deep learning', 'data analysis', 'tensorflow', 'pytorch',
                    'pandas', 'numpy', 'scikit-learn', 'opencv', 'nltk', 'spacy'
                ],
                'soft_skills': [
                    'project management', 'agile', 'scrum', 'leadership', 'communication',
                    'problem solving', 'teamwork', 'analytical', 'time management'
                ]
            }
            
            self.education_keywords = [
                'bachelor', 'master', 'phd', 'degree', 'university', 'college', 'school',
                'education', 'certification', 'diploma', 'b.tech', 'm.tech', 'b.e', 'm.e',
                'mba', 'bba', 'b.sc', 'm.sc', 'b.com', 'm.com'
            ]
            
            self.experience_markers = [
                'experience', 'employment', 'work history', 'career', 'position',
                'job', 'role', 'professional experience'
            ]
            
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file with improved formatting."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                blocks = page.get_text("blocks")
                # Sort blocks by vertical position (top to bottom)
                blocks.sort(key=lambda b: b[1])  # b[1] is the y0 coordinate
                for b in blocks:
                    text += b[4] + "\n"  # b[4] is the text content
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def extract_name(self, text: str) -> str:
        """Extract name from text using pattern matching and NER."""
        # First few lines often contain the name
        first_lines = text.split("\n")[:5]
        for line in first_lines:
            doc = self.nlp(line)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text.strip()
        
        # If no name found with NER, try the first non-empty line
        for line in first_lines:
            if line.strip() and not any(w in line.lower() for w in ["resume", "cv", "curriculum"]):
                return line.strip()
        return ""

    def extract_contact_info(self, text: str) -> Dict:
        """Extract contact information with improved patterns."""
        contact_info = {
            "email": "",
            "phone": "",
            "location": ""
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            contact_info["email"] = email_matches[0]
            
        # Phone patterns (including Indian formats)
        phone_patterns = [
            r'\+91[-\s]?\d{10}',
            r'(?<!\d)\d{10}(?!\d)',  # Exactly 10 digits
            r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info["phone"] = matches[0].replace(" ", "").replace("-", "")
                break
                
        # Location pattern
        location_patterns = [
            r'(?i)Address[:\s]+([^\n]+)',
            r'(?i)Location[:\s]+([^\n]+)',
            r'(?i)(?:Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata|Pune)[,\s]*[^\n]*'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                contact_info["location"] = match.group(0).strip()
                break
                
        return contact_info

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information with improved patterns."""
        education = []
        
        # Common Indian education keywords
        edu_keywords = [
            r'(?i)B\.?Tech',
            r'(?i)M\.?Tech',
            r'(?i)BE\b',
            r'(?i)ME\b',
            r'(?i)Bachelor of',
            r'(?i)Master of',
            r'(?i)PhD',
            r'(?i)XII',
            r'(?i)HSC',
            r'(?i)10th',
            r'(?i)12th'
        ]
        
        # Split text into sections
        sections = text.split("\n\n")
        education_section = False
        current_edu = {}
        
        for section in sections:
            # Check if this is the education section
            if re.search(r'(?i)education|qualification|academic', section):
                education_section = True
                continue
                
            if education_section:
                # Look for education entries
                for keyword in edu_keywords:
                    if re.search(keyword, section):
                        if current_edu:
                            education.append(current_edu)
                            
                        current_edu = {
                            "degree": "",
                            "institution": "",
                            "year": "",
                            "score": ""
                        }
                        
                        lines = section.split("\n")
                        for line in lines:
                            # Extract degree
                            if re.search(keyword, line):
                                current_edu["degree"] = line.strip()
                                
                            # Extract institution
                            if re.search(r'(?i)(university|college|institute|school)', line):
                                current_edu["institution"] = line.strip()
                                
                            # Extract year
                            year_match = re.search(r'(?:19|20)\d{2}(?:\s*-\s*(?:19|20)\d{2})?', line)
                            if year_match:
                                current_edu["year"] = year_match.group()
                                
                            # Extract score (percentage or CGPA)
                            score_match = re.search(r'(?i)(?:cgpa|percentage|score)[:\s]*(\d+\.?\d*)', line)
                            if score_match:
                                current_edu["score"] = score_match.group(1)
                                
        if current_edu:
            education.append(current_edu)
            
        return education

    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience information with improved patterns."""
        experience = []
        
        # Split text into sections
        sections = text.split("\n\n")
        experience_section = False
        current_exp = {}
        
        for section in sections:
            # Check if this is the experience section
            if re.search(r'(?i)experience|employment|work history', section):
                experience_section = True
                continue
                
            if experience_section:
                lines = section.split("\n")
                
                # Look for company names and positions
                company_pattern = r'(?i)(ltd|limited|inc|corp|corporation|technologies|solutions)'
                position_pattern = r'(?i)(engineer|developer|manager|consultant|analyst|architect)'
                
                if any(re.search(company_pattern, line) for line in lines) or \
                   any(re.search(position_pattern, line) for line in lines):
                    if current_exp:
                        experience.append(current_exp)
                        
                    current_exp = {
                        "company": "",
                        "position": "",
                        "duration": "",
                        "responsibilities": []
                    }
                    
                    for line in lines:
                        # Extract company name
                        if re.search(company_pattern, line):
                            current_exp["company"] = line.strip()
                            
                        # Extract position
                        elif re.search(position_pattern, line):
                            current_exp["position"] = line.strip()
                            
                        # Extract duration
                        elif re.search(r'(?:19|20)\d{2}', line):
                            current_exp["duration"] = line.strip()
                            
                        # Extract responsibilities
                        elif line.strip().startswith(("-", "•", "*")) or \
                             re.search(r'(?i)(developed|implemented|managed|created|designed)', line):
                            current_exp["responsibilities"].append(line.strip())
                            
        if current_exp:
            experience.append(current_exp)
            
        return experience

    def extract_certifications(self, text: str) -> List[Dict]:
        """Extract certification information with improved patterns."""
        certifications = []
        
        # Split text into sections
        sections = text.split("\n\n")
        cert_section = False
        current_cert = {}
        
        for section in sections:
            # Check if this is the certifications section
            if re.search(r'(?i)certification|certificate|certified', section):
                cert_section = True
                continue
                
            if cert_section:
                lines = section.split("\n")
                
                for line in lines:
                    if re.search(r'(?i)(certification|certificate|certified)', line):
                        if current_cert:
                            certifications.append(current_cert)
                            
                        current_cert = {
                            "name": line.strip(),
                            "issuer": "",
                            "date": ""
                        }
                        
                    elif current_cert:
                        # Extract issuer
                        if re.search(r'(?i)(issued|provided|by|from)', line):
                            current_cert["issuer"] = line.strip()
                            
                        # Extract date
                        elif re.search(r'(?:19|20)\d{2}', line):
                            current_cert["date"] = re.search(r'(?:19|20)\d{2}', line).group()
                            
        if current_cert:
            certifications.append(current_cert)
            
        return certifications

    def categorize_skills(self, text):
        categorized_skills = {category: [] for category in self.skill_patterns.keys()}
        doc = self.nlp(text.lower())
        
        # Extract skills by category
        for category, patterns in self.skill_patterns.items():
            for skill in patterns:
                if skill in text.lower():
                    categorized_skills[category].append(skill)
        
        # Extract additional technical terms
        for token in doc:
            if token.pos_ in ['PROPN', 'NOUN'] and len(token.text) > 2:
                # Check for technical indicators
                text_lower = token.text.lower()
                if any(indicator in text_lower for indicator in ['api', 'sdk', 'framework', 'library']):
                    if not any(text_lower in skills for skills in categorized_skills.values()):
                        categorized_skills['web_technologies'].append(text_lower)
        
        return categorized_skills

    def extract_summary(self, text):
        doc = self.nlp(text)
        first_paragraph = next(doc.sents).text
        
        # Check if the first paragraph looks like a summary
        if len(first_paragraph.split()) > 10:  # Minimum words for a summary
            return first_paragraph
        
        # If not, look for summary section
        summary_markers = ['summary', 'objective', 'profile', 'about']
        for sent in doc.sents:
            if any(marker in sent.text.lower() for marker in summary_markers):
                next_sent = next(doc.sents, None)
                if next_sent and len(next_sent.text.split()) > 10:
                    return next_sent.text
        
        return None

    def analyze_with_openai(self, text):
        """Use OpenAI GPT-3.5-turbo to analyze resume text."""
        try:
            self.logger.info("Starting GPT-3.5-turbo analysis")
            
            # Initialize OpenAI client with API key from environment
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Analyze the following resume text and extract key information in JSON format:

Resume Text:
{text}

Please extract:
1. Personal information (name, contact details)
2. Skills categorized by type (technical, soft skills, etc.)
3. Work experience with details
4. Education history
5. Key achievements
6. Professional summary

Format the response as detailed JSON."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Specifically using GPT-3.5-turbo
                messages=[
                    {"role": "system", "content": "You are a professional resume analyzer. Extract and structure information from resumes accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            self.logger.info("GPT-3.5-turbo analysis completed successfully")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error in GPT-3.5-turbo analysis: {str(e)}")
            return None

    def process_resume(self, pdf_path: str) -> Dict:
        """Process resume and extract all relevant information."""
        try:
            self.logger.info(f"Starting resume processing from: {pdf_path}")
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            self.logger.info("PDF text extraction completed")
            
            if not text or len(text.strip()) == 0:
                self.logger.error("No text could be extracted from the PDF")
                return {
                    "error": "No text could be extracted from the PDF",
                    "extracted_text": "",
                    "entities": {}
                }
            
            # First try GPT-3.5-turbo analysis
            openai_analysis = self.analyze_with_openai(text)
            
            if openai_analysis:
                # Also process with spaCy as backup/supplement
                spacy_analysis = self.process_with_spacy(text)
                
                # Extract entities from spaCy analysis for frontend compatibility
                entities = {
                    'name': [spacy_analysis['personal_info']['name']] if spacy_analysis['personal_info']['name'] else [],
                    'email': spacy_analysis['personal_info']['contact']['email'],
                    'phone': spacy_analysis['personal_info']['contact']['phone'],
                    'skills': [skill for category in spacy_analysis['skills'].values() for skill in category],
                    'education': [f"{edu['degree']} from {edu['institution']} ({edu['year']})" if edu['institution'] and edu['year'] else edu['degree'] for edu in spacy_analysis['education']],
                    'experience': [f"{exp['position']} at {exp['company']} ({', '.join(exp['duration']) if exp['duration'] else 'No date'})" for exp in spacy_analysis['experience']]
                }
                
                result = {
                    'gpt_analysis': openai_analysis,
                    'spacy_analysis': spacy_analysis,
                    'entities': entities,
                    'metadata': {
                        'processed_date': str(datetime.now()),
                        'pdf_path': pdf_path,
                        'text_length': len(text),
                        'model_used': 'gpt-3.5-turbo'
                    }
                }
            else:
                # Fallback to traditional NLP if GPT-3.5-turbo fails
                self.logger.warning("GPT-3.5-turbo analysis failed, falling back to spaCy")
                result = self.process_with_spacy(text)
            
            self.logger.info("Resume processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_resume: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "traceback": str(traceback.format_exc())
            }

    def process_with_spacy(self, text):
        """Process the resume using spaCy as a fallback."""
        try:
            doc = self.nlp(text)
            
            # Extract all information
            contact_info = self.extract_contact_info(text)
            skills = self.categorize_skills(text)
            education = self.extract_education(text)
            experience = self.extract_experience(text)
            certifications = self.extract_certifications(text)
            summary = self.extract_summary(text)
            
            # Get name from PERSON entities
            names = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
            name = names[0] if names else None
            
            # Compile all information
            result = {
                'personal_info': {
                    'name': name,
                    'contact': contact_info
                },
                'summary': summary,
                'skills': skills,
                'education': education,
                'experience': experience,
                'certifications': certifications,
                'metadata': {
                    'processed_date': str(datetime.now()),
                    'text_length': len(text)
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_with_spacy: {str(e)}", exc_info=True)
            raise Exception(f"Error processing resume with spaCy: {str(e)}")

def get_resume_parser():
    return ResumeParser()