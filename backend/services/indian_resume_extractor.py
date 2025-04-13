import os
import json
import re
from pathlib import Path
import logging
from typing import Dict, List, Optional
from backend.services.resume_parser import get_resume_parser
import fitz

class IndianResumeExtractor:
    def __init__(self):
        self.resume_parser = get_resume_parser()
        current_dir = os.getcwd()
        project_root = Path(current_dir).resolve()
        if "backend" in str(project_root):
            project_root = project_root.parent
        self.data_dir = project_root / "data"
        self.json_dir = project_root / "extracted_indian_resumes"
        self.json_dir.mkdir(exist_ok=True)
        self._load_all_resumes()

    def _mask_personal_info(self, resume_data: Dict) -> Dict:
        """Mask personal information in the resume data."""
        masked_data = resume_data.copy()
        
        if 'spacy_analysis' in masked_data and 'personal_info' in masked_data['spacy_analysis']:
            # Mask name
            if 'name' in masked_data['spacy_analysis']['personal_info']:
                masked_data['spacy_analysis']['personal_info']['name'] = "Candidate"
            
            # Mask contact info
            if 'contact' in masked_data['spacy_analysis']['personal_info']:
                contact = masked_data['spacy_analysis']['personal_info']['contact']
                if 'email' in contact:
                    contact['email'] = "candidate@example.com"
                if 'phone' in contact:
                    contact['phone'] = "XXXXXXXXXX"
                if 'location' in contact:
                    contact['location'] = "Location masked"
        
        return masked_data

    def _load_all_resumes(self):
        """Load all extracted resumes from the JSON directory."""
        self.resumes = []
        try:
            json_files = list(self.json_dir.glob("resume_*_extracted.json"))
            for json_path in json_files:
                with open(json_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                    # Add resume ID from filename
                    resume_id = int(json_path.stem.split('_')[1])
                    resume_data['resume_id'] = resume_id
                    # Mask personal information
                    masked_data = self._mask_personal_info(resume_data)
                    self.resumes.append(masked_data)
            logging.info(f"Loaded {len(self.resumes)} resumes from {self.json_dir}")
        except Exception as e:
            logging.error(f"Error loading resumes: {str(e)}")
            self.resumes = []

    def get_all_resumes(self) -> List[Dict]:
        """Get all loaded resumes with masked personal information."""
        return self.resumes

    def get_resume_by_id(self, resume_id: int) -> Optional[Dict]:
        """Get a specific resume by its ID with masked personal information."""
        for resume in self.resumes:
            if resume.get('resume_id') == resume_id:
                return resume
        return None

    def search_resumes(self, query: str) -> List[Dict]:
        """Search resumes by query string with masked personal information."""
        results = []
        query = query.lower()
        
        for resume in self.resumes:
            # Search in skills
            if 'spacy_analysis' in resume and 'skills' in resume['spacy_analysis']:
                skills = resume['spacy_analysis']['skills']
                if any(query in str(skill).lower() for skill in skills.values()):
                    results.append(resume)
                    continue
            
            # Search in education
            if 'spacy_analysis' in resume and 'education' in resume['spacy_analysis']:
                education = resume['spacy_analysis']['education']
                if any(query in str(edu).lower() for edu in education):
                    results.append(resume)
                    continue
            
            # Search in experience
            if 'spacy_analysis' in resume and 'experience' in resume['spacy_analysis']:
                experience = resume['spacy_analysis']['experience']
                if any(query in str(exp).lower() for exp in experience):
                    results.append(resume)
                    continue
        
        return results

    def get_resumes_by_skill(self, skill: str) -> List[Dict]:
        """Get resumes that have a specific skill."""
        results = []
        skill = skill.lower()
        
        for resume in self.resumes:
            if 'spacy_analysis' in resume and 'skills' in resume['spacy_analysis']:
                skills = resume['spacy_analysis']['skills']
                for category, skill_list in skills.items():
                    if any(skill in s.lower() for s in skill_list):
                        results.append(resume)
                        break
        
        return results

    def get_resumes_by_education(self, education: str) -> List[Dict]:
        """Get resumes with specific education."""
        results = []
        education = education.lower()
        
        for resume in self.resumes:
            if 'spacy_analysis' in resume and 'education' in resume['spacy_analysis']:
                edu_list = resume['spacy_analysis']['education']
                if any(education in str(edu).lower() for edu in edu_list):
                    results.append(resume)
        
        return results

    def extract_phone_number(self, text: str) -> str:
        """Extract phone number using Indian phone number patterns."""
        # Common Indian phone number patterns
        patterns = [
            r'\+91[-\s]?\d{10}',  # +91 followed by 10 digits
            r'0?\d{10}',          # 10 digits with optional 0 prefix
            r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'  # XXX-XXX-XXXX format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group().replace(' ', '').replace('-', '')
        return ""

    def extract_details(self, resume_data: Dict) -> Dict:
        """Extract specific details from the resume data."""
        extracted = {
            "name": "",
            "phone_number": "",
            "education": [],
            "certifications": [],
            "experience": []
        }

        # Extract name
        if "name" in resume_data:
            extracted["name"] = resume_data["name"]
        
        # Extract phone from contact info
        if "contact_info" in resume_data:
            extracted["phone_number"] = self.extract_phone_number(str(resume_data["contact_info"]))
        
        # Extract education
        if "education" in resume_data:
            for edu in resume_data["education"]:
                education_entry = {
                    "degree": edu.get("degree", ""),
                    "institution": edu.get("institution", ""),
                    "year": edu.get("year", ""),
                    "score": edu.get("score", "")
                }
                extracted["education"].append(education_entry)
        
        # Extract certifications
        if "certifications" in resume_data:
            for cert in resume_data["certifications"]:
                cert_entry = {
                    "name": cert.get("name", ""),
                    "issuer": cert.get("issuer", ""),
                    "date": cert.get("date", "")
                }
                extracted["certifications"].append(cert_entry)
        
        # Extract experience
        if "experience" in resume_data:
            for exp in resume_data["experience"]:
                exp_entry = {
                    "company": exp.get("company", ""),
                    "position": exp.get("position", ""),
                    "duration": exp.get("duration", ""),
                    "responsibilities": exp.get("responsibilities", [])
                }
                extracted["experience"].append(exp_entry)
        
        return extracted

    def process_indian_resumes(self) -> Dict:
        """Process Indian resumes and extract specific details."""
        results = {
            "status": "success",
            "processed": [],
            "failed": []
        }

        # Look for Indian resumes
        indian_resume_patterns = [
            "Indian_Sample_Resumes_Cleaned.pdf"
        ]

        for resume_file in indian_resume_patterns:
            pdf_path = self.data_dir / resume_file
            if not pdf_path.exists():
                results["failed"].append(f"{resume_file} - File not found")
                continue

            try:
                # Process the resume
                doc = fitz.open(str(pdf_path))
                
                # Process each page as a separate resume
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    
                    # Create a temporary PDF with just this page
                    temp_doc = fitz.open()
                    temp_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    temp_path = self.data_dir / f"temp_resume_{page_num}.pdf"
                    temp_doc.save(temp_path)
                    temp_doc.close()
                    
                    try:
                        # Process the single-page resume
                        resume_data = self.resume_parser.process_resume(str(temp_path))
                        
                        # Save to JSON
                        json_path = self.json_dir / f"resume_{page_num + 1}_extracted.json"
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(resume_data, f, indent=2, ensure_ascii=False)
                        
                        results["processed"].append(f"Page {page_num + 1} of {resume_file}")
                    except Exception as e:
                        results["failed"].append(f"Page {page_num + 1} of {resume_file} - {str(e)}")
                    finally:
                        # Clean up temporary file
                        if temp_path.exists():
                            temp_path.unlink()
                
                doc.close()
                
            except Exception as e:
                logging.error(f"Error processing {resume_file}: {str(e)}")
                results["failed"].append(f"{resume_file} - {str(e)}")

        # Reload all resumes after processing
        self._load_all_resumes()
        return results 