import pytest
from io import BytesIO

from latex_parser.renderer import (
    LatexBackend,
    LatexRenderError,
    LatexRenderer,
    MatplotlibRenderer,
    WeasyPrintRenderer,
    parse_backend,
)


class TestParseBackend:
    def test_matplotlib(self):
        assert parse_backend("matplotlib") == LatexBackend.MATPLOTLIB

    def test_weasyprint(self):
        assert parse_backend("weasyprint") == LatexBackend.WEASYPRINT

    def test_case_insensitive(self):
        assert parse_backend("MATPLOTLIB") == LatexBackend.MATPLOTLIB
        assert parse_backend("WeasyPrint") == LatexBackend.WEASYPRINT

    def test_strips_whitespace(self):
        assert parse_backend("  matplotlib  ") == LatexBackend.MATPLOTLIB

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid LATEX_BACKEND"):
            parse_backend("pdflatex")

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="must be a string"):
            parse_backend(123)


class TestMatplotlibRenderer:
    def test_is_available(self):
        renderer = MatplotlibRenderer()
        assert renderer.is_available() is True

    def test_name(self):
        assert MatplotlibRenderer().name == "Matplotlib"

    def test_availability_is_cached(self):
        renderer = MatplotlibRenderer()
        result1 = renderer.is_available()
        result2 = renderer.is_available()
        assert result1 == result2
        assert renderer._available is not None

    def test_render_returns_png(self):
        renderer = MatplotlibRenderer()
        result = renderer.render("x^2")

        assert isinstance(result, BytesIO)
        header = result.read(8)
        assert header == b'\x89PNG\r\n\x1a\n', "Output should be a valid PNG"

    def test_render_empty_string_raises(self):
        renderer = MatplotlibRenderer()
        with pytest.raises(LatexRenderError, match="non-empty"):
            renderer.render("")

    def test_render_whitespace_only_raises(self):
        renderer = MatplotlibRenderer()
        with pytest.raises(LatexRenderError, match="non-empty"):
            renderer.render("   ")

    def test_render_none_raises(self):
        renderer = MatplotlibRenderer()
        with pytest.raises(LatexRenderError, match="non-empty"):
            renderer.render(None)

    def test_render_various_expressions(self, sample_expressions):
        renderer = MatplotlibRenderer()
        for expr in sample_expressions:
            result = renderer.render(expr)
            assert isinstance(result, BytesIO)
            assert result.read(4) == b'\x89PNG'
            result.seek(0)


def _weasyprint_available() -> bool:
    try:
        return WeasyPrintRenderer().is_available()
    except Exception:
        return False


class TestWeasyPrintRenderer:
    @pytest.fixture
    def renderer(self):
        return WeasyPrintRenderer()

    def test_name(self, renderer):
        assert renderer.name == "WeasyPrint"

    def test_empty_string_raises(self, renderer):
        with pytest.raises(LatexRenderError, match="non-empty"):
            renderer.render("")

    @pytest.mark.skipif(
        not _weasyprint_available(),
        reason="WeasyPrint dependencies not installed",
    )
    def test_render_returns_png(self, renderer):
        result = renderer.render("x^2")
        assert isinstance(result, BytesIO)
        assert result.read(8) == b'\x89PNG\r\n\x1a\n'


class TestLatexRenderer:
    def test_matplotlib_facade(self):
        renderer = LatexRenderer(LatexBackend.MATPLOTLIB)
        assert renderer.backend == LatexBackend.MATPLOTLIB
        assert renderer.info()["renderer"] == "Matplotlib"

    def test_render_through_facade(self):
        renderer = LatexRenderer(LatexBackend.MATPLOTLIB)
        result = renderer.render("E = mc^2")
        assert isinstance(result, BytesIO)
        assert result.read(4) == b'\x89PNG'

    def test_invalid_backend_type_raises(self):
        with pytest.raises(LatexRenderError, match="must be a LatexBackend"):
            LatexRenderer("matplotlib")

    def test_info_structure(self):
        renderer = LatexRenderer(LatexBackend.MATPLOTLIB)
        info = renderer.info()
        assert "backend" in info
        assert "renderer" in info
