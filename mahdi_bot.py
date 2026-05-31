import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "7949558988:AAFf8xnn4Q9bXbq01t4jdn7jw4zvMsPVaY0"  # توکنت را اینجا بگذار

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def get_price(symbol):
    ids = {"BTC":"bitcoin","ETH":"ethereum","BNB":"binancecoin","SOL":"solana","XRP":"ripple","DOGE":"dogecoin","TON":"the-open-network"}
    cid = ids.get(symbol.upper())
    if not cid:
        return None
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd&include_24hr_change=true", timeout=10)
        d = r.json()[cid]
        return {"price": d["usd"], "change": d.get("usd_24h_change", 0)}
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("₿ BTC", callback_data="BTC"), InlineKeyboardButton("Ξ ETH", callback_data="ETH")],
        [InlineKeyboardButton("◎ SOL", callback_data="SOL"), InlineKeyboardButton("Ð DOGE", callback_data="DOGE")],
        [InlineKeyboardButton("💎 TON", callback_data="TON"), InlineKeyboardButton("✕ XRP", callback_data="XRP")],
    ]
    await update.message.reply_text("👋 سلام! ربات تحلیل‌گر مهدی\nیه ارز انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data
    data = get_price(symbol)
    if data:
        e = "📈" if data["change"] > 0 else "📉"
        text = f"💰 {symbol}\n💵 قیمت: ${data['price']:,.2f}\n{e} تغییر ۲۴h: {data['change']:.2f}%\n🕐 {datetime.now().strftime('%H:%M')}"
    else:
        text = "❌ خطا در دریافت قیمت"
    kb = [[InlineKeyboardButton("🔙 برگشت", callback_data="back")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("₿ BTC", callback_data="BTC"), InlineKeyboardButton("Ξ ETH", callback_data="ETH")],
        [InlineKeyboardButton("◎ SOL", callback_data="SOL"), InlineKeyboardButton("Ð DOGE", callback_data="DOGE")],
        [InlineKeyboardButton("💎 TON", callback_data="TON"), InlineKeyboardButton("✕ XRP", callback_data="XRP")],
    ]
    await query.message.edit_text("یه ارز انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.upper().strip()
    data = get_price(t)
    if data:
        e = "📈" if data["change"] > 0 else "📉"
        await update.message.reply_text(f"💰 {t}\n💵 ${data['price']:,.2f}\n{e} {data['change']:.2f}%")
    else:
        await update.message.reply_text("❓ بنویس BTC یا ETH یا /start")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ ربات مهدی روشنه!")
    app.run_polling()

if __name__ == "__main__":
    main()
