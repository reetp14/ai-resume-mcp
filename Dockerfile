# Multi-stage build for MCP Resume Generator Server
FROM ubuntu:22.04 as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install TinyTeX
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh \
    && /root/.TinyTeX/bin/*/tlmgr install \
        moderncv \
        fontawesome \
        academicons \
        multirow \
        arydshln \
        ifoddpage \
        xifthen \
        ifmtarg \
        microtype \
        geometry \
        fancyhdr \
        lastpage \
        tocloft \
        etoolbox \
        xcolor \
        colortbl \
        hhline \
        longtable \
        array \
        booktabs \
        calc \
        ifthen \
        url \
        hyperref \
    && /root/.TinyTeX/bin/*/tlmgr path add

# Add TinyTeX to PATH
ENV PATH="/root/.TinyTeX/bin/x86_64-linux:${PATH}"

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/
COPY .env.example ./

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python3", "-m", "src.server"]

# Production stage
FROM base as production

# Copy only production requirements
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY templates/ ./templates/

# Set production environment
ENV DEBUG=false
ENV PYTHONPATH=/app

CMD ["python3", "-m", "src.server"]

# Development stage
FROM base as development

# Install development dependencies
RUN python3 -m pip install --no-cache-dir -r requirements-dev.txt

# Copy all files including tests
COPY . .

# Set development environment
ENV DEBUG=true
ENV PYTHONPATH=/app

CMD ["python3", "-m", "src.server"]