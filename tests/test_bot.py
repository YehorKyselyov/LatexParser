import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from latex_parser.bot import LatexBot
from latex_parser.config import Config
from latex_parser.renderer import LatexBackend, LatexRenderError


@pytest.fixture
def config():
    return Config(
        telegram_token="fake-token",
        backend=LatexBackend.MATPLOTLIB,
        max_expressions=5,
    )


@pytest.fixture
def bot(config, mock_renderer):
    return LatexBot(config, mock_renderer)


class TestExtractLatexStrings:
    def test_single_expression(self):
        assert LatexBot.extract_latex_strings("Here is $x^2$ done") == ["x^2"]

    def test_multiple_expressions(self):
        result = LatexBot.extract_latex_strings("$a$ and $b$ and $c$")
        assert result == ["a", "b", "c"]

    def test_no_expressions(self):
        assert LatexBot.extract_latex_strings("No latex here") == []

    def test_empty_string(self):
        assert LatexBot.extract_latex_strings("") == []

    def test_none_input(self):
        assert LatexBot.extract_latex_strings(None) == []

    def test_empty_dollars(self):
        assert LatexBot.extract_latex_strings("$$") == [""]

    def test_complex_expression(self):
        text = r"Consider $\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$ please"
        result = LatexBot.extract_latex_strings(text)
        assert len(result) == 1
        assert "int" in result[0]

    def test_adjacent_expressions(self):
        result = LatexBot.extract_latex_strings("$a$$b$")
        assert result == ["a", "b"]


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_renders_single_expression(self, bot, mock_update, mock_context):
        mock_update.message.text = "Check $x^2$"

        await bot._handle_message(mock_update, mock_context)

        mock_context.bot.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_expressions_does_nothing(self, bot, mock_update, mock_context):
        mock_update.message.text = "No latex here"

        await bot._handle_message(mock_update, mock_context)

        mock_context.bot.send_photo.assert_not_called()
        mock_context.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_spam_guard(self, bot, mock_update, mock_context):
        # 6 expressions > max_expressions (5)
        mock_update.message.text = "$a$ $b$ $c$ $d$ $e$ $f$"

        await bot._handle_message(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "spam" in call_args.kwargs["text"].lower() or "spamming" in call_args.kwargs["text"].lower()
        mock_context.bot.send_photo.assert_not_called()

    @pytest.mark.asyncio
    async def test_exactly_max_expressions_allowed(self, bot, mock_update, mock_context):
        mock_update.message.text = "$a$ $b$ $c$ $d$ $e$"

        await bot._handle_message(mock_update, mock_context)

        assert mock_context.bot.send_photo.call_count == 5

    @pytest.mark.asyncio
    async def test_render_error_sends_error_message(
        self, bot, mock_update, mock_context, mock_renderer
    ):
        mock_update.message.text = "$bad$"
        mock_renderer.render.side_effect = LatexRenderError("fail")

        await bot._handle_message(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        assert "couldn't render" in mock_context.bot.send_message.call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_unexpected_error_sends_error_message(
        self, bot, mock_update, mock_context, mock_renderer
    ):
        mock_update.message.text = "$bad$"
        mock_renderer.render.side_effect = RuntimeError("unexpected")

        await bot._handle_message(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        assert "went wrong" in mock_context.bot.send_message.call_args.kwargs["text"]


class TestHandleStart:
    @pytest.mark.asyncio
    async def test_sends_welcome(self, bot, mock_update, mock_context):
        await bot._handle_start(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        assert "Add me" in mock_context.bot.send_message.call_args.kwargs["text"]
