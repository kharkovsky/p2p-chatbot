from __future__ import print_function
import sys  # For passing -t or --token right from terminal
import logging  # Only service information without any user data
import os

import time
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)


from users import User, Users, Database, Debug


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

APP_FOLDER = os.path.dirname(os.path.realpath(__file__))

users = None


def init():
    global users
    users = Users(Database.user_list())


def command_start(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*Welcome to anon chat!*\n/search - Search for chat",
                              # "\n/settings - Settings menu",
                         parse_mode=ParseMode.MARKDOWN)
        users.add(you)
    else:
        bot.send_message(chat_id=you,
                         text="*We have already started*",
                         parse_mode=ParseMode.MARKDOWN)


def command_search(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=update.message.chat_id,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if users.in_search(you):
        return

    if not users.search_empty():
        for chat_id in users.create_chat(you):
            bot.send_message(chat_id=chat_id,
                             text="Chat found! Talk!")
            time.sleep(.3)
    else:
        bot.send_message(chat_id=you,
                         text="*Searching for chat*...\n/cancel - Stop searching",
                         parse_mode=ParseMode.MARKDOWN)
        users.search_add(you)


def messages(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if users.is_chatting(you):
        bot.send_message(chat_id=users.get(you).target.id,
                         text="*Stranger*\n{}".format(update.message.text),
                         parse_mode=ParseMode.MARKDOWN)


def command_bye(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if users.is_chatting(you):
        for chat_id in users.stop_chat(you):
            bot.send_message(chat_id=chat_id,
                             text="*Chatting has been stopped.*\n"
                                  "/search - Search for another chat\n/settings - Settings menu",
                             parse_mode=ParseMode.MARKDOWN)


def command_settings(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return


def command_offer(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
    elif users.is_chatting(you):
        update.message.reply_text("TODO: offer")


def command_cancel(bot, update):
    you = update.message.chat_id
    if not users.exists(you):
        bot.send_message(chat_id=you,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
    elif users.in_search(you):
        users.search_remove(you)
        bot.send_message(chat_id=you,
                         text="*Canceled.*\n/search - Search for chat",
                              # "\n/settings - Settings menu",
                         parse_mode=ParseMode.MARKDOWN)


def command_stop(bot, update):
    you = update.message.chat_id

    if not users.exists(you):
        bot.send_message(chat_id=update.message.chat_id,
                         text="*PRO TIP*: type /start to start",
                         parse_mode=ParseMode.MARKDOWN)
        return

    if users.is_chatting(you):
        command_bye(bot, update)
    elif users.in_search(you):
        users.search_remove(you)

    users.remove(you)

    update.message.reply_text("Bye!")


def command_print(bot, update):
    you = update.message.chat_id
    commands = set(update.message.text.split(' ')[1:])

    if len(commands) == 0:
        bot.send_message(chat_id=you, text="You requested nothing! Available options: in_chat active in_search")
        return

    to_print = "You requested:\n-> " + '\n-> '.join(commands)
    bot.send_message(chat_id=you, text=to_print)

    message = ''
    for command in commands:
        if command == 'active':
            message += 'active = [' + ', '.join(str(v) for v in Debug.users_active()) + ']\n'
        elif command == 'in_chat':
            message += 'in_chat = [' + ', '.join(str(v) for v in Debug.users_chatting()) + ']\n'
        elif command == 'in_search':
            message += 'in_search = [' + ', '.join(str(v) for v in Debug.users_searching()) + ']\n'

    bot.send_message(chat_id=you, text=message)


def error_handler(bot, update, error):
    try:
        raise error
    except TimedOut:
        print("TimedOut")
    except NetworkError:
        print("Network error! Seems like too many TimedOut raised before. Restarting bot...")
        os.execv(sys.executable, ['python'] + sys.argv)


def main():
    init()
    token = None

    try:
        for keyword in '-t', '--token':
            if keyword in sys.argv:
                token = sys.argv[sys.argv.index(keyword)+1]
                break
        else:
            with open(os.path.join(APP_FOLDER, 'token.secret'), 'r') as token_file:
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
    dp.add_handler(CommandHandler('print', command_print))  # DEBUG: print objects
    dp.add_handler(CommandHandler('search', command_search))
    dp.add_handler(CommandHandler('bye', command_bye))
    dp.add_handler(CommandHandler('offer', command_offer))
    dp.add_handler(CommandHandler('settings', command_settings))
    dp.add_handler(CommandHandler('stop', command_stop))
    dp.add_handler(CommandHandler('cancel', command_cancel))
    dp.add_handler(MessageHandler(Filters.text, messages))
    dp.add_error_handler(error_handler)

    print("Bot @{} has been started!".format(upd.bot.username))
    upd.start_polling()
    upd.idle()


if __name__ == "__main__":
    Database.init()
    main()
    Database.close()
