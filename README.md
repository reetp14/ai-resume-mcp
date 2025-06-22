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
git clone https://github.com/reetp14/ai-resume-mcp.git
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
|----------|-------------|----------|
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

## 🚀 **Live Demo**

Try the AI Resume Generator:
- **Input**: Your profile data + job description
- **AI Processing**: GPT-4.1 analyzes and optimizes content
- **Output**: Professional PDF resume in seconds

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
- **OpenAI Service**: Generates tailored resume content using GPT-4.1
- **LaTeX Service**: Compiles LaTeX to PDF with security sandboxing
- **S3 Service**: Manages file uploads and presigned URL generation
- **Input Validation**: Pydantic schemas for data validation
- **Error Handling**: Comprehensive error handling and logging

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the test suite for usage examples