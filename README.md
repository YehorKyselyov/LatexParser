# Telegram Bot for LaTeX Rendering

A Telegram bot that renders LaTeX code embedded in text messages and sends the rendered result as an image. It supports two rendering backends:

- WeasyPrint (latex2mathml + weasyprint) — high quality typesetting
- Matplotlib — reliable fallback

Backend is selected explicitly via the LATEX_BACKEND environment variable.
## Example

Take a look at [@LatexParser_Bot](https://t.me/LatexParser_Bot) in Telegram!

## Features

- /start: Sends a welcome message and explains the bot's functionality
- Detects LaTeX code between `$...$` in text messages
- Renders up to 5 LaTeX expressions per message to prevent spamming
- Sends the rendered output as a PNG image

## Requirements

- Python 3.9+
- `python-telegram-bot`
- One of the renderers:
    - WeasyPrint path: `latex2mathml` + `weasyprint`
    - Matplotlib path: `matplotlib`

Install from the included `requirements.txt`.

## Installation

```powershell
# from project root
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Set your bot token (from BotFather) and choose a backend.

```powershell
# Required
$env:TELEGRAM_TOKEN = "<your_bot_token>"

# Optional: choose renderer backend (weasyprint or matplotlib)
$env:LATEX_BACKEND = "matplotlib"    # default
# or
$env:LATEX_BACKEND = "weasyprint"
```

## Run

```powershell
python .\main.py
```

Then add the bot to a chat and send a message containing LaTeX code between `$...$`, e.g.:

```
Here’s an equation: $E = mc^2$
```

## License

MIT
