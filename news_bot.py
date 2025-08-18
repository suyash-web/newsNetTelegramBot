import sys
import random
from datetime import datetime
import telebot
from flask import Flask, request
from newsapi import NewsApiClient
from rapidfuzz import fuzz
from bot_sqlite import SqDB

class NewsBot:
    def __init__(self, token: str, api_key: str, webhook_url: str, db_path: str):
        self.token = token
        self.api_key = api_key
        self.webhook_url = webhook_url

        self.bot = telebot.TeleBot(self.token, threaded=False)
        self.app = Flask(__name__)
        self.db = SqDB(db_path)

        self.user_data = {}

        self._setup_database()
        self.newsapi = NewsApiClient(api_key=self.api_key)
        self.news_sources = self._define_sources()
        self._register_handlers()
        self._setup_routes()

        with self.app.app_context():
            self.bot.remove_webhook()
            self.bot.set_webhook(url=self.webhook_url)

    def _setup_database(self):
        self.db.create_table(
            table_name="news",
            schema="""
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER NOT NULL,
                sources TEXT NOT NULL,
                category TEXT NOT NULL,
                schedule TEXT DEFAULT "No",
                date_added TEXT NOT NULL
            """
        )

    @staticmethod
    def _define_sources():
        return {
            "General": ["BBC News", "CNN", "Reuters", "Associated Press"],
            "Technology": ["TechCrunch", "The Verge", "Wired"],
            "Business": ["Bloomberg", "Business Insider", "CBS News"],
            "Entertainment": ["BuzzFeed", "Entertainment Weekly", "Polygon"],
            "Health": ["Medical News Today", "NBC News", "HuffPost"],
            "Science": ["National Geographic", "New Scientist", "Scientific American"],
            "Sports": ["ESPN", "BBC Sport", "Fox Sports"]
        }

    @staticmethod
    def is_match(a, b, threshold=80):
        return fuzz.partial_ratio(a.lower(), b.lower()) >= threshold

    def get_news_by_category(self, category: str):
        news_dict = {}
        top_headlines = self.newsapi.get_top_headlines(category=category.lower(), language="en")
        for article in top_headlines.get("articles", []):
            source = article["source"]["name"]
            news_dict.setdefault(source, []).append({
                "category": category,
                "headline": article["title"],
                "url": article["url"]
            })
        return news_dict

    def get_filtered_news(self, sources, category, min_count=5):
        news_dict = self.get_news_by_category(category)
        filtered = {
            src: arts for src, arts in news_dict.items()
            if any(self.is_match(src, s) for s in sources)
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

    def _register_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def start(message):
            try:
                markup = telebot.types.InlineKeyboardMarkup()
                for category in self.news_sources.keys():
                    markup.add(telebot.types.InlineKeyboardButton(category, callback_data=f"cat_{category}"))
                self.bot.send_message(message.chat.id, "Choose a category:", reply_markup=markup)
            except Exception as e:
                print(f"Error in start handler: {e}", file=sys.stderr, flush=True)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
        def select_category(call):
            category = call.data.split("_", 1)[1]
            self.user_data[call.from_user.id] = {"category": category, "sources": set()}

            markup = telebot.types.InlineKeyboardMarkup()
            for source in self.news_sources[category]:
                markup.add(telebot.types.InlineKeyboardButton(source, callback_data=f"src_{source}"))
            markup.add(telebot.types.InlineKeyboardButton("✅ Done", callback_data="done"))

            self.bot.edit_message_text(
                f"Category: {category}\nSelect your preferred sources (tap again to unselect):",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("src_"))
        def toggle_source(call):
            source = call.data.split("_", 1)[1]
            uid = call.from_user.id
            category = self.user_data[uid]["category"]

            if source in self.user_data[uid]["sources"]:
                self.user_data[uid]["sources"].remove(source)
            else:
                self.user_data[uid]["sources"].add(source)

            markup = telebot.types.InlineKeyboardMarkup()
            for s in self.news_sources[category]:
                label = f"✅ {s}" if s in self.user_data[uid]["sources"] else s
                markup.add(telebot.types.InlineKeyboardButton(label, callback_data=f"src_{s}"))
            markup.add(telebot.types.InlineKeyboardButton("✅ Done", callback_data="done"))

            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data == "done")
        def finish_selection(call):
            uid = call.from_user.id
            selection = self.user_data[uid]
            category = selection["category"]
            sources = selection["sources"]

            news_items = self.get_filtered_news(list(sources), category)
            if not news_items:
                self.bot.edit_message_text(f"No news found for {category} from selected sources.",
                                           call.message.chat.id, call.message.message_id)
                return

            for item in news_items:
                item["uid"] = uid

            formatted = "\n\n".join(
                f"{i+1}.) Headline: \"{item['headline']}\"\n     Source: \"{item['source']}\"\n     Read more: {item['url']}"
                for i, item in enumerate(news_items)
            )

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🔄 Start Again", callback_data="start_again"),
                telebot.types.InlineKeyboardButton("📅 Schedule", callback_data="schedule")
            )

            self.bot.edit_message_text(
                formatted,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                disable_web_page_preview=True
            )

            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.insert(
                query="INSERT INTO news (uid, sources, category, date_added) VALUES (?, ?, ?, ?)",
                data_tuple=(uid, ", ".join(sources), category, date_now)
            )
            self.db.create_table(
                table_name="schedules",
                schema="""
                    uid INTEGER NOT NULL,
                    sources TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date_added TEXT NOT NULL
                """
            )
            self.db.insert(
                query="INSERT INTO schedules (uid, sources, category, date_added) VALUES (?, ?, ?, ?)",
                data_tuple=(uid, ", ".join(sources), category, date_now)
            )

        @self.bot.callback_query_handler(func=lambda call: call.data == "start_again")
        def start_again(call):
            try:
                self.bot.answer_callback_query(call.id)

                self.bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=None
                )

                start(call.message)
            except Exception as e:
                print(f"Error in start_again handler: {e}", file=sys.stderr, flush=True)

        @self.bot.callback_query_handler(func=lambda call: call.data == "schedule")
        def schedule(call):
            uid = call.from_user.id
            selection = self.user_data[uid]
            category = selection["category"]
            sources = selection["sources"]
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.create_table(
                table_name="schedules",
                schema="""
                    uid INTEGER NOT NULL,
                    sources TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date_added TEXT NOT NULL
                """
            )
            self.db.insert(
                query="""
                    INSERT INTO schedules (uid, sources, category, date_added)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(uid) DO UPDATE SET
                        sources=excluded.sources,
                        category=excluded.category,
                        date_added=excluded.date_added
                """,
                data_tuple=(uid, ", ".join(sources), category, date_now)
            )
            self.bot.answer_callback_query(call.id)

            msg = (
                f"✅ Your selection has been recorded!\n\n"
                f"📰 **Category:** {category}\n"
                f"📡 **Sources:** {', '.join(sources)}\n\n"
                f"📅 Your news is now scheduled to be sent *everyday*."
            )
            self.bot.send_message(uid, msg, parse_mode="Markdown")
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "unsubscribe")
        def unsubscribe(call):
            uid = call.from_user.id
            deleted = self.db.delete_row("schedules", "uid", uid)
            deleted = self.db.delete_row("schedules", "uid", uid)
            if deleted:
                self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                self.bot.send_message(uid, "✅ You have unsubscribed from daily updates.\nHope to see you soon!")
            else:
                self.bot.answer_callback_query(call.id, "You've already been unsubscribed")

    def _setup_routes(self):
        @self.app.route("/", methods=["GET"])
        def index():
            return "Bot is running!"

        @self.app.route("/setwebhook", methods=["GET"])
        def set_webhook():
            self.bot.remove_webhook()
            s = self.bot.set_webhook(url=self.webhook_url)
            return f"Webhook set: {s}"

        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            if request.headers.get('content-type').startswith("application/json"):
                json_str = request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_str)
                self.bot.process_new_updates([update])
                return ''
            else:
                return "Invalid content type", 403
