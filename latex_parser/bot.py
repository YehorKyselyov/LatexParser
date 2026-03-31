import re
import logging

from telegram import Update, InputFile
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from latex_parser.config import Config
from latex_parser.renderer import LatexRenderer, LatexRenderError

logger = logging.getLogger(__name__)


class LatexBot:
    """Telegram bot that renders LaTeX expressions from chat messages."""

    def __init__(self, config: Config, renderer: LatexRenderer) -> None:
        self._config = config
        self._renderer = renderer

    # -- Telegram handlers ---------------------------------------------------

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Add me to your chats so that I will render your latex code for you.",
        )

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        latex_strings = self.extract_latex_strings(update.message.text)
        if not latex_strings:
            return

        if len(latex_strings) > self._config.max_expressions:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Stop spamming or you will be punished.",
            )
            return

        for latex_string in latex_strings:
            await self._process_latex_string(latex_string, update, context)

    async def _process_latex_string(
        self,
        latex_string: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        latex_string = latex_string.strip()
        try:
            image_stream = self._renderer.render(latex_string)
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=InputFile(image_stream, filename="latex_image.png"),
            )
        except LatexRenderError as e:
            logger.error("LaTeX rendering error: %s", e)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Sorry, I couldn't render the LaTeX: ${latex_string}$.",
            )
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Sorry, something went wrong while rendering: ${latex_string}$.",
            )

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def extract_latex_strings(text: str) -> list[str]:
        """Extract LaTeX strings enclosed in $...$."""
        if not text:
            return []
        return re.findall(r'\$(.*?)\$', text)

    # -- Lifecycle ------------------------------------------------------------

    def run(self) -> None:
        """Build the Telegram application and start polling."""
        application = ApplicationBuilder().token(self._config.telegram_token).build()

        application.add_handler(CommandHandler("start", self._handle_start))
        application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message)
        )

        info = self._renderer.info()
        print("LaTeX Bot starting...")
        print(f"Using backend: {info['backend']}")
        print(f"Active renderer: {info['renderer']}")
        print("\nBot is ready! Send LaTeX expressions like: $x^2 + y^2 = z^2$")

        application.run_polling()
