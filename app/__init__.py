# app/__init__.py

from config import Config

import os


import logging
from textwrap import dedent

from telegram import Update, PhotoSize
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import CallbackContext


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

updater = Updater(token=Config.token, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    from_user = update.message.from_user
    logger.info(f"Start called by {from_user.username}")
    if 'used_by' not in context.bot_data:
        context.bot_data['active_users'] = set()
    context.bot_data['active_users'].add(from_user.username)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Session for @{from_user.username} started"
    )


def stop(update, context):
    from_user = update.message.from_user
    logger.info(f"Stop called by {from_user.username}")
    if from_user.username not in context.bot_data.get('active_users', set()):
        message = 'Please start me first'
    else:
        context.bot_data['active_users'].remove(from_user.username)
        message = f"Session for @{from_user.username} stopped"
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


def who(update, context):
    from_user = update.message.from_user
    logger.info(f"Who called by {from_user.username}")
    if len(context.bot_data.get('active_users', set())) == 0:
        message = 'No active users'
    else:
        message = 'Active users: ' + ', '.join("@" + name for name in context.bot_data['active_users'])
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


def help(update, context):
    from_user = update.message.from_user
    logger.info(f"Help called by {from_user.username}")
    if from_user.username not in context.bot_data.get('active_users', set()):
        message = 'use "/start" to start'
    else:
        message = dedent("""\
            Help:
                /start: start your session
                /stop: stop your session
                /who: list all active users
                /help: show this help
            """)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        message = dedent("""\
            During a session, every text and photo is stored chronologically. Use the web-app to organise the photos later.
            """)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def msg(update: Update, context: CallbackContext):
    from_user = update.message.from_user
    logger.info(f"Message from {from_user.username}")
    if from_user.username not in context.bot_data.get('active_users', set()):
        message = 'Please start me first'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        if update.message.text:
            print(f'@{from_user.username}:{update.message.date}:message:{update.message.text}', file = context.bot_data['database'], flush=True)
        if update.message.caption:
            print(f'@{from_user.username}:{update.message.date}:message:{update.message.caption}', file = context.bot_data['database'], flush=True)

        def photosortkey(p: PhotoSize):
            return p.height * p.width
        
        photo = sorted(update.message.photo, key=photosortkey)[-1]
        image = photo.get_file().download(os.path.join(context.bot_data['imagestore'], f'{photo.file_unique_id}.jpg'))
        print(f'@{from_user.username}:{update.message.date}:image:{image}', file = context.bot_data['database'], flush=True)


def run():

    if not os.path.isdir(Config.imagestore):
        os.mkdir(Config.imagestore) 

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    who_handler = CommandHandler('who', who)
    help_handler = CommandHandler('help', help)
    msg_handler = MessageHandler((~Filters.command), msg)

    dispatcher.bot_data['database'] = open(Config.database, 'at')
    dispatcher.bot_data['imagestore'] = Config.imagestore

    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stop_handler)
    dispatcher.add_handler(who_handler)
    dispatcher.add_handler(msg_handler)
    
    
    updater.start_polling()
    updater.idle()

    dispatcher.bot_data['database'].close()

