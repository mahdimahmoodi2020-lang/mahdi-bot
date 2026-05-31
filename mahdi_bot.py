#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تحلیل‌گر ارز دیجیتال - مهدی
Mahdi Crypto Analysis Telegram Bot
"""

import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ==================== تنظیمات ====================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # ← توکن جدید از BotFather را اینجا بگذار
BOT_NAME = "مهدی"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== دریافت قیمت‌ها ====================

def get_crypto_price(symbol: str) -> dict:
    """دریافت قیمت ارز دیجیتال از CoinGecko"""
    coin_ids = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "USDT": "tether",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "TRX": "tron",
        "TON": "the-open-network",
    }
    
    coin_id = coin_ids.get(symbol.upper())
    if not coin_id:
        return None
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {"localization": "false", "tickers": "false", "community_data": "false"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        market = data["market_data"]
        return {
            "name": data["name"],
            "symbol": symbol.upper(),
            "price_usd": market["current_price"]["usd"],
            "change_24h": market["price_change_percentage_24h"],
            "change_7d": market["price_change_percentage_7d"],
            "market_cap": market["market_cap"]["usd"],
            "volume_24h": market["total_volume"]["usd"],
            "high_24h": market["high_24h"]["usd"],
            "low_24h": market["low_24h"]["usd"],
        }
    except Exception as e:
        logger.error(f"Error fetching crypto price: {e}")
        return None


def get_gold_price() -> dict:
    """دریافت قیمت طلا"""
    try:
        # از API رایگان metals-api یا goldapi استفاده می‌کنیم
        # اگر API key داری اینجا بذار، وگرنه قیمت تقریبی نمایش داده می‌شه
        url = "https://api.gold-api.com/price/XAU"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get("price", 0)
            return {
                "price_usd": price,
                "unit": "اونس",
                "gram_price": round(price / 31.1035, 2),
            }
    except:
        pass
    
    # قیمت پیش‌فرض اگه API کار نکرد
    return {
        "price_usd": 3300,
        "unit": "اونس",
        "gram_price": round(3300 / 31.1035, 2),
        "note": "قیمت تقریبی - برای دقیق‌تر بودن API key اضافه کنید"
    }


def get_dollar_price() -> dict:
    """دریافت قیمت دلار به تومان"""
    try:
        # سایت‌های ایرانی مثل navasan
        url = "https://api.navasan.tech/latest/?api_key=free&item=usd_buy"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                price = list(data.values())[0].get("value", 0)
                return {"price_irt": int(price), "source": "navasan"}
    except:
        pass
    
    return {
        "price_irt": 0,
        "note": "برای قیمت دلار نیاز به API معتبر ایرانی دارید",
        "suggestion": "سایت‌هایی مثل tgju.org یا navasan.tech را بررسی کنید"
    }


# ==================== تحلیل تکنیکال ساده ====================

def simple_analysis(price: float, high_24h: float, low_24h: float, change_24h: float) -> str:
    """تحلیل ساده بر اساس داده‌های موجود"""
    
    analysis = []
    
    # موقعیت قیمت در رنج روزانه
    range_24h = high_24h - low_24h
    if range_24h > 0:
        position = (price - low_24h) / range_24h * 100
        if position > 70:
            analysis.append("📈 قیمت در بالای رنج روزانه - قدرت خریداران بیشتر")
        elif position < 30:
            analysis.append("📉 قیمت در پایین رنج روزانه - فشار فروش بیشتر")
        else:
            analysis.append("↔️ قیمت در میانه رنج روزانه - بازار در تعادل")
    
    # تغییرات ۲۴ ساعته
    if change_24h > 5:
        analysis.append("🚀 رشد قوی در ۲۴ ساعت - مومنتوم صعودی")
        signal = "خرید احتیاطی"
    elif change_24h > 2:
        analysis.append("✅ رشد مثبت - روند صعودی ضعیف")
        signal = "نگهداری / خرید"
    elif change_24h < -5:
        analysis.append("🔴 افت شدید - فشار فروش بالا")
        signal = "صبر برای تثبیت"
    elif change_24h < -2:
        analysis.append("🟠 کاهش قیمت - احتیاط لازم")
        signal = "صبر / فروش جزئی"
    else:
        analysis.append("⚪ تغییر کم - بازار خنثی")
        signal = "صبر و بررسی"
    
    return "\n".join(analysis), signal


# ==================== هندلرهای بات ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام خوش‌آمد"""
    keyboard = [
        [
            InlineKeyboardButton("💰 قیمت بیتکوین", callback_data="price_BTC"),
            InlineKeyboardButton("💎 قیمت اتریوم", callback_data="price_ETH"),
        ],
        [
            InlineKeyboardButton("🥇 قیمت طلا", callback_data="gold"),
            InlineKeyboardButton("💵 قیمت دلار", callback_data="dollar"),
        ],
        [
            InlineKeyboardButton("📊 تحلیل BTC", callback_data="analyze_BTC"),
            InlineKeyboardButton("📊 تحلیل ETH", callback_data="analyze_ETH"),
        ],
        [
            InlineKeyboardButton("📋 راهنما", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
👋 سلام! من ربات تحلیل‌گر {BOT_NAME} هستم

🔹 قیمت لحظه‌ای ارزهای دیجیتال
🔹 تحلیل تکنیکال ساده
🔹 قیمت طلا و دلار
🔹 پیشنهاد خرید/فروش کوتاه‌مدت

از دکمه‌های زیر استفاده کن یا مستقیم بنویس:
مثال: `BTC` یا `bitcoin` یا `طلا`
"""
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنما"""
    text = """
📖 *راهنمای ربات مهدی*

*دستورات:*
/start - شروع و منوی اصلی
/price BTC - قیمت ارز (مثال: /price ETH)
/analyze BTC - تحلیل ارز
/gold - قیمت طلا
/dollar - قیمت دلار
/coins - لیست ارزهای پشتیبانی‌شده

*ارزهای پشتیبانی‌شده:*
BTC، ETH، BNB، SOL، XRP، ADA، DOGE، TRX، TON، USDT

*نکته مهم:*
⚠️ این ربات صرفاً جنبه آموزشی دارد و مسئولیت معاملات با خود شماست.
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور قیمت"""
    if not context.args:
        await update.message.reply_text("❌ مثال: /price BTC")
        return
    
    symbol = context.args[0].upper()
    await send_price(update.message, symbol)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور تحلیل"""
    if not context.args:
        await update.message.reply_text("❌ مثال: /analyze BTC")
        return
    
    symbol = context.args[0].upper()
    await send_analysis(update.message, symbol)


async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_gold_price(update.message)


async def dollar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_dollar_price(update.message)


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📋 *ارزهای پشتیبانی‌شده:*

₿ BTC - بیتکوین
Ξ ETH - اتریوم  
🔶 BNB - بایننس کوین
◎ SOL - سولانا
✕ XRP - ریپل
₳ ADA - کاردانو
Ð DOGE - دوج‌کوین
⚡ TRX - ترون
💎 TON - تون کوین
💲 USDT - تتر

*روش استفاده:*
/price ETH
/analyze SOL
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های متنی"""
    text = update.message.text.strip().upper()
    
    crypto_map = {
        "BTC": "BTC", "BITCOIN": "BTC", "بیتکوین": "BTC",
        "ETH": "ETH", "ETHEREUM": "ETH", "اتریوم": "ETH",
        "BNB": "BNB", "بایننس": "BNB",
        "SOL": "SOL", "سولانا": "SOL",
        "XRP": "XRP", "ریپل": "XRP",
        "ADA": "ADA", "کاردانو": "ADA",
        "DOGE": "DOGE", "دوج": "DOGE",
        "TRX": "TRX", "ترون": "TRX",
        "TON": "TON",
        "USDT": "USDT", "تتر": "USDT",
    }
    
    if text in crypto_map or text.replace("قیمت ", "") in crypto_map:
        symbol = crypto_map.get(text) or crypto_map.get(text.replace("قیمت ", ""))
        await send_price(update.message, symbol)
    elif text in ["طلا", "GOLD", "قیمت طلا"]:
        await send_gold_price(update.message)
    elif text in ["دلار", "DOLLAR", "USD", "قیمت دلار"]:
        await send_dollar_price(update.message)
    elif text.startswith("تحلیل "):
        symbol_text = text.replace("تحلیل ", "").strip()
        symbol = crypto_map.get(symbol_text, symbol_text)
        await send_analysis(update.message, symbol)
    else:
        keyboard = [[InlineKeyboardButton("📋 راهنما", callback_data="help")]]
        await update.message.reply_text(
            "❓ متوجه نشدم. بنویس مثلاً:\n`BTC` یا `طلا` یا `تحلیل ETH`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("price_"):
        symbol = data.replace("price_", "")
        await send_price(query.message, symbol, edit=True)
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await send_analysis(query.message, symbol, edit=True)
    elif data == "gold":
        await send_gold_price(query.message, edit=True)
    elif data == "dollar":
        await send_dollar_price(query.message, edit=True)
    elif data == "help":
        text = """
📖 *راهنما:*
• بنویس `BTC` برای قیمت بیتکوین
• بنویس `تحلیل ETH` برای تحلیل اتریوم
• بنویس `طلا` برای قیمت طلا
• دستور /coins برای لیست همه ارزها
"""
        await query.message.edit_text(text, parse_mode="Markdown")


# ==================== توابع ارسال پیام ====================

async def send_price(message, symbol: str, edit=False):
    """ارسال قیمت ارز"""
    data = get_crypto_price(symbol)
    
    if not data:
        text = f"❌ ارز {symbol} پیدا نشد. از /coins لیست کامل را ببین."
    else:
        change_emoji = "📈" if data["change_24h"] > 0 else "📉"
        text = f"""
💰 *{data['name']} ({data['symbol']})*

💵 قیمت: `${data['price_usd']:,.2f}`
{change_emoji} تغییر ۲۴ ساعت: `{data['change_24h']:.2f}%`
📊 تغییر ۷ روز: `{data['change_7d']:.2f}%`
⬆️ بالاترین ۲۴h: `${data['high_24h']:,.2f}`
⬇️ پایین‌ترین ۲۴h: `${data['low_24h']:,.2f}`
💹 حجم معاملات: `${data['volume_24h']:,.0f}`

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
    
    keyboard = [
        [InlineKeyboardButton(f"📊 تحلیل {symbol}", callback_data=f"analyze_{symbol}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="start")],
    ]
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def send_analysis(message, symbol: str, edit=False):
    """ارسال تحلیل ارز"""
    data = get_crypto_price(symbol)
    
    if not data:
        text = f"❌ ارز {symbol} پیدا نشد."
    else:
        analysis_text, signal = simple_analysis(
            data["price_usd"],
            data["high_24h"],
            data["low_24h"],
            data["change_24h"]
        )
        
        text = f"""
📊 *تحلیل کوتاه‌مدت {data['name']}*

💵 قیمت فعلی: `${data['price_usd']:,.2f}`

*📈 تحلیل:*
{analysis_text}

*🎯 سیگنال پیشنهادی:*
`{signal}`

*⚠️ نقاط مهم:*
• مقاومت: `${data['high_24h']:,.2f}` (سقف ۲۴h)
• حمایت: `${data['low_24h']:,.2f}` (کف ۲۴h)

━━━━━━━━━━━━━━
⚠️ این تحلیل آموزشی است
مسئولیت معاملات با شماست
"""
    
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="start")]]
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def send_gold_price(message, edit=False):
    """ارسال قیمت طلا"""
    data = get_gold_price()
    
    note = f"\n⚠️ {data.get('note', '')}" if data.get('note') else ""
    
    text = f"""
🥇 *قیمت طلا*

💵 قیمت جهانی: `${data['price_usd']:,.2f}` per اونس
⚖️ قیمت هر گرم: `${data['gram_price']:,.2f}`{note}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="start")]]
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def send_dollar_price(message, edit=False):
    """ارسال قیمت دلار"""
    data = get_dollar_price()
    
    if data.get("price_irt") and data["price_irt"] > 0:
        text = f"""
💵 *قیمت دلار*

🇮🇷 دلار به تومان: `{data['price_irt']:,}` تومان

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
    else:
        text = f"""
💵 *قیمت دلار*

⚠️ {data.get('note', 'خطا در دریافت قیمت')}
💡 {data.get('suggestion', '')}

برای قیمت لحظه‌ای:
🔗 tgju.org
"""
    
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="start")]]
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== اجرای ربات ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("gold", gold_command))
    app.add_handler(CommandHandler("dollar", dollar_command))
    app.add_handler(CommandHandler("coins", coins_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ ربات مهدی در حال اجراست...")
    print("برای توقف Ctrl+C بزن")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
