"""
OpenAI service for generating resume content.
"""

import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from ..models import FormData

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API to generate resume content."""
    
    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        """Initialize OpenAI service."""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
    async def generate_latex_resume(
        self, 
        form_data: FormData, 
        job_description: str,
        template_style: str = "modern"
    ) -> str:
        """
        Generate LaTeX resume content based on form data and job description.
        
        Args:
            form_data: User's resume data
            job_description: Job description to tailor against
            template_style: Template style preference
            
        Returns:
            Generated LaTeX content
        """
        try:
            prompt = self._build_prompt(form_data, job_description, template_style)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2048
            )
            
            latex_content = response.choices[0].message.content
            
            if not latex_content:
                raise ValueError("Empty response from OpenAI")
                
            logger.info(f"Generated LaTeX content ({len(latex_content)} chars)")
            return latex_content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LaTeX generation."""
        return """You are an expert resume writer and LaTeX specialist. Your task is to generate a professional, ATS-optimized resume in LaTeX format using the moderncv class.

IMPORTANT REQUIREMENTS:
1. Return ONLY valid LaTeX code - no explanations, no markdown formatting
2. Use the moderncv document class with appropriate packages
3. Structure the content to be ATS-friendly with clear sections
4. Tailor the content to match the provided job description
5. Use professional formatting and appropriate fonts
6. Include all provided information without making up details
7. Optimize for both human readability and ATS parsing

The resume should include these sections in order:
- Personal Information (name, email, phone, location, LinkedIn, GitHub)
- Professional Summary (if provided)
- Skills (organized by category when possible)
- Work Experience (reverse chronological order)
- Education
- Projects (if provided)
- Certifications (if provided)
- Languages (if provided)"""

    def _build_prompt(
        self, 
        form_data: FormData, 
        job_description: str,
        template_style: str
    ) -> str:
        """Build the user prompt with form data and job description."""
        
        # Convert form data to a structured format
        form_dict = {
            "personal_info": form_data.personal_info.dict(),
            "summary": form_data.summary,
            "skills": form_data.skills,
            "work_experience": [exp.dict() for exp in form_data.work_experience],
            "education": [edu.dict() for edu in form_data.education],
            "projects": [proj.dict() for proj in form_data.projects] if form_data.projects else [],
            "certifications": form_data.certifications or [],
            "languages": form_data.languages or []
        }
        
        return f"""Generate a professional resume in LaTeX format (moderncv class) using this information:

RESUME DATA:
{self._format_form_data(form_dict)}

JOB DESCRIPTION TO TAILOR AGAINST:
{job_description}

TEMPLATE STYLE: {template_style}

Please create an ATS-optimized resume that:
1. Highlights relevant skills and experience for this specific job
2. Uses appropriate keywords from the job description
3. Maintains professional formatting
4. Is optimized for both ATS systems and human reviewers

Return only the complete LaTeX document code."""

    def _format_form_data(self, form_dict: Dict[str, Any]) -> str:
        """Format form data for the prompt."""
        formatted = []
        
        # Personal Info
        personal = form_dict["personal_info"]
        formatted.append(f"Name: {personal['name']}")
        formatted.append(f"Email: {personal['email']}")
        if personal.get("phone"):
            formatted.append(f"Phone: {personal['phone']}")
        if personal.get("location"):
            formatted.append(f"Location: {personal['location']}")
        if personal.get("linkedin"):
            formatted.append(f"LinkedIn: {personal['linkedin']}")
        if personal.get("github"):
            formatted.append(f"GitHub: {personal['github']}")
        
        # Summary
        if form_dict["summary"]:
            formatted.append(f"\nSummary: {form_dict['summary']}")
        
        # Skills
        formatted.append(f"\nSkills: {', '.join(form_dict['skills'])}")
        
        # Work Experience
        if form_dict["work_experience"]:
            formatted.append("\nWork Experience:")
            for exp in form_dict["work_experience"]:
                formatted.append(f"- {exp['position']} at {exp['company']} ({exp['start_date']} - {exp.get('end_date', 'Present')})")
                for desc in exp['description']:
                    formatted.append(f"  • {desc}")
        
        # Education
        formatted.append("\nEducation:")
        for edu in form_dict["education"]:
            degree_info = f"- {edu['degree']}"
            if edu.get("field"):
                degree_info += f" in {edu['field']}"
            degree_info += f" from {edu['institution']}"
            if edu.get("graduation_date"):
                degree_info += f" ({edu['graduation_date']})"
            formatted.append(degree_info)
        
        # Projects
        if form_dict["projects"]:
            formatted.append("\nProjects:")
            for proj in form_dict["projects"]:
                formatted.append(f"- {proj['name']}: {proj['description']}")
                formatted.append(f"  Technologies: {', '.join(proj['technologies'])}")
        
        # Certifications
        if form_dict["certifications"]:
            formatted.append(f"\nCertifications: {', '.join(form_dict['certifications'])}")
        
        # Languages
        if form_dict["languages"]:
            formatted.append(f"\nLanguages: {', '.join(form_dict['languages'])}")
        
        return "\n".join(formatted)