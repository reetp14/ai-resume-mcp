# MCP Resume Generator Server

A production-ready Model Context Protocol (MCP) server that generates ATS-optimized resumes using OpenAI GPT-4.1, LaTeX compilation, and AWS S3 storage.

## Features

- **AI-Powered Content Generation**: Uses OpenAI GPT-4.1 to create tailored resume content
- **Professional LaTeX Compilation**: Compiles resumes to PDF using TinyTeX and ModernCV template
- **Cloud Storage Integration**: Uploads PDFs to AWS S3 with presigned URLs
- **MCP Protocol Support**: Full compatibility with MCP clients and AI agents
- **Security First**: Sandboxed LaTeX compilation and input validation
- **Docker Ready**: Complete containerization with multi-stage builds
- **Comprehensive Testing**: Unit and integration tests included

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- AWS S3 bucket
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ai-resume-mcp
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

3. **Run with Docker Compose**
```bash
# Development mode
docker-compose up mcp-resume-server

# Production mode
docker-compose --profile production up mcp-resume-server-prod
```

### Manual Installation

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

2. **Install TinyTeX (for LaTeX compilation)**
```bash
# Linux/macOS
wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
# Add to PATH: export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"

# Install required LaTeX packages
tlmgr install moderncv fontawesome academicons multirow arydshln
```

3. **Run the server**
```bash
python -m src.server
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name | Required |
| `SERVER_HOST` | Server host | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `LATEX_TIMEOUT` | LaTeX compilation timeout (seconds) | `10` |
| `MAX_RESUME_SIZE_MB` | Maximum PDF size in MB | `5` |

### AWS S3 Setup

1. Create an S3 bucket for storing resume PDFs
2. Configure bucket permissions for upload/download access
3. Set up IAM user with appropriate S3 permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::your-bucket-name"
        }
    ]
}
```

## API Usage

### MCP Tool: `generate_resume`

Generates an ATS-optimized resume PDF from user data and job description.

**Input Schema:**
```json
{
    "form_data": {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/johndoe",
            "github": "github.com/johndoe"
        },
        "summary": "Experienced software engineer...",
        "skills": ["Python", "JavaScript", "React"],
        "work_experience": [...],
        "education": [...],
        "projects": [...],
        "certifications": [...],
        "languages": [...]
    },
    "job_description": "We are looking for a Senior Software Engineer...",
    "template_style": "modern"
}
```

**Output:**
```json
{
    "pdf_url": "https://s3.amazonaws.com/bucket/presigned-url",
    "resume_id": "uuid-string",
    "generated_at": "2024-01-01T12:00:00Z",
    "expires_at": "2024-01-02T12:00:00Z"
}
```

### MCP Tool: `health_check`

Performs a health check on all system components.

**Output:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "dependencies": {
        "openai": "healthy",
        "latex": "healthy",
        "s3": "healthy"
    }
}
```

## Client Integration Example

```python
from mcp_sdk import MCPClient

# Initialize client
client = MCPClient(server_url="ws://localhost:8000/mcp")

# Generate resume
result = await client.call_tool("generate_resume", {
    "form_data": {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        "skills": ["Python", "AWS", "Docker"],
        "work_experience": [...],
        "education": [...]
    },
    "job_description": "Looking for a DevOps Engineer with Python and AWS experience..."
})

print(f"Resume generated: {result['pdf_url']}")
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_server.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Development with Docker

```bash
# Build development image
docker-compose build mcp-resume-server

# Run with volume mounting for live reload
docker-compose up mcp-resume-server

# Run tests in container
docker-compose exec mcp-resume-server pytest
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agent/     │    │  MCP Resume      │    │   External      │
│   Client        │◄──►│  Generator       │◄──►│   Services      │
└─────────────────┘    │  Server          │    └─────────────────┘
                       └──────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │     Components       │
                    ├──────────────────────┤
                    │ • OpenAI Service     │
                    │ • LaTeX Service      │
                    │ • S3 Service         │
                    │ • Input Validation   │
                    │ • Error Handling     │
                    └──────────────────────┘
```

### Key Components

- **MCP Server**: Handles protocol communication and tool registration
- **OpenAI Service**: Generates tailored resume content using GPT-4o-mini
- **LaTeX Service**: Compiles LaTeX to PDF with security sandboxing
- **S3 Service**: Manages file uploads and presigned URL generation
- **Input Validation**: Pydantic schemas for data validation
- **Error Handling**: Comprehensive error handling and logging

## Security

- **Input Sanitization**: All inputs are validated and sanitized
- **Sandboxed Compilation**: LaTeX runs in a network-disabled subprocess
- **Timeout Protection**: LaTeX compilation has a 10-second timeout
- **File Size Limits**: PDFs are limited to 5MB by default
- **Non-root Container**: Docker container runs as non-root user
- **Secure Dependencies**: Regular dependency updates and security scanning

## Deployment

### Production Deployment

1. **Build production image**
```bash
docker build --target production -t mcp-resume-server:prod .
```

2. **Run with production settings**
```bash
docker run -d \
  --name mcp-resume-server \
  -p 8000:8000 \
  --env-file .env \
  mcp-resume-server:prod
```

3. **With Docker Compose**
```bash
docker-compose --profile production up -d
```

### Scaling Considerations

- Use Redis for job queue when scaling beyond single instance
- Consider using AWS ECS or Kubernetes for container orchestration
- Set up load balancing for multiple instances
- Monitor memory usage during LaTeX compilation

## Troubleshooting

### Common Issues

1. **LaTeX Compilation Fails**
   - Check TinyTeX installation
   - Verify required packages are installed
   - Check LaTeX syntax in generated content

2. **S3 Upload Errors**
   - Verify AWS credentials and permissions
   - Check bucket exists and is accessible
   - Validate network connectivity

3. **OpenAI API Errors**
   - Check API key validity
   - Verify rate limits not exceeded
   - Monitor API usage and billing

### Logs

View server logs:
```bash
# Docker logs
docker-compose logs mcp-resume-server

# Local development
python -m src.server  # Logs to stdout
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the test suite for usage examples