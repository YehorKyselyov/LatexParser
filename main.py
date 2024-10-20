import matplotlib.pyplot as plt
import re
import logging
from telegram import Update, InputFile
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from io import BytesIO

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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
        image_stream = render_latex_to_image(latex_string)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(image_stream, filename="latex_image.png")
        )
    except Exception as e:
        logging.error(f"Error rendering LaTeX: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sorry, I couldn't render the LaTeX: ${latex_string}$."
        )


def render_latex_to_image(latex_string):
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.text(0.5, 0.5, f'${latex_string}$', fontsize=20, ha='center', va='center')
    ax.axis('off')

    # Save the image to a BytesIO object (in-memory)
    image_stream = BytesIO()
    fig.savefig(image_stream, format='png')
    image_stream.seek(0)
    plt.close(fig)

    return image_stream


if __name__ == '__main__':
    application = ApplicationBuilder().token('YOUR_TELEGRAM_BOT_TOKEN').build()

    start_handler = CommandHandler('start', start)
    latex_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), to_latex)

    application.add_handler(start_handler)
    application.add_handler(latex_handler)

    application.run_polling()
