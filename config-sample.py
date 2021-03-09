# config.py

class Config:

    token = 'your-telegram-bot-token-here'

    database = os.path.join(basedir, 'imageuploader.txt')
    imagestore = os.path.join(basedir, 'imagestore')
