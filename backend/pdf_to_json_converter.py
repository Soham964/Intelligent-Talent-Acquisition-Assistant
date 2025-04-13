import os
import json
import re
from PyPDF2 import PdfReader
from pathlib import Path

def clean_text(text):
    """Clean and normalize the text."""
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere with parsing
    text = re.sub(r'[^\w\s.,;:()@+-]', ' ', text)
    return text.strip()

def preprocess_text(text):
    """Preprocess the text to make it easier to parse."""
    # Replace common section headers with standardized versions
    replacements = {
        r'WORK\s*EXPERIENCE': 'EXPERIENCE',
        r'EMPLOYMENT\s*HISTORY': 'EXPERIENCE',
        r'PROFESSIONAL\s*EXPERIENCE': 'EXPERIENCE',
        r'EDUCATION(?:AL)?\s*(?:BACKGROUND|QUALIFICATION)': 'EDUCATION',
        r'SKILLS\s*(?:&|AND)\s*COMPETENCIES': 'SKILLS',
        r'TECHNICAL\s*SKILLS': 'SKILLS',
        r'KEY\s*COMPETENCIES': 'SKILLS',
        r'PROFESSIONAL\s*SUMMARY': 'SUMMARY',
        r'CAREER\s*OBJECTIVE': 'SUMMARY',
        r'OBJECTIVE': 'SUMMARY'
    }
    
    # Add line breaks before section headers to help with parsing
    section_headers = [
        'SUMMARY',
        'EXPERIENCE',
        'EDUCATION',
        'SKILLS',
        'CERTIFICATIONS',
        'PROJECTS'
    ]
    
    # First standardize the headers
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Then add line breaks before headers
    for header in section_headers:
        text = re.sub(f'({header})', r'\n\1', text, flags=re.IGNORECASE)
    
    return text

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return preprocess_text(text)

def find_section_boundaries(text):
    """Find the start and end positions of each section in the text."""
    sections = {}
    section_headers = [
        'SUMMARY',
        'EXPERIENCE',
        'EDUCATION',
        'SKILLS',
        'CERTIFICATIONS',
        'PROJECTS'
    ]
    
    # Split text into sections based on headers
    current_section = None
    current_content = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a section header
        found_header = None
        for header in section_headers:
            if re.search(rf'\b{header}\b', line, re.IGNORECASE):
                found_header = header
                break
                
        if found_header:
            # Save the previous section if it exists
            if current_section and current_content:
                sections[current_section] = current_content
            # Start a new section
            current_section = found_header
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Add the last section
    if current_section and current_content:
        sections[current_section] = current_content
    
    return sections

def extract_contact_info(text):
    """Extract contact information from resume text."""
    contact_info = {}
    
    # Extract email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_matches = re.finditer(email_pattern, text)
    for match in email_matches:
        email = match.group(0)
        if not email.startswith(('http://', 'https://', 'www.')):
            contact_info['email'] = email
            break
    
    # Extract phone
    phone_pattern = r'(?:\+\d{1,3}[-\s]?)?\d{3}[-\s]?\d{3}[-\s]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact_info['phone'] = phone_match.group(0).strip()
    
    # Extract address
    address_pattern = r'\d+\s+[\w\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way)[\w\s,]*\d{5}'
    address_match = re.search(address_pattern, text)
    if address_match:
        contact_info['address'] = address_match.group(0).strip()
    
    return contact_info

def extract_education(sections):
    """Extract education information from sections."""
    education = []
    if 'EDUCATION' in sections:
        content = sections['EDUCATION']
        current_entry = {
            'degree': '',
            'institution': '',
            'year': '',
            'details': []
        }
        
        for line in content:
            line = clean_text(line)
            # Look for degree patterns
            if re.search(r'Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech', line, re.IGNORECASE):
                if current_entry['degree']:  # Save previous entry if it exists
                    education.append(current_entry)
                    current_entry = {'degree': '', 'institution': '', 'year': '', 'details': []}
                current_entry['degree'] = line
            # Look for year patterns
            elif re.search(r'\d{4}', line):
                current_entry['year'] = line
            # Look for institution patterns
            elif re.search(r'University|College|Institute|School', line, re.IGNORECASE):
                current_entry['institution'] = line
            else:
                current_entry['details'].append(line)
        
        # Add the last entry
        if current_entry['degree'] or current_entry['details']:
            education.append(current_entry)
    
    return education

