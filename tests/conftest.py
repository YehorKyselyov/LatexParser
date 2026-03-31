import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from latex_parser.renderer import LatexRenderer, LatexBackend


@pytest.fixture
def mock_renderer():
    """A LatexRenderer mock that returns a fake PNG BytesIO."""
    renderer = MagicMock(spec=LatexRenderer)
    # Minimal valid PNG header
    png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    renderer.render.return_value = BytesIO(png_header)
    renderer.info.return_value = {"backend": "matplotlib", "renderer": "Matplotlib"}
    return renderer


@pytest.fixture
def mock_update():
    """A mock Telegram Update object."""
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.text = "Check this: $x^2$"
    return update


@pytest.fixture
def mock_context():
    """A mock Telegram CallbackContext."""
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    return context


@pytest.fixture
def sample_expressions():
    return [
        "x^2",
        r"\frac{a}{b}",
        r"\int_0^1 f(x) dx",
        r"\sqrt{x^2 + y^2}",
        "E = mc^2",
    ]
