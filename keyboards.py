from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    rows = [
        [
            InlineKeyboardButton("🔥 Ready Deals", callback_data="deals"),
            InlineKeyboardButton("🔎 Analyze Car", callback_data="analyze"),
        ],
        [
            InlineKeyboardButton("📊 Market Pulse", callback_data="market"),
            InlineKeyboardButton("📍 My Location", callback_data="location"),
        ],
        [
            InlineKeyboardButton("🛠 Repair Hub", callback_data="repair"),
            InlineKeyboardButton("🧩 Parts Finder", callback_data="parts"),
        ],
        [
            InlineKeyboardButton("🤝 Seller Script", callback_data="seller"),
            InlineKeyboardButton("💬 Buyer Script", callback_data="buyer"),
        ],
        [
            InlineKeyboardButton("➕ Add Deal", callback_data="adddeal"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(rows)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]])
