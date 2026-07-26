import logging
import re
from telegram import Update
from telegram.ext import ContextTypes

from bot.ai import AI
from bot.keyboards import main_menu, back_menu

logger = logging.getLogger(__name__)
ai = AI()

WELCOME = """🚘 *CarFlip AI*

Find better vehicle deals, estimate profit, diagnose repairs, compare parts, and create negotiation scripts.

Start by setting your location, then use the menu."""

def db(context):
    return context.application.bot_data["db"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db(context).upsert_user(user.id)
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text("Choose a feature:", reply_markup=main_menu())

async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "location"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "📍 Send your location like:\n\n`Dallas, TX, 75201`\n\nYou may also send only `Dallas, TX`.",
        parse_mode="Markdown", reply_markup=back_menu()
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "analyze"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "🔎 Paste the listing details.\n\nExample:\n"
        "2017 Honda Accord, $8,500, 142,000 miles, clean title, check-engine light, Dallas TX.\n"
        "You can also paste the listing description and URL.",
        reply_markup=back_menu()
    )

async def seller_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "seller"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "🤝 Send the car details, asking price, problems you noticed, and your intended offer.",
        reply_markup=back_menu()
    )

async def buyer_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "buyer"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "💬 Send your vehicle details, sale price, and the buyer's message. I’ll write your response.",
        reply_markup=back_menu()
    )

async def repair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "repair"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "🛠 Send:\n• Year, make, model and engine\n• Symptoms\n• Warning lights or OBD code\n• What happened before the issue",
        reply_markup=back_menu()
    )

async def parts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "parts"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "🧩 Send the year, make, model, engine and exact part needed.\n\n"
        "I’ll explain compatibility checks and give store search links.",
        reply_markup=back_menu()
    )

async def ready_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db(context).get_user(update.effective_user.id)
    city = user["city"] if user else None
    state = user["state"] if user else None
    deals = db(context).best_deals(city, state, 8)
    target = update.callback_query.message if update.callback_query else update.message

    if not deals:
        await target.reply_text(
            "🔥 No saved deals are available yet.\n\nUse ➕ Add Deal to load listings manually. "
            "Your approved marketplace/data connector can later populate this feed automatically.",
            reply_markup=back_menu()
        )
        return

    lines = ["🔥 *READY DEALS*\n"]
    for i, d in enumerate(deals, 1):
        score = max(1, min(100, int(50 + (d["profit"] or 0) / max(d["price"], 1) * 100)))
        lines.append(
            f"*{i}. {d['title']}*\n"
            f"Price: ${d['price']:,.0f}\n"
            f"Market value: ${d['market_value']:,.0f}\n"
            f"Estimated repairs: ${d['repairs']:,.0f}\n"
            f"Potential profit: ${d['profit']:,.0f}\n"
            f"Deal score: {score}/100\n"
            f"{d['listing_url'] or ''}\n"
        )
    await target.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=back_menu())

async def market_pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db(context).get_user(update.effective_user.id)
    city = user["city"] if user else None
    state = user["state"] if user else None
    stats = db(context).market_pulse(city, state, 8)
    target = update.callback_query.message if update.callback_query else update.message

    if not stats:
        await target.reply_text(
            "📊 Market Pulse has no imported transaction data yet.\n\n"
            "This section will rank the most bought, most sold, fastest-selling, and highest-demand "
            "vehicles by ZIP, city, state, and nearby states once a licensed data source or CSV feed is connected.\n\n"
            "Important: removed listings are not automatically treated as confirmed sales.",
            reply_markup=back_menu()
        )
        return

    lines = [f"📊 *MARKET PULSE — {city or ''} {state or ''}*\n"]
    for i, s in enumerate(stats, 1):
        lines.append(
            f"*{i}. {s['make']} {s['model']}*\n"
            f"Sold: {s['sold_count']} | Bought: {s['bought_count']}\n"
            f"Average price: ${s['avg_price']:,.0f}\n"
            f"Average time to sell: {s['avg_days_to_sell']:.0f} days\n"
        )
    await target.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=back_menu())

async def add_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "adddeal"
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "➕ Add a deal using this exact format:\n\n"
        "`Title | price | market value | repairs | fees | mileage | city | state | URL`\n\n"
        "Example:\n"
        "`2017 Honda Accord | 8500 | 11200 | 600 | 350 | 142000 | Dallas | TX | https://...`",
        parse_mode="Markdown", reply_markup=back_menu()
    )

