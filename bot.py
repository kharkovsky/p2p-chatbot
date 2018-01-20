from __future__ import print_function
import sys  # For passing -t or --token right from terminal
import logging  # Only service information without any user data


from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

STATE = 0xFFFF
TARGET = 0xFFFE
STATE_IDLE = 0x0000
STATE_SEARCHING = 0x0001
STATE_CHATTING = 0x0002

active_users = {
}
searching = []


def command_start(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*Welcome to anon chat!*\n/search - Search for chat",
                              # "\n/settings - Settings menu",
                         parse_mode=ParseMode.MARKDOWN)
        active_users[you] = {STATE: STATE_IDLE}


def command_search(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] != STATE_IDLE:
        return

    bot.send_message(chat_id=you,
                     text="*Searching for chat*...\n/cancel - Stop searching",
                     parse_mode=ParseMode.MARKDOWN)

    if len(searching) >= 1:
        chatmate = searching.pop()

        active_users[chatmate][TARGET] = you
        active_users[chatmate][STATE] = STATE_CHATTING
        active_users[you][TARGET] = chatmate
        active_users[you][STATE] = STATE_CHATTING

        update.message.reply_text("Chat found! Talk!")
        bot.send_message(chat_id=chatmate, text="Chat found! Talk!")
    else:
        active_users[you][STATE] = STATE_SEARCHING
        searching.append(you)


def messages(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_CHATTING:
        bot.send_message(chat_id=active_users[you][TARGET],
                         text="*Stranger*\n{}".format(update.message.text),
                         parse_mode=ParseMode.MARKDOWN)


def command_bye(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_CHATTING:
        chatmate = active_users[you][TARGET]

        bot.send_message(chat_id=you,
                         text="*Chatting has been stopped.*\n"
                              "/search - Search for another chat\n/settings - Settings menu",
                         parse_mode=ParseMode.MARKDOWN)
        bot.send_message(chat_id=chatmate,
                         text="*Stranger has stopped conversation.*",
                         parse_mode=ParseMode.MARKDOWN)

        active_users[chatmate][STATE] = STATE_IDLE
        active_users[you][STATE] = STATE_IDLE

        del active_users[chatmate][TARGET]
        del active_users[you][TARGET]


def command_settings(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_IDLE:
        update.message.reply_text("TODO: settings")


def command_offer(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_CHATTING:
        update.message.reply_text("TODO: offer")


def command_cancel(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_SEARCHING:
        bot.send_message(chat_id=you,
                         text="*Canceled.*\n/search - Search for chat",
                              # "\n/settings - Settings menu",
                         parse_mode=ParseMode.MARKDOWN)

        searching.remove(update.message.chat_id)
        active_users[update.message.chat_id][STATE] = STATE_IDLE

        return STATE_IDLE


def command_stop(bot, update):
    you = update.message.chat_id

    if active_users.get(you, None) is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if active_users[you][STATE] == STATE_CHATTING:
        bot.send_message(chat_id=you, text="*/stop conversation at first!*",
                         parse_mode=ParseMode.MARKDOWN)
        return
    elif active_users[you][STATE] == STATE_SEARCHING:
        searching.remove(you)

    del active_users[you]
    update.message.reply_text("Bye!")


def main():

    token = None

    try:
        for keyword in '-t', '--token':
            if keyword in sys.argv:
                token = sys.argv[sys.argv.index(keyword)+1]
                break
        else:
            with open('token.secret', 'r') as token_file:
                token = token_file.readline().strip()
    except IndexError:
        print("No token specified!\nUsage: bot.py [-t|--token] [TOKEN_STRING]")
        exit(1)
    except IOError:
        print("File token.secret not exists!")
        exit(1)

    upd = Updater(token)
    dp = upd.dispatcher

    dp.add_handler(CommandHandler('start', command_start))
    dp.add_handler(CommandHandler('search', command_search))
    dp.add_handler(CommandHandler('bye', command_bye))
    dp.add_handler(CommandHandler('offer', command_offer))
    dp.add_handler(CommandHandler('settings', command_settings))
    dp.add_handler(CommandHandler('stop', command_stop))
    dp.add_handler(CommandHandler('cancel', command_cancel))
    dp.add_handler(MessageHandler(Filters.text, messages))

    upd.start_polling()
    upd.idle()


if __name__ == "__main__":
    main()
