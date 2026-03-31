import logging
import sys

from latex_parser.config import Config
from latex_parser.renderer import LatexRenderer, LatexRenderError
from latex_parser.bot import LatexBot

logging.basicConfig(level=logging.WARNING)


def main() -> None:
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    try:
        renderer = LatexRenderer(config.backend)
    except LatexRenderError as e:
        print(f"Error initializing renderer: {e}")
        sys.exit(1)

    bot = LatexBot(config, renderer)
    bot.run()


if __name__ == "__main__":
    main()
