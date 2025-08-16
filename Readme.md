# Telegram News Bot with SQLite & Flask (Webhook on PythonAnywhere)

This project is a **Telegram Bot** built using [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI), [Flask](https://flask.palletsprojects.com/), and **SQLite**.  
It uses **webhooks** instead of polling to receive updates from Telegram, making it suitable for hosting on platforms like **PythonAnywhere**.

---

## 🚀 Features
- Responds to `/start` and other commands.
- Fetches news from an external API (via your `api_key`).
- Persists user data or preferences in an **SQLite database**.
- Deployed easily on **PythonAnywhere** using Flask as a webhook receiver.
