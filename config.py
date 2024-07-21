from os import environ 

class Config:
    API_ID = environ.get("API_ID", "29726374")
    API_HASH = environ.get("API_HASH", "ee797487083e78676bc682c2e78df5fc")
    BOT_TOKEN = environ.get("BOT_TOKEN", "7309002879:AAGdhHj-aMz-f9F6GrmJ4n1bBqglZc1Ik3o") 
    BOT_SESSION = environ.get("BOT_SESSION", "") 
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://ackbot:ackbot@bot.uthcly0.mongodb.net/?retryWrites=true&w=majority&appName=bot")
    DATABASE_NAME = environ.get("DATABASE_NAME", "ackbot")
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '1974513195').split()]

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
