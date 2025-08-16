from news_bot import NewsBot

bot_instance = NewsBot(
    token="telegram bot token",
    api_key="newsapi key",
    webhook_url="pythonanywhere/webhook/url",
    db_path="/path/to/database"
)

app = bot_instance.app
