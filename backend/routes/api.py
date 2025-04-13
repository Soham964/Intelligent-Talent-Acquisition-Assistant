import logging
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from backend.services.sourcing_service import SourcingAgent
from backend.services.screening_service import screen_resume
from backend.services.resume_parser import get_resume_parser
import os
from pathlib import Path
from backend.services.indian_resume_extractor import IndianResumeExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()
sourcing_agent = SourcingAgent()
resume_parser = get_resume_parser()
indian_resume_extractor = IndianResumeExtractor()

class ScreeningRequest(BaseModel):
    resume: dict
    job_description: dict

class EngagementRequest(BaseModel):
    candidate_id: int
    message: str

class SchedulingRequest(BaseModel):
    candidate_id: int
    recruiter_id: int

@router.get("/sourcing")
def sourcing():
    """Endpoint for sourcing candidates."""
    logging.info("Sourcing candidates...")
    return sourcing_agent.crawl_job_platforms()

@router.post("/screening")
def screening(request: ScreeningRequest):
    """Endpoint for screening resumes."""
    logging.info(f"Screening resume: {request.resume}")
    result = screen_resume(request.resume, request.job_description)
    return result

@router.post("/engagement")
def engagement(request: EngagementRequest):
    """Endpoint for engaging with candidates."""
    logging.info(f"Engaging candidate {request.candidate_id} with message: {request.message}")
    return {"message": f"Message sent to candidate {request.candidate_id}", "content": request.message}

@router.post("/scheduling")
def scheduling(request: SchedulingRequest):
    """Endpoint for scheduling interviews."""
    logging.info(f"Scheduling interview for candidate {request.candidate_id} with recruiter {request.recruiter_id}")
    return {"message": f"Interview scheduled for candidate {request.candidate_id} with recruiter {request.recruiter_id}"}

@router.post("/process-resume")
async def process_resume(file: UploadFile = File(...)):
    """Endpoint for processing PDF resumes."""
    try:
        # Create a temporary file to store the uploaded PDF
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the resume
        result = resume_parser.process_resume(temp_path)
        
        # Clean up the temporary file
        os.remove(temp_path)
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/parse-susovan-resume")
async def parse_susovan_resume():
    """Endpoint for processing resumes from the data folder."""
    try:
        # Get the absolute path to the resume using the current working directory
        current_dir = os.getcwd()
        project_root = Path(current_dir).resolve()
        if "backend" in str(project_root):
            project_root = project_root.parent
        data_dir = project_root / "data"
        
        # Check if the data directory exists
        if not data_dir.exists():
            return {
                "status": "error",
                "message": "Data directory not found"
            }
            
        # List all PDF files in the data directory
        pdf_files = list(data_dir.glob("*.pdf"))
        if not pdf_files:
            return {
                "status": "error",
                "message": "No PDF files found in data directory"
            }
            
        # Use the first available PDF file
        resume_path = pdf_files[0]
        logging.info(f"Processing resume from: {resume_path}")
        
        # Process the resume
        result = resume_parser.process_resume(str(resume_path))
        logging.info("Resume processing completed successfully")
        
        return {
            "status": "success",
            "data": result,
            "processed_file": resume_path.name
        }
    except Exception as e:
        error_msg = f"Error processing resume: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/process-indian-resumes")
async def process_indian_resumes():
    """Process Indian resumes and extract specific details (name, phone, education, certifications, experience)."""
    try:
        result = indian_resume_extractor.process_indian_resumes()
        if not result["processed"]:
            return {
                "status": "error",
                "message": "No resumes were processed successfully",
                "details": result
            }
        
        return {
            "status": "success",
            "message": f"Successfully processed {len(result['processed'])} resumes",
            "processed_files": result["processed"],
            "failed_files": result["failed"]
        }
    except Exception as e:
        error_msg = f"Error processing Indian resumes: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/get-all-resumes")
async def get_all_resumes():
    """Get all extracted resume data."""
    try:
        resumes = indian_resume_extractor.get_all_resumes()
        return {
            "status": "success",
            "count": len(resumes),
            "data": resumes
        }
    except Exception as e:
        error_msg = f"Error getting resumes: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/get-resume/{resume_id}")
async def get_resume(resume_id: int):
    """Get a specific resume by ID."""
    try:
        resume = indian_resume_extractor.get_resume_by_id(resume_id)
        if not resume:
            return {
                "status": "error",
                "message": f"Resume with ID {resume_id} not found"
            }
        return {
            "status": "success",
            "data": resume
        }
    except Exception as e:
        error_msg = f"Error getting resume: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/search-resumes")
async def search_resumes(query: str):
    """Search resumes by query string."""
    try:
        results = indian_resume_extractor.search_resumes(query)
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        error_msg = f"Error searching resumes: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/resumes-by-skill/{skill}")
async def get_resumes_by_skill(skill: str):
    """Get resumes that have a specific skill."""
    try:
        results = indian_resume_extractor.get_resumes_by_skill(skill)
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        error_msg = f"Error getting resumes by skill: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }

@router.get("/resumes-by-education/{education}")
async def get_resumes_by_education(education: str):
    """Get resumes with specific education."""
    try:
        results = indian_resume_extractor.get_resumes_by_education(education)
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        error_msg = f"Error getting resumes by education: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg
        }