"""
LaTeX Renderer Abstraction (WeasyPrint and Matplotlib)

Provides a clean interface for LaTeX rendering with two supported backends:
- WeasyPrint (via latex2mathml + weasyprint)
- Matplotlib
"""

import os
import logging
import tempfile
from abc import ABC, abstractmethod
from io import BytesIO
from enum import Enum

logger = logging.getLogger(__name__)


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
    for member in LatexBackend:
        if normalized == member.value:
            return member
    raise ValueError(
        f"Invalid LATEX_BACKEND='{value}'. Allowed: {[b.value for b in LatexBackend]}."
    )


class LatexRenderError(Exception):
    """Exception raised when LaTeX rendering fails."""


class LatexRendererBase(ABC):
    """Abstract base class for LaTeX renderers."""

    def __init__(self) -> None:
        self._available: bool | None = None

    @abstractmethod
    def _render(self, latex_string: str) -> BytesIO:
        """Backend-specific rendering implementation."""

    @abstractmethod
    def _check_available(self) -> bool:
        """Check if backend dependencies are installed."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the renderer."""

    def is_available(self) -> bool:
        """Cached availability check."""
        if self._available is None:
            self._available = self._check_available()
        return self._available

    def render(self, latex_string: str) -> BytesIO:
        """Render a LaTeX string to a PNG image stream.

        Raises:
            LatexRenderError: On empty input or rendering failure.
        """
        if not isinstance(latex_string, str) or not latex_string.strip():
            raise LatexRenderError("LaTeX string must be a non-empty string")
        if not self.is_available():
            raise LatexRenderError(f"{self.name} dependencies not available")
        return self._render(latex_string.strip())


class WeasyPrintRenderer(LatexRendererBase):
    """High-quality renderer using latex2mathml + WeasyPrint."""

    @property
    def name(self) -> str:
        return "WeasyPrint"

    def _check_available(self) -> bool:
        try:
            import latex2mathml  # noqa: F401
            import weasyprint  # noqa: F401
            return True
        except (ImportError, OSError):
            return False

    def _render(self, latex_string: str) -> BytesIO:
        try:
            from latex2mathml.converter import convert
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration

            mathml = convert(latex_string)

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

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                font_config = FontConfiguration()
                html_doc = HTML(string=html_content)
                html_doc.write_png(temp_path, font_config=font_config)

                with open(temp_path, 'rb') as f:
                    image_stream = BytesIO(f.read())
                    image_stream.seek(0)
                    return image_stream
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except LatexRenderError:
            raise
        except Exception as e:
            raise LatexRenderError(f"WeasyPrint rendering failed: {e}") from e


class MatplotlibRenderer(LatexRendererBase):
    """Renderer using matplotlib."""

    @property
    def name(self) -> str:
        return "Matplotlib"

    def _check_available(self) -> bool:
        try:
            import matplotlib  # noqa: F401
            return True
        except ImportError:
            return False

    def _render(self, latex_string: str) -> BytesIO:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            matplotlib.rcParams['mathtext.fontset'] = 'stix'
            matplotlib.rcParams['font.size'] = 14

            fig, ax = plt.subplots(figsize=(12, 4))

            ax.text(0.5, 0.5, f'${latex_string}$',
                    fontsize=26,
                    ha='center',
                    va='center',
                    transform=ax.transAxes,
                    color='black')

            ax.axis('off')

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

        except LatexRenderError:
            raise
        except Exception as e:
            raise LatexRenderError(f"Matplotlib rendering failed: {e}") from e


class LatexRenderer:
    """Facade for LaTeX rendering with explicit backend selection.

    Usage:
        renderer = LatexRenderer(LatexBackend.MATPLOTLIB)
        image_stream = renderer.render("x^2 + y^2 = z^2")
    """

    def __init__(self, backend: LatexBackend) -> None:
        if not isinstance(backend, LatexBackend):
            raise LatexRenderError("backend must be a LatexBackend enum value")

        self._backend = backend
        renderers = {
            LatexBackend.WEASYPRINT: WeasyPrintRenderer,
            LatexBackend.MATPLOTLIB: MatplotlibRenderer,
        }
        self._renderer: LatexRendererBase = renderers[backend]()

        if not self._renderer.is_available():
            raise LatexRenderError(f"{self._renderer.name} dependencies not available")

    @property
    def backend(self) -> LatexBackend:
        return self._backend

    def render(self, latex_string: str) -> BytesIO:
        """Render LaTeX string to PNG image stream."""
        return self._renderer.render(latex_string)

    def info(self) -> dict:
        """Get information about the active renderer."""
        return {
            'backend': self._backend.value,
            'renderer': self._renderer.name,
        }
