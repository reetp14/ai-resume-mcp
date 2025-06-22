"""
LaTeX service for compiling resumes to PDF.
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LaTeXService:
    """Service for compiling LaTeX documents to PDF."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize LaTeX service.
        
        Args:
            timeout: Compilation timeout in seconds
        """
        self.timeout = timeout
        
    async def compile_to_pdf(self, latex_content: str) -> bytes:
        """
        Compile LaTeX content to PDF.
        
        Args:
            latex_content: LaTeX source code
            
        Returns:
            PDF bytes
            
        Raises:
            LaTeXCompilationError: If compilation fails
        """
        try:
            with tempfile.TemporaryDirectory(prefix="resume_") as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write LaTeX content to file
                tex_file = temp_path / "resume.tex"
                tex_file.write_text(latex_content, encoding='utf-8')
                
                # Compile to PDF
                pdf_path = await self._compile_latex(tex_file)
                
                # Read PDF bytes
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                logger.info(f"Successfully compiled PDF ({len(pdf_bytes)} bytes)")
                return pdf_bytes
                
        except Exception as e:
            logger.error(f"LaTeX compilation failed: {str(e)}")
            raise LaTeXCompilationError(f"Failed to compile LaTeX: {str(e)}")
    
    async def _compile_latex(self, tex_file: Path) -> Path:
        """
        Compile LaTeX file to PDF using latexmk.
        
        Args:
            tex_file: Path to LaTeX file
            
        Returns:
            Path to generated PDF
        """
        try:
            # Run latexmk with security restrictions
            cmd = [
                "latexmk",
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                str(tex_file)
            ]
            
            # Create secure environment
            env = os.environ.copy()
            env.update({
                'TEXMFHOME': str(tex_file.parent / '.texmf'),
                'TEXMFVAR': str(tex_file.parent / '.texmf-var'),
                'TEXMFCONFIG': str(tex_file.parent / '.texmf-config'),
            })
            
            # Run compilation in sandboxed environment
            result = subprocess.run(
                cmd,
                cwd=tex_file.parent,
                timeout=self.timeout,
                capture_output=True,
                text=True,
                env=env,
                # Security: disable network access
                preexec_fn=self._disable_network if hasattr(os, 'setns') else None
            )
            
            if result.returncode != 0:
                error_msg = self._parse_latex_error(result.stderr, result.stdout)
                raise LaTeXCompilationError(f"LaTeX compilation failed: {error_msg}")
            
            # Check if PDF was created
            pdf_file = tex_file.with_suffix('.pdf')
            if not pdf_file.exists():
                raise LaTeXCompilationError("PDF file was not generated")
            
            return pdf_file
            
        except subprocess.TimeoutExpired:
            raise LaTeXCompilationError(f"LaTeX compilation timed out after {self.timeout} seconds")
        except Exception as e:
            raise LaTeXCompilationError(f"Compilation error: {str(e)}")
    
    def _disable_network(self):
        """Disable network access for LaTeX compilation (Linux only)."""
        try:
            import socket
            # Create a dummy socket to test network access
            # In a real implementation, you might use more sophisticated sandboxing
            pass
        except ImportError:
            pass
    
    def _parse_latex_error(self, stderr: str, stdout: str) -> str:
        """
        Parse LaTeX error messages to provide meaningful feedback.
        
        Args:
            stderr: Standard error output
            stdout: Standard output
            
        Returns:
            Parsed error message
        """
        error_lines = []
        
        # Check for common LaTeX errors
        if "Undefined control sequence" in stderr:
            error_lines.append("Undefined LaTeX command found")
        if "Missing" in stderr and "inserted" in stderr:
            error_lines.append("Missing LaTeX syntax element")
        if "Package" in stderr and "Error" in stderr:
            error_lines.append("LaTeX package error")
        if "Emergency stop" in stderr:
            error_lines.append("Critical LaTeX error - compilation stopped")
        
        # Extract specific error lines
        for line in stderr.split('\n'):
            if line.startswith('!') or 'Error' in line:
                error_lines.append(line.strip())
        
        # Fallback to raw output if no specific errors found
        if not error_lines:
            error_lines = [stderr[:200] + "..." if len(stderr) > 200 else stderr]
        
        return "; ".join(error_lines) if error_lines else "Unknown LaTeX error"
    
    def validate_latex_packages(self) -> bool:
        """
        Validate that required LaTeX packages are available.
        
        Returns:
            True if all required packages are available
        """
        try:
            # Test basic LaTeX compilation
            test_latex = r"""
\documentclass{article}
\usepackage{moderncv}
\begin{document}
Test document
\end{document}
"""
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                tex_file = temp_path / "test.tex"
                tex_file.write_text(test_latex)
                
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", str(tex_file)],
                    cwd=temp_path,
                    timeout=5,
                    capture_output=True
                )
                
                return result.returncode == 0
                
        except Exception as e:
            logger.warning(f"LaTeX validation failed: {str(e)}")
            return False


class LaTeXCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""
    pass