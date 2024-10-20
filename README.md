# Telegram Bot for LaTeX Rendering

This is a Telegram bot that renders LaTeX code embedded in text messages and sends the rendered result as an image. It utilizes the Python `matplotlib` library to generate the images from LaTeX code.

## Features

- **/start**: Sends a welcome message and explains the bot's functionality.
- Detects LaTeX code between `$...$` in text messages.
- Renders up to 5 LaTeX expressions per message to prevent spamming.
- Sends the LaTeX-rendered output as an image back to the user.

## Requirements

- Python 3.7+
- `matplotlib` library for rendering LaTeX.
- `python-telegram-bot` library for interacting with Telegram.

## Installation

1. Clone the repository:

2. Install the dependencies:

3. Set up your bot on Telegram:

    - Create a bot using [BotFather](https://core.telegram.org/bots#botfather) and get your bot token.
    - Replace the placeholder `YOUR_TELEGRAM_BOT_TOKEN` in the script with your bot token.

## Usage

1. Run the bot
2. Add the bot to a chat and send a message containing LaTeX code between `$...$`. For example:

    ```
    Here’s an equation: $E = mc^2$
    ```

3. The bot will send back an image of the rendered LaTeX.