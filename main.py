import re
import logging
import os
from telegram import Update, InputFile
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from latex_renderer import LatexRenderer, LatexRenderError, LatexBackend, parse_backend


logging.basicConfig(level=logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Add me to your chats so that I will render your latex code for you.")


async def to_latex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latex_strings = extract_latex_strings(update.message.text)

    if len(latex_strings) > 5:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Stop spamming or you will be punished."
        )
        return

    for latex_string in latex_strings[:5]:
        await process_latex_string(latex_string, update, context)


# Extract LaTeX strings enclosed in $...$
def extract_latex_strings(text):
    return re.findall(r'\$(.*?)\$', text)


async def process_latex_string(latex_string, update, context):
    latex_string = latex_string.strip()
    try:
        # Use the single renderer instance created at startup
        renderer = context.application.bot_data.get('renderer')
        if renderer is None:
            raise RuntimeError("Renderer not initialized. Ensure main sets application.bot_data['renderer'] before adding handlers.")
        
        # Render the LaTeX expression
        image_stream = renderer.render(latex_string)
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(image_stream, filename="latex_image.png")
        )
    except LatexRenderError as e:
        logging.error(f"LaTeX rendering error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sorry, I couldn't render the LaTeX: ${latex_string}$."
        )
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sorry, something went wrong while rendering: ${latex_string}$."
        )


if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
        print("Set it with: set TELEGRAM_TOKEN=your_bot_token")
        exit(1)
    
    # Get the configured LaTeX backend (enum-based)
    backend_env = os.getenv("LATEX_BACKEND", "matplotlib")
    try:
        backend = parse_backend(backend_env)
    except ValueError as e:
        print(str(e))
        print("Defaulting to 'matplotlib'. Set LATEX_BACKEND to 'weasyprint' or 'matplotlib'.")
        backend = LatexBackend.MATPLOTLIB
    
    # Initialize renderer
    try:
        renderer = LatexRenderer(backend)
        renderer_info = renderer.info()
        
        print("LaTeX Bot starting...")
        print(f"Using backend: {backend.value}")
        print(f"Active renderer: {renderer_info['renderer']}")
        
    except LatexRenderError as e:
        print(f"Error initializing renderer: {e}")
        print("Ensure dependencies are installed. For WeasyPrint: pip install latex2mathml weasyprint. For Matplotlib: pip install matplotlib.")
        exit(1)
    
    application = ApplicationBuilder().token(TOKEN).build()

    # Store shared renderer for reuse in handlers
    application.bot_data['renderer'] = renderer

    start_handler = CommandHandler('start', start)
    latex_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), to_latex)

    application.add_handler(start_handler)
    application.add_handler(latex_handler)

    print("\nBot is ready! Send LaTeX expressions like: $x^2 + y^2 = z^2$")
    application.run_polling()
