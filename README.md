# 📰 Telegram News Bot with SQLite & Flask (Webhook on PythonAnywhere)

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey)
![SQLite](https://img.shields.io/badge/SQLite-DB-blue)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue)

This project is a **Telegram News Bot** built using [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI), [Flask](https://flask.palletsprojects.com/), and **SQLite**.  
It uses **webhooks** instead of polling to receive updates from Telegram, making it suitable for hosting on platforms like **PythonAnywhere**.

---

## 🚀 Features
- ⚡ Responds to `/start` and interactive button clicks.
- 📰 Fetches latest news from [NewsAPI](https://newsapi.org/) using your API key.
- 💾 Stores user preferences (categories, sources, schedules) in **SQLite database**.
- 📅 Lets users schedule daily news updates at 8 AM IST.
- ❌ Users can unsubscribe anytime with a button click.
- 🌐 Hosted on **PythonAnywhere** with Flask handling the webhook.

---

## 📂 Project Structure
```
.
├── bot_sqlite.py        # SQLite database wrapper (SqDB class)
├── config.py            # Stores API keys, tokens, and configs
├── execute_schedules.py # Daily scheduler script (sends scheduled news)
├── news_bot.py          # Main bot implementation (Flask + Telebot)
├── news.db              # SQLite database (created at runtime)
└── README.md            # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/suyash-web/newsNetTelegramBot.git
cd newsNetTelegramBot
```

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Typical dependencies:
```txt
flask
pyTelegramBotAPI
newsapi-python
rapidfuzz
```

### 4. Configure API Keys
Edit `config.py`:
```python
TOKEN = "your-telegram-bot-token"
API_KEY = "your-newsapi-key"
WEBHOOK_URL = "https://<your-username>.pythonanywhere.com/webhook"
DB_PATH = "news.db"
```

Get:
- **Telegram Bot Token** → from [BotFather](https://t.me/botfather).  
- **NewsAPI Key** → from [https://newsapi.org](https://newsapi.org).

---

## 🌐 Deployment on PythonAnywhere

1. Upload project files (`news_bot.py`, `bot_sqlite.py`, `config.py`, etc.) to PythonAnywhere.  
2. Create a **Flask Web App** in the **Web tab**.  
3. Point WSGI file to your `flask_app.py`.  
4. Set webhook:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<your-username>.pythonanywhere.com/webhook
   ```
5. Check logs (`/var/log/.../error.log` & `access.log`) if something goes wrong.

---

## 💡 Usage

- `/start` → Choose a **category**.  
- Select your preferred **sources**.  
- ✅ Done → Bot fetches and sends news.  
- 🔄 **Start Again** → Restart the selection flow.  
- 📅 **Schedule** → Subscribe to daily 8 AM news.  
- ❌ **Unsubscribe** → Stop daily updates.  

---

## 🛠 Example Database Schema

### `news` table
| id | uid       | sources      | category   | date_added          |
|----|-----------|--------------|------------|---------------------|
| 1  | 919867993 | BBC, CNN     | General    | 2025-08-18 08:00:00 |

### `schedules` table
| uid       | sources      | category   | date_added          |
|-----------|--------------|------------|---------------------|
| 919867993 | BBC, CNN     | General    | 2025-08-18 08:00:00 |

---

## 📝 To-Do / Improvements
- [ ] Add multiple scheduling times (morning/evening).  
- [ ] Support more news APIs (NYTimes, Guardian).  
- [ ] Add keyword-based personalized news.  
- [ ] Deploy on AWS Lambda or Fly.io for scalability.  

---

## 📜 License
MIT License. Free to use and modify.

---

## 🙌 Acknowledgements
- [Telegram Bot API](https://core.telegram.org/bots/api)  
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)  
- [NewsAPI](https://newsapi.org)  
