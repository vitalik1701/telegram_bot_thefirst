import os
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI
import gspread
from datetime import datetime


from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
gc = gspread.service_account(filename="credentials.json")

sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1M1lJJpHO3RHAudwDZsXQhA29thWT6EbxWwsbcyWwVPY/edit?usp=sharing").sheet1


def make_summary(query, results):
    sources_text = ""

    for index, item in enumerate(results, start=1):
        title = item.get("title", "")
        url = item.get("url", "")
        content = item.get("content", "")

        sources_text += f"""
Источник {index}
Заголовок: {title}
Ссылка: {url}
Текст: {content}
"""

    prompt = f"""
Ты аналитический помощник для Product/Project Manager.

Пользователь спросил:
{query}

Вот результаты поиска:
{sources_text}

Сделай ответ на русском:
1. Краткая суть
2. 3–5 ключевых фактов
3. Почему это важно
4. Ссылки на источники

Не выдумывай факты. Используй только данные из результатов поиска.
"""

    response = openai_client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-исследователь 🔎\n\n"
        "Напиши:\n"
        "/news wildberries\n"
        "/news ozon\n"
        "/news нейросети"
    )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)

    if not query:
        await update.message.reply_text("Напиши тему после команды. Например: /news wildberries")
        return

    await update.message.reply_text(f"Ищу информацию по теме: {query} 🔎")

    try:
        result = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

        results = result.get("results", [])

        if not results:
            await update.message.reply_text("Ничего не нашёл 😕")
            return

        message = f"Вот что я нашёл по теме: {query}\n\n"

        for index, item in enumerate(results, start=1):
            title = item.get("title", "Без названия")
            url = item.get("url", "")
            content = item.get("content", "")

            message += (
                f"{index}. {title}\n"
                f"{content[:250]}...\n"
                f"{url}\n\n"
            )

        await update.message.reply_text(message)

    except Exception as error:
        await update.message.reply_text(f"Ошибка при поиске: {error}")

async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Напиши так:\n/expense кофе 350"
        )
        return

    category = context.args[0]
    amount = context.args[1]

    date = datetime.now().strftime("%d.%m.%Y %H:%M")

    sheet.append_row([date, category, amount])

    await update.message.reply_text(
        f"Расход добавлен ✅\n\nКатегория: {category}\nСумма: {amount}"
    )
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("expense", expense))

app.run_polling()