async def add_deal_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = [x.strip() for x in update.message.text.split("|")]
    if len(parts) < 8:
        await update.message.reply_text("Use the exact format shown. Include at least 8 sections.")
        return
    try:
        title = parts[0]
        year_match = re.search(r"\b(19|20)\d{2}\b", title)
        tokens = title.split()
        deal = {
            "title": title,
            "year": int(year_match.group()) if year_match else None,
            "make": tokens[1] if year_match and len(tokens) > 1 else None,
            "model": " ".join(tokens[2:]) if year_match and len(tokens) > 2 else None,
            "price": float(parts[1].replace("$","").replace(",","")),
            "market_value": float(parts[2].replace("$","").replace(",","")),
            "repairs": float(parts[3].replace("$","").replace(",","")),
            "fees": float(parts[4].replace("$","").replace(",","")),
            "mileage": int(parts[5].replace(",","")),
            "city": parts[6],
            "state": parts[7].upper(),
            "listing_url": parts[8] if len(parts) > 8 else "",
            "source": "Manual"
        }
        db(context).add_deal(deal)
        profit = deal["market_value"] - deal["price"] - deal["repairs"] - deal["fees"]
        context.user_data["mode"] = None
        await update.message.reply_text(
            f"✅ Deal saved.\nEstimated profit: ${profit:,.0f}",
            reply_markup=main_menu()
        )
    except ValueError:
        await update.message.reply_text("One of the price or mileage fields is not a valid number.")

async def location_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    if not mode:
        return

    text = update.message.text.strip()
    if mode == "location":
        fields = [x.strip() for x in text.split(",")]
        if len(fields) < 2:
            await update.message.reply_text("Send at least a city and state, like `Dallas, TX`.", parse_mode="Markdown")
            return
        city, state = fields[0], fields[1].upper()
        zip_code = fields[2] if len(fields) > 2 else ""
        db(context).upsert_user(update.effective_user.id, city, state, zip_code, 50)
        context.user_data["mode"] = None
        await update.message.reply_text(
            f"✅ Location saved: {city}, {state} {zip_code}",
            reply_markup=main_menu()
        )
        return

    if mode == "analyze":
        await analyze_text_handler(update, context)
    elif mode == "seller":
        answer = await ai.ask(
            "Write 3 concise Facebook Marketplace seller negotiation messages: friendly, direct cash offer, "
            "and follow-up. Use only supplied facts. Vehicle/listing:\n" + text
        )
        context.user_data["mode"] = None
        await update.message.reply_text(answer, reply_markup=main_menu())
    elif mode == "buyer":
        answer = await ai.ask(
            "Write a confident, honest reply to a prospective vehicle buyer. Do not hide defects or invent facts. "
            "Include a clear next step. Details:\n" + text
        )
        context.user_data["mode"] = None
        await update.message.reply_text(answer, reply_markup=main_menu())
    elif mode == "repair":
        await repair_text_handler(update, context)
    elif mode == "parts":
        await parts_text_handler(update, context)
    elif mode == "adddeal":
        await add_deal_text_handler(update, context)

async def analyze_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = await ai.ask(
        "Analyze this potential vehicle flip. Include missing information, market-value caution, likely repairs, "
        "all-in cost, possible resale range, estimated profit range, maximum offer, risk flags, inspection checklist, "
        "and BUY / NEGOTIATE / SKIP. Listing:\n" + update.message.text
    )
    context.user_data["mode"] = None
    await update.message.reply_text(answer, reply_markup=main_menu())

async def repair_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = await ai.ask(
        "Diagnose these vehicle symptoms cautiously. Give likely causes ranked, safe checks, tools/parts, "
        "difficulty, estimated DIY and shop cost ranges, step-by-step overview, and stop-driving warnings. "
        "Never invent exact torque specs. Vehicle/problem:\n" + update.message.text
    )
    context.user_data["mode"] = None
    await update.message.reply_text(answer, reply_markup=main_menu())

async def parts_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.message.text
    answer = await ai.ask(
        "Explain how to verify the exact compatible part using VIN, engine, trim, OEM number and connector shape. "
        "Suggest OEM/new/used/rebuilt options and warn that stock/prices must be verified. Request:\n" + q
    )
    encoded = q.replace(" ", "+")
    links = (
        "\n\n🔗 Search stores:\n"
        f"AutoZone: https://www.autozone.com/searchresult?searchText={encoded}\n"
        f"O'Reilly: https://www.oreillyauto.com/search?q={encoded}\n"
        f"NAPA: https://www.napaonline.com/en/search?text={encoded}\n"
        f"RockAuto: https://www.rockauto.com/\n"
        f"LKQ: https://www.lkqonline.com/\n"
        f"eBay Motors: https://www.ebay.com/sch/i.html?_nkw={encoded}"
    )
    context.user_data["mode"] = None
    await update.message.reply_text(answer + links, disable_web_page_preview=True, reply_markup=main_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(
        "HOW TO USE\n\n"
        "1. Set your location.\n"
        "2. Paste a listing into Analyze Car.\n"
        "3. Save promising listings with Add Deal.\n"
        "4. Open Ready Deals to compare profit.\n"
        "5. Use Repair Hub and Parts Finder before purchasing.\n\n"
        "This bot provides estimates, not a mechanical inspection, title report, or guaranteed profit.",
        reply_markup=back_menu()
    )

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    actions = {
        "menu": menu, "location": set_location, "analyze": analyze,
        "seller": seller_script, "buyer": buyer_script,
        "repair": repair, "parts": parts, "deals": ready_deals,
        "market": market_pulse, "adddeal": add_deal, "help": help_command
    }
    handler = actions.get(query.data)
    if handler:
        await handler(update, context)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Bot error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Temporary error. Please try again or use /menu."
        )
