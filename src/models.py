"""
Pydantic models for the MCP Resume Generator Server.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PersonalInfo(BaseModel):
    """Personal information section of the resume."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    linkedin: Optional[str] = Field(None, max_length=200)
    github: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=200)


class WorkExperience(BaseModel):
    """Work experience entry."""
    company: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    start_date: str = Field(..., max_length=20)
    end_date: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    description: List[str] = Field(..., min_items=1, max_items=10)


class Education(BaseModel):
    """Education entry."""
    institution: str = Field(..., min_length=1, max_length=100)
    degree: str = Field(..., min_length=1, max_length=100)
    field: Optional[str] = Field(None, max_length=100)
    graduation_date: Optional[str] = Field(None, max_length=20)
    gpa: Optional[str] = Field(None, max_length=10)
    location: Optional[str] = Field(None, max_length=100)


class Project(BaseModel):
    """Project entry."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    technologies: List[str] = Field(..., min_items=1, max_items=20)
    url: Optional[str] = Field(None, max_length=200)
    date: Optional[str] = Field(None, max_length=20)


class FormData(BaseModel):
    """Complete form data for resume generation."""
    personal_info: PersonalInfo
    summary: Optional[str] = Field(None, max_length=500)
    skills: List[str] = Field(..., min_items=1, max_items=50)
    work_experience: List[WorkExperience] = Field(..., min_items=0, max_items=20)
    education: List[Education] = Field(..., min_items=1, max_items=10)
    projects: Optional[List[Project]] = Field(None, max_items=10)
    certifications: Optional[List[str]] = Field(None, max_items=20)
    languages: Optional[List[str]] = Field(None, max_items=10)


class ResumeArgs(BaseModel):
    """Arguments for the generate_resume tool."""
    form_data: FormData = Field(..., description="User's resume data")
    job_description: str = Field(
        ..., 
        min_length=50, 
        max_length=5000,
        description="Job description to tailor the resume against"
    )
    template_style: Optional[str] = Field(
        "modern", 
        description="Resume template style (modern, professional, creative)"
    )

    @validator('job_description')
    def validate_job_description(cls, v):
        """Validate job description contains meaningful content."""
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters')
        return v.strip()


class ResumeResponse(BaseModel):
    """Response from the generate_resume tool."""
    pdf_url: str = Field(..., description="Presigned S3 URL for the generated PDF")
    resume_id: str = Field(..., description="Unique identifier for the generated resume")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for categorization")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")