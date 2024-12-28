from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json
import os

# Data structures
users = {}
verified = []
verifiers = [5476909488]
waiting_users = {
    "male": [],
    "female": [],
    "gay": [],
    "lesbian": []
}
active_chats = {}

# Log file path
LOG_FILE = "chat_logs.json"
VERIFY_LOG = "verified_users.json"

# Ensure log file exists and is initialized as an empty dictionary if not
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as file:
        json.dump({}, file)





# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    group_id = -1002385481659
    invite_link = 'https://t.me/+jJjm7pFRqaczNjdl'
    me_link = 'https://t.me/rockzydex'
    bot_link = 'https://t.me/doitu_bot'

    keyboard = [
        [InlineKeyboardButton("Request to Join", url=invite_link)],
        [InlineKeyboardButton("Contact support", url=me_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    keyboard2 = [
        [InlineKeyboardButton("Take me to bot", url=bot_link)]
    ]
    reply_markup2 = InlineKeyboardMarkup(keyboard2)

    if chat_type == 'private':
        user_id = update.effective_user.id

        try:
            chat_member = await context.bot.get_chat_member(group_id, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                await update.message.reply_text(
                    "Welcome! Please select your gender 👇"
                )

                if user_id in active_chats:
                    await update.message.reply_text("You're already in a chat! Send /end to leave before starting a new session.")
                    return

                gender_keyboard = [["Male👦", "Female👧"]]
                await update.message.reply_text(
                    "Choose your gender:",
                    reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True)
                )
            else:
                await update.message.reply_text("You need to be a member of the group to access the bot.", reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text("You need to join the group to access the bot.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You can only access bot in private chat.", reply_markup=reply_markup2)


async def choose_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    preference = update.message.text.lower()  # Convert input to lowercase for uniformity
    
    # Mapping the input with emojis to the corresponding gender
    gender_map = {
        "male👦": "male",
        "female👧": "female",
        "gay🏳️‍🌈": "gay",
        "lesbian🏳️‍🌈": "lesbian"
    }

    # Check if the user has selected a valid gender (with emojis)
    if preference not in gender_map:
        await update.message.reply_text("Invalid choice. Please select a valid gender option.")
        return

    # Get the mapped gender (the lowercase version of the preference)
    preference = gender_map[preference]

    # Prevent preference change while in active chat
    if user_id in active_chats:
        await update.message.reply_text("You're in an active chat. Use /end to leave the chat before changing preferences.")
        return

    # Remove user from all waiting lists before assigning a new preference
    for gender_list in waiting_users.values():
        if user_id in gender_list:
            gender_list.remove(user_id)

    # Update user's preference
    users[user_id] = {"preference": preference, "partner": None}

    # Matching logic
    if preference in ["male", "female"]:
        # Male looks for female, female looks for male
        target_group = "female" if preference == "male" else "male"
        if waiting_users[target_group]:
            partner_id = waiting_users[target_group].pop(0)
            users[user_id]["partner"] = partner_id
            users[partner_id]["partner"] = user_id
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id

            await context.bot.send_message(chat_id=user_id, text="You are now connected! Say hi to your partner.")
            await context.bot.send_message(chat_id=partner_id, text="You are now connected! Say hi to your partner.")
        else:
            waiting_users[preference].append(user_id)
            await update.message.reply_text("Waiting for a partner...")
    elif preference in ["gay", "lesbian"]:
        # Gay looks for gay, lesbian looks for lesbian
        if waiting_users[preference]:
            partner_id = waiting_users[preference].pop(0)
            users[user_id]["partner"] = partner_id
            users[partner_id]["partner"] = user_id
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id

            await context.bot.send_message(chat_id=user_id, text="You are now connected! Say hi to your partner.")
            await context.bot.send_message(chat_id=partner_id, text="You are now connected! Say hi to your partner.")
        else:
            waiting_users[preference].append(user_id)
            await update.message.reply_text("Waiting for a partner...")



async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("You're not in a chat. Type /start to begin.")
        return

    partner_id = active_chats[user_id]
    message_text = update.message.text


    await context.bot.send_message(chat_id=partner_id, text=message_text)


async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type

    if chat_type == 'private':
        user_id = update.effective_user.id
        if user_id not in active_chats:
            await update.message.reply_text("You're not in a chat.")
            return

        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id)
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None

        await context.bot.send_message(chat_id=user_id, text="Chat ended. Type /start to begin again.")
        await context.bot.send_message(chat_id=partner_id, text="Your partner has ended the chat. Type /start to find a new partner.")


# Main application
def main():
    application = Application.builder().token("7545112793:AAGVBUB1zFlBVUPEtVvd0j_gKuJhcmMyjcs").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^(Male👦|Female👧)$"), choose_gender))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_message))
    application.add_handler(CommandHandler("end", end_chat))

    application.run_polling()


if __name__ == "__main__":
    main()
