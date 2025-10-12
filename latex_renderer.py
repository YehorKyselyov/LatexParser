"""
LaTeX Renderer Abstraction (WeasyPrint and Matplotlib only)

This module provides a clean interface for LaTeX rendering with two supported backends:
- WeasyPrint (via latex2mathml + weasyprint)
- Matplotlib

Configuration is explicit via the LatexBackend enum. No auto-selection logic.
"""

import os
import logging
import tempfile
from abc import ABC, abstractmethod
from io import BytesIO
from enum import Enum
from typing import Optional


class LatexBackend(Enum):
    WEASYPRINT = "weasyprint"
    MATPLOTLIB = "matplotlib"


def parse_backend(value: str) -> LatexBackend:
    """Parse string to LatexBackend enum (case-insensitive).

    Raises ValueError for invalid values.
    """
    if not isinstance(value, str):
        raise ValueError("LATEX_BACKEND must be a string")
    normalized = value.strip().lower()
    if normalized == LatexBackend.WEASYPRINT.value:
        return LatexBackend.WEASYPRINT
    if normalized == LatexBackend.MATPLOTLIB.value:
        return LatexBackend.MATPLOTLIB
    raise ValueError(
        f"Invalid LATEX_BACKEND='{value}'. Allowed: 'weasyprint', 'matplotlib'."
    )


class LatexRendererBase(ABC):
    """Abstract base class for LaTeX renderers"""
    
    @abstractmethod
    def render(self, latex_string: str) -> BytesIO:
        """
        Render LaTeX string to PNG image stream
        
        Args:
            latex_string: LaTeX expression to render
            
        Returns:
            BytesIO: PNG image data
            
        Raises:
            LatexRenderError: If rendering fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this renderer is available (dependencies installed)"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the renderer"""
        pass
    
    @property
    @abstractmethod
    def quality_score(self) -> int:
        """Quality score (1-5, higher is better)"""
        pass


class LatexRenderError(Exception):
    """Exception raised when LaTeX rendering fails"""
    pass


class WeasyPrintRenderer(LatexRendererBase):
    """High-quality renderer using latex2mathml + WeasyPrint"""
    
    @property
    def name(self) -> str:
        return "WeasyPrint"
    
    @property
    def quality_score(self) -> int:
        return 5
    
    def is_available(self) -> bool:
        try:
            import latex2mathml
            import weasyprint
            return True
        except ImportError:
            return False
    
    def render(self, latex_string: str) -> BytesIO:
        if not self.is_available():
            raise LatexRenderError("WeasyPrint dependencies not available")
        
        try:
            from latex2mathml.converter import convert
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration
            
            # Convert LaTeX to MathML
            mathml = convert(latex_string)
            
            # Create HTML document with proper styling
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        margin: 15px;
                        padding: 15px;
                        font-family: 'STIX Two Math', 'Cambria Math', 'Latin Modern Math', serif;
                        background: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 60px;
                    }}
                    math {{
                        font-size: 28px;
                        color: #000000;
                    }}
                </style>
            </head>
            <body>
                {mathml}
            </body>
            </html>
            """
            
            # Render to PNG
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                font_config = FontConfiguration()
                html_doc = HTML(string=html_content)
                html_doc.write_png(temp_path, font_config=font_config)
                
                # Read image into BytesIO
                with open(temp_path, 'rb') as f:
                    image_stream = BytesIO(f.read())
                    image_stream.seek(0)
                    return image_stream
                    
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            raise LatexRenderError(f"WeasyPrint rendering failed: {e}")


class MatplotlibRenderer(LatexRendererBase):
    """Fallback renderer using matplotlib"""
    
    @property
    def name(self) -> str:
        return "Matplotlib"
    
    @property
    def quality_score(self) -> int:
        return 3
    
    def is_available(self) -> bool:
        try:
            import matplotlib
            return True
        except ImportError:
            return False
    
    def render(self, latex_string: str) -> BytesIO:
        if not self.is_available():
            raise LatexRenderError("Matplotlib not available")
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            
            # Configure matplotlib for better math rendering
            matplotlib.rcParams['mathtext.fontset'] = 'stix'
            matplotlib.rcParams['font.size'] = 14
            
            # Create figure with appropriate sizing
            fig, ax = plt.subplots(figsize=(12, 4))
            
            # Render LaTeX with better styling
            ax.text(0.5, 0.5, f'${latex_string}$', 
                    fontsize=26, 
                    ha='center', 
                    va='center',
                    transform=ax.transAxes,
                    color='black')
            
            ax.axis('off')
            
            # Save with high quality settings
            image_stream = BytesIO()
            fig.savefig(image_stream, 
                        format='png',
                        bbox_inches='tight',
                        facecolor='white',
                        edgecolor='none',
                        dpi=200,
                        pad_inches=0.3)
            
            image_stream.seek(0)
            plt.close(fig)
            
            return image_stream
            
        except Exception as e:
            raise LatexRenderError(f"Matplotlib rendering failed: {e}")


class LatexRenderer:
    """
    Main LaTeX renderer. Explicit backend selection via LatexBackend.

    Usage:
        backend = parse_backend(os.getenv("LATEX_BACKEND", "matplotlib"))
        renderer = LatexRenderer(backend)
        image_stream = renderer.render(latex_string)
    """

    def __init__(self, backend: LatexBackend):
        if not isinstance(backend, LatexBackend):
            raise LatexRenderError("backend must be a LatexBackend enum value")
        self.backend = backend

        if backend == LatexBackend.WEASYPRINT:
            self._renderer: LatexRendererBase = WeasyPrintRenderer()
        else:
            self._renderer = MatplotlibRenderer()

        if not self._renderer.is_available():
            raise LatexRenderError(f"{self._renderer.name} dependencies not available")

    def render(self, latex_string: str) -> BytesIO:
        """Render LaTeX string to PNG image stream"""
        return self._renderer.render(latex_string)

    def info(self) -> dict:
        """Get basic information about the active renderer"""
        return {
            'backend': self.backend.value,
            'renderer': self._renderer.name,
        }