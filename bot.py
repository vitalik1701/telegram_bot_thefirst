import os
from dotenv import load_dotenv
from tavily import TavilyClient

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes



TELEGRAM_TOKEN = ("8280654091:AAEGSFUttxnArFHEVnlYDDayV96bXdj5DVM")
TAVILY_API_KEY = ("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")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


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


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))

app.run_polling()