def extract_experience(sections):
    """Extract work experience from sections."""
    experience = []
    if 'EXPERIENCE' in sections:
        content = sections['EXPERIENCE']
        current_entry = {
            'title': '',
            'company': '',
            'duration': '',
            'responsibilities': []
        }
        
        for line in content:
            line = clean_text(line)
            # Look for date patterns
            if re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*-\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', line, re.IGNORECASE):
                if current_entry['title'] or current_entry['responsibilities']:  # Save previous entry if it exists
                    experience.append(current_entry)
                    current_entry = {'title': '', 'company': '', 'duration': '', 'responsibilities': []}
                current_entry['duration'] = line
            # Look for job title patterns (usually capitalized)
            elif re.match(r'^[A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Analyst|Assistant|Director|Coordinator|Specialist)', line):
                current_entry['title'] = line
            # Look for company names (usually ends with Inc., LLC, Ltd., etc.)
            elif re.search(r'(?:Inc\.|LLC|Ltd\.|Limited|Corp\.|Corporation)', line):
                current_entry['company'] = line
            else:
                current_entry['responsibilities'].append(line)
        
        # Add the last entry
        if current_entry['title'] or current_entry['responsibilities']:
            experience.append(current_entry)
    
    return experience

def extract_skills(sections):
    """Extract skills from sections."""
    skills = []
    if 'SKILLS' in sections:
        content = sections['SKILLS']
        for line in content:
            # Split by common skill delimiters
            skill_items = re.split(r'[,;]|\s{2,}', line)
            for skill in skill_items:
                skill = clean_text(skill)
                if skill and len(skill) > 2:  # Avoid single letters or empty strings
                    skills.append(skill)
    
    # If no skills found in dedicated sections, try to extract from summary or other text
    if not skills:
        skill_keywords = [
            'proficient in', 'skilled in', 'expertise in', 'experience with',
            'knowledge of', 'familiar with', 'competent in', 'trained in'
        ]
        for section in sections.values():
            for line in ' '.join(section).split('.'):  # Split into sentences
                for keyword in skill_keywords:
                    if keyword.lower() in line.lower():
                        # Extract skills after the keyword
                        skills_text = line.lower().split(keyword)[1]
                        skill_items = re.split(r'[,;]|\s{2,}', skills_text)
                        for skill in skill_items:
                            skill = clean_text(skill)
                            if skill and len(skill) > 2:
                                skills.append(skill)
    
    return list(set(skills))  # Remove duplicates

def extract_name(text):
    """Extract name from resume text."""
    # Look for common name patterns
    name_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # First Last
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:Resume|CV)',  # First Last Resume
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[\w\s]*@'  # First Last email
    ]
    
    # First try to find name at the beginning of the document
    first_lines = text.split('\n')[:5]  # Check first 5 lines
    for line in first_lines:
        for pattern in name_patterns:
            match = re.search(pattern, line)
            if match and not any(word.lower() in match.group(1).lower() for word in ['resume', 'cv', 'summary', 'school', 'university', 'college']):
                return match.group(1).strip()
    
    # If not found at the beginning, try to find near contact information
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'@|phone|\+\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}', line, re.IGNORECASE):
            # Check the lines around contact info for name
            for j in range(max(0, i-2), min(len(lines), i+3)):
                name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', lines[j])
                if name_match and not any(word.lower() in name_match.group(1).lower() for word in ['resume', 'cv', 'summary', 'school', 'university', 'college']):
                    return name_match.group(1).strip()
    
    return ""

def process_resume_text(text):
    """Process the extracted text into a structured format."""
    # Extract sections
    sections = find_section_boundaries(text)
    
    # Extract name
    name = extract_name(text)
    
    # Extract contact information
    contact_info = extract_contact_info(text)
    
    # Extract education
    education = extract_education(sections)
    
    # Extract experience
    experience = extract_experience(sections)
    
    # Extract skills
    skills = extract_skills(sections)
    
    # Extract summary
    summary = ""
    if 'SUMMARY' in sections:
        summary = ' '.join(sections['SUMMARY'])
    elif len(text.split('\n')) > 0:
        # If no summary section found, use the first paragraph
        first_para = []
        for line in text.split('\n'):
            if not line.strip():
                break
            first_para.append(line.strip())
        summary = ' '.join(first_para)
    
    # Create structured resume data
    resume_data = {
        "name": name,
        "contact_info": contact_info,
        "summary": clean_text(summary),
        "education": education,
        "experience": experience,
        "skills": skills
    }
    
    return resume_data

def convert_pdf_to_json(pdf_path, output_dir):
    """Convert a PDF file to JSON format."""
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Process the text into structured data
        resume_data = process_resume_text(text)
        
        # Create output filename
        pdf_name = os.path.basename(pdf_path)
        json_name = os.path.splitext(pdf_name)[0] + '.json'
        output_path = os.path.join(output_dir, json_name)
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully converted {pdf_name} to JSON")
        return True
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return False

def main():
    # Define paths
    pdf_dir = os.path.join('data')
    output_dir = os.path.join('extracted_indian_resumes')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        convert_pdf_to_json(pdf_path, output_dir)

if __name__ == "__main__":
    main() 