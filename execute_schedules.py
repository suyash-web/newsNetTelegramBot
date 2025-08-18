from config import TOKEN, API_KEY, DB_PATH
from bot_sqlite import SqDB
from newsapi import NewsApiClient
from rapidfuzz import fuzz
import random
import telebot

bot = telebot.TeleBot(TOKEN, threaded=False)
db = SqDB(DB_PATH)
newsapi = NewsApiClient(API_KEY)

def is_match(a, b, threshold=80):
    return fuzz.partial_ratio(a.lower(), b.lower()) >= threshold

def get_news_by_category(category: str):
    news_dict = {}
    top_headlines = newsapi.get_top_headlines(category=category.lower(), language="en")
    for article in top_headlines.get("articles", []):
        source = article["source"]["name"]
        news_dict.setdefault(source, []).append({
            "category": category,
            "headline": article["title"],
            "url": article["url"]
        })
    return news_dict

def get_filtered_news(sources, category, min_count=5):
    news_dict = get_news_by_category(category)
    filtered = {
        src: arts for src, arts in news_dict.items()
        if any(is_match(src, s) for s in sources)
    }

    news_list = [
        {"source": src, "headline": art["headline"], "url": art["url"], "category": category}
        for src, arts in filtered.items()
        for art in arts
    ]

    if len(news_list) < min_count:
        all_articles = [
            {"source": src, "headline": art["headline"], "url": art["url"], "category": category}
            for src, arts in news_dict.items()
            for art in arts
            if {"source": src, "headline": art["headline"], "url": art["url"]} not in news_list
        ]
        needed = min_count - len(news_list)
        extra = random.sample(all_articles, min(needed, len(all_articles)))
        news_list.extend(extra)

    return news_list

schedule_data = db.get_all_data_from_table("schedules")

for data in schedule_data:
    uid = data["uid"]
    first_name = data["first_name"]
    sources = data["sources"].split(",")
    category = data["category"]
    news_items = get_filtered_news(sources, category)
    headlines = (
        f"Hello {first_name}, here are you updates for today!\n\n"
        + "\n\n".join(
            f"{i+1}.) Headline: \"{item['headline']}\"\n     Source: \"{item['source']}\"\n     Read more: {item['url']}"
            for i, item in enumerate(news_items)
        )
        + "\n\nHave a great day!"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
            telebot.types.InlineKeyboardButton("❌ Unsubscribe", callback_data="unsubscribe"),
            telebot.types.InlineKeyboardButton("🔧 Customize", callback_data="customize")
        )

    bot.send_message(
        uid,
        headlines,
        reply_markup=markup,
        disable_web_page_preview=True
    )
