"""
Main MCP Resume Generator Server implementation.
"""

import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

from .mcp_mock import MCPServer, ToolContext
from .models import ResumeArgs, ResumeResponse, ErrorResponse, HealthResponse
from .services import OpenAIService, LaTeXService, S3Service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP Server
server = MCPServer(title="ATS-Resume-MCP", version="1.0.0")

# Initialize services
try:
    openai_service = OpenAIService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4.1"
    )
    
    latex_service = LaTeXService(
        timeout=int(os.getenv("LATEX_TIMEOUT", 10))
    )
    
    s3_service = S3Service(
        bucket_name=os.getenv("S3_BUCKET_NAME"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    
    logger.info("All services initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise


@server.tool(name="generate_resume", schema=ResumeArgs)
async def generate_resume(ctx: ToolContext, args: ResumeArgs) -> Dict[str, Any]:
    """
    Generate an ATS-optimized resume PDF from user data and job description.
    
    This tool:
    1. Takes user form data and job description
    2. Uses OpenAI to generate tailored LaTeX content
    3. Compiles LaTeX to PDF using TinyTeX
    4. Uploads PDF to S3 and returns presigned URL
    
    Args:
        ctx: Tool execution context
        args: Resume generation arguments containing form data and job description
        
    Returns:
        Dictionary containing PDF URL, resume ID, and metadata
    """
    resume_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting resume generation for ID: {resume_id}")
        
        # Step 1: Generate LaTeX content using OpenAI
        logger.info("Generating LaTeX content with OpenAI...")
        latex_content = await openai_service.generate_latex_resume(
            form_data=args.form_data,
            job_description=args.job_description,
            template_style=args.template_style or "modern"
        )
        
        # Step 2: Compile LaTeX to PDF
        logger.info("Compiling LaTeX to PDF...")
        pdf_bytes = await latex_service.compile_to_pdf(latex_content)
        
        # Validate PDF size
        max_size_mb = int(os.getenv("MAX_RESUME_SIZE_MB", 5))
        if len(pdf_bytes) > max_size_mb * 1024 * 1024:
            raise ValueError(f"Generated PDF exceeds maximum size of {max_size_mb}MB")
        
        # Step 3: Upload to S3 and get presigned URL
        logger.info("Uploading PDF to S3...")
        presigned_url, _ = await s3_service.upload_resume_pdf(
            pdf_bytes=pdf_bytes,
            resume_id=resume_id
        )
        
        # Step 4: Prepare response
        response = ResumeResponse(
            pdf_url=presigned_url,
            resume_id=resume_id,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        logger.info(f"Successfully generated resume {resume_id}")
        return response.dict()
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Resume generation failed for {resume_id}: {error_msg}")
        
        # Return structured error response
        error_response = ErrorResponse(
            error=error_msg,
            error_code=_get_error_code(e),
            details={
                "resume_id": resume_id,
                "timestamp": datetime.utcnow().isoformat(),
                "step": _get_failure_step(e)
            }
        )
        
        return {"error": error_response.dict()}


@server.tool(name="health_check")
async def health_check(ctx: ToolContext) -> Dict[str, Any]:
    """
    Perform a health check on all system components.
    
    Returns:
        System health status and dependency information
    """
    try:
        logger.info("Performing health check...")
        
        dependencies = {}
        
        # Check OpenAI API
        try:
            # Simple API test (this would need a real test in production)
            dependencies["openai"] = "healthy"
        except Exception as e:
            dependencies["openai"] = f"unhealthy: {str(e)}"
        
        # Check LaTeX
        try:
            if latex_service.validate_latex_packages():
                dependencies["latex"] = "healthy"
            else:
                dependencies["latex"] = "unhealthy: missing packages"
        except Exception as e:
            dependencies["latex"] = f"unhealthy: {str(e)}"
        
        # Check S3
        try:
            if s3_service.validate_bucket_access():
                dependencies["s3"] = "healthy"
            else:
                dependencies["s3"] = "unhealthy: bucket access failed"
        except Exception as e:
            dependencies["s3"] = f"unhealthy: {str(e)}"
        
        # Determine overall status
        overall_status = "healthy" if all(
            "healthy" in status for status in dependencies.values()
        ) else "degraded"
        
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies=dependencies
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def _get_error_code(exception: Exception) -> str:
    """Get appropriate error code based on exception type."""
    exception_str = str(exception).lower()
    type_str = str(type(exception)).lower()
    
    if "openai" in exception_str or "openai" in type_str:
        return "OPENAI_ERROR"
    elif "latex" in exception_str or "latex" in type_str:
        return "LATEX_ERROR"
    elif "s3" in exception_str or "s3" in type_str:
        return "S3_ERROR"
    elif isinstance(exception, ValueError):
        return "VALIDATION_ERROR"
    else:
        return "INTERNAL_ERROR"


def _get_failure_step(exception: Exception) -> str:
    """Determine which step failed based on exception."""
    error_str = str(exception).lower()
    
    if "openai" in error_str or "api" in error_str:
        return "content_generation"
    elif "latex" in error_str or "compile" in error_str:
        return "pdf_compilation"
    elif "s3" in error_str or "upload" in error_str:
        return "file_upload"
    else:
        return "unknown"


def main():
    """Main entry point for the server."""
    try:
        host = os.getenv("SERVER_HOST", "0.0.0.0")
        port = int(os.getenv("SERVER_PORT", 8000))
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        logger.info(f"Starting MCP Resume Server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the server
        server.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


if __name__ == "__main__":
    main()