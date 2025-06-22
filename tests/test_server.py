"""
Tests for the main MCP server functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.server import generate_resume, health_check
from src.models import ResumeArgs, FormData, PersonalInfo, WorkExperience, Education
from src.mcp_mock import ToolContext


@pytest.fixture
def sample_form_data():
    """Create sample form data for testing."""
    return FormData(
        personal_info=PersonalInfo(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1-555-0123",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/johndoe",
            github="github.com/johndoe"
        ),
        summary="Experienced software engineer with 5+ years in full-stack development",
        skills=["Python", "JavaScript", "React", "Node.js", "AWS"],
        work_experience=[
            WorkExperience(
                company="Tech Corp",
                position="Senior Software Engineer",
                start_date="2020-01",
                end_date="Present",
                location="San Francisco, CA",
                description=[
                    "Led development of microservices architecture",
                    "Improved system performance by 40%",
                    "Mentored junior developers"
                ]
            )
        ],
        education=[
            Education(
                institution="University of California",
                degree="Bachelor of Science",
                field="Computer Science",
                graduation_date="2019-05",
                gpa="3.8"
            )
        ]
    )


@pytest.fixture
def sample_resume_args(sample_form_data):
    """Create sample resume arguments for testing."""
    return ResumeArgs(
        form_data=sample_form_data,
        job_description="We are looking for a Senior Software Engineer with experience in Python and AWS...",
        template_style="modern"
    )


@pytest.fixture
def mock_tool_context():
    """Create a mock tool context."""
    context = Mock(spec=ToolContext)
    return context


class TestGenerateResume:
    """Test cases for the generate_resume tool."""
    
    @pytest.mark.asyncio
    async def test_successful_resume_generation(self, sample_resume_args, mock_tool_context):
        """Test successful resume generation flow."""
        mock_latex_content = "\\documentclass{moderncv}\n\\begin{document}\nTest Resume\n\\end{document}"
        mock_pdf_bytes = b"mock_pdf_content"
        mock_presigned_url = "https://s3.amazonaws.com/mock-bucket/resume.pdf"
        mock_resume_id = "test-resume-id"
        
        with patch('src.server.openai_service') as mock_openai, \
             patch('src.server.latex_service') as mock_latex, \
             patch('src.server.s3_service') as mock_s3, \
             patch('uuid.uuid4') as mock_uuid:
            
            # Setup mocks
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value=mock_resume_id)
            
            mock_openai.generate_latex_resume = AsyncMock(return_value=mock_latex_content)
            mock_latex.compile_to_pdf = AsyncMock(return_value=mock_pdf_bytes)
            mock_s3.upload_resume_pdf = AsyncMock(return_value=(mock_presigned_url, mock_resume_id))
            
            # Call the function
            result = await generate_resume(mock_tool_context, sample_resume_args)
            
            # Assertions
            assert "pdf_url" in result
            assert "resume_id" in result
            assert "generated_at" in result
            assert result["pdf_url"] == mock_presigned_url
            assert result["resume_id"] == mock_resume_id
            
            # Verify service calls
            mock_openai.generate_latex_resume.assert_called_once()
            mock_latex.compile_to_pdf.assert_called_once_with(mock_latex_content)
            mock_s3.upload_resume_pdf.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_service_failure(self, sample_resume_args, mock_tool_context):
        """Test handling of OpenAI service failure."""
        with patch('src.server.openai_service') as mock_openai:
            mock_openai.generate_latex_resume = AsyncMock(side_effect=Exception("OpenAI API error"))
            
            result = await generate_resume(mock_tool_context, sample_resume_args)
            
            assert "error" in result
            assert "OPENAI_ERROR" in str(result["error"])
    
    @pytest.mark.asyncio
    async def test_latex_compilation_failure(self, sample_resume_args, mock_tool_context):
        """Test handling of LaTeX compilation failure."""
        mock_latex_content = "\\documentclass{moderncv}\n\\begin{document}\nTest Resume\n\\end{document}"
        
        with patch('src.server.openai_service') as mock_openai, \
             patch('src.server.latex_service') as mock_latex:
            
            mock_openai.generate_latex_resume = AsyncMock(return_value=mock_latex_content)
            mock_latex.compile_to_pdf = AsyncMock(side_effect=Exception("LaTeX compilation failed"))
            
            result = await generate_resume(mock_tool_context, sample_resume_args)
            
            assert "error" in result
            assert "LATEX_ERROR" in str(result["error"])
    
    @pytest.mark.asyncio
    async def test_s3_upload_failure(self, sample_resume_args, mock_tool_context):
        """Test handling of S3 upload failure."""
        mock_latex_content = "\\documentclass{moderncv}\n\\begin{document}\nTest Resume\n\\end{document}"
        mock_pdf_bytes = b"mock_pdf_content"
        
        with patch('src.server.openai_service') as mock_openai, \
             patch('src.server.latex_service') as mock_latex, \
             patch('src.server.s3_service') as mock_s3:
            
            mock_openai.generate_latex_resume = AsyncMock(return_value=mock_latex_content)
            mock_latex.compile_to_pdf = AsyncMock(return_value=mock_pdf_bytes)
            mock_s3.upload_resume_pdf = AsyncMock(side_effect=Exception("S3 upload failed"))
            
            result = await generate_resume(mock_tool_context, sample_resume_args)
            
            assert "error" in result
            assert "S3_ERROR" in str(result["error"])
    
    @pytest.mark.asyncio
    async def test_pdf_size_validation(self, sample_resume_args, mock_tool_context):
        """Test PDF size validation."""
        mock_latex_content = "\\documentclass{moderncv}\n\\begin{document}\nTest Resume\n\\end{document}"
        # Create a mock PDF that's too large (6MB when limit is 5MB)
        mock_pdf_bytes = b"x" * (6 * 1024 * 1024)
        
        with patch('src.server.openai_service') as mock_openai, \
             patch('src.server.latex_service') as mock_latex, \
             patch.dict('os.environ', {'MAX_RESUME_SIZE_MB': '5'}):
            
            mock_openai.generate_latex_resume = AsyncMock(return_value=mock_latex_content)
            mock_latex.compile_to_pdf = AsyncMock(return_value=mock_pdf_bytes)
            
            result = await generate_resume(mock_tool_context, sample_resume_args)
            
            assert "error" in result
            assert "exceeds maximum size" in str(result["error"])


class TestHealthCheck:
    """Test cases for the health_check tool."""
    
    @pytest.mark.asyncio
    async def test_healthy_system(self, mock_tool_context):
        """Test health check with all systems healthy."""
        with patch('src.server.latex_service') as mock_latex, \
             patch('src.server.s3_service') as mock_s3:
            
            mock_latex.validate_latex_packages = Mock(return_value=True)
            mock_s3.validate_bucket_access = Mock(return_value=True)
            
            result = await health_check(mock_tool_context)
            
            assert result["status"] == "healthy"
            assert "dependencies" in result
            assert result["dependencies"]["latex"] == "healthy"
            assert result["dependencies"]["s3"] == "healthy"
            assert result["dependencies"]["openai"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_degraded_system(self, mock_tool_context):
        """Test health check with some systems unhealthy."""
        with patch('src.server.latex_service') as mock_latex, \
             patch('src.server.s3_service') as mock_s3:
            
            mock_latex.validate_latex_packages = Mock(return_value=False)
            mock_s3.validate_bucket_access = Mock(return_value=True)
            
            result = await health_check(mock_tool_context)
            
            assert result["status"] == "degraded"
            assert "unhealthy" in result["dependencies"]["latex"]
            assert result["dependencies"]["s3"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_tool_context):
        """Test health check with exception."""
        with patch('src.server.latex_service') as mock_latex:
            mock_latex.validate_latex_packages = Mock(side_effect=Exception("Service error"))
            
            result = await health_check(mock_tool_context)
            
            assert result["status"] in ["degraded", "unhealthy"]


class TestErrorHandling:
    """Test cases for error handling utilities."""
    
    def test_get_error_code(self):
        """Test error code generation."""
        from src.server import _get_error_code
        
        # Test different exception types
        assert _get_error_code(Exception("OpenAI error")) == "OPENAI_ERROR"
        assert _get_error_code(Exception("LaTeX compilation failed")) == "LATEX_ERROR"
        assert _get_error_code(Exception("S3 upload failed")) == "S3_ERROR"
        assert _get_error_code(ValueError("Invalid input")) == "VALIDATION_ERROR"
        assert _get_error_code(RuntimeError("Unknown error")) == "INTERNAL_ERROR"
    
    def test_get_failure_step(self):
        """Test failure step identification."""
        from src.server import _get_failure_step
        
        # Test different failure scenarios
        assert _get_failure_step(Exception("OpenAI API failed")) == "content_generation"
        assert _get_failure_step(Exception("LaTeX compilation error")) == "pdf_compilation"
        assert _get_failure_step(Exception("S3 upload failed")) == "file_upload"
        assert _get_failure_step(Exception("Unknown error")) == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])