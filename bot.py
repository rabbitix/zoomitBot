import os
import zipfile
import logging
import string
import random
import shutil
import itertools
from telegram.ext import (Updater, Dispatcher, ConversationHandler, CommandHandler,
                          MessageHandler, RegexHandler, Filters,
                          CallbackContext,)
from telegram import (Update, KeyboardButton, PhotoSize, ChatMember,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto,
                      ReplyMarkup, InlineKeyboardButton, InlineKeyboardMarkup,)
from telegram.utils import helpers

import requests
from telegram import ParseMode
from telegram.utils.helpers import mention_html
import sys
import traceback
from telegram import Bot
from bs4 import BeautifulSoup

 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def error(update: Update, context: CallbackContext):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    devs = [194419690]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message
    # could fail
    if update.effective_message:
        text = "خطایی پیش اومده..لطفا ورودی ها رو بررسی کنید .. به سازندم اطلاع دادم، اگه خطا از سمت ما باشه بزودی رفع میشه ..ممنون که از من استفاده میکنید :)"
        update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    raise


messages = {
    "start":"""سلام 
🔗🔗لینک سایت زومیت برای محصول رو برام بفرست:
(برای مثال https://www.zoomit.ir/product/samsung-galaxy-m02/ )""",
    "bad_url":"⚠️خطا! ⚠️ لینک شناخته نشد!❌ مجدد تلاش کنید🔁",
    "working":"""✅  در حال پردازش درخواست شما 🔰
🕐🕑🕒لطفا منتظر بمانید.. ممکن است کمی طول بکشد!🕤🕥🕦""" ,
    "photos": " {} photos!📸📸 \nby 🆔 @zoomit_photo_bot 🆔 ",
    "send_new":"""📌یک لینک از زومیت بفرستید 🔖🔖 
(برای مثال: 
https://www.zoomit.ir/product/samsung-galaxy-m02/
⚠️ به / انتها دقت کنید!  )"""
}
class Bot:
    def __init__(self, token):
        REQ = {
            'proxy_url': 'socks5h://127.0.0.1:9050',
            'urllib3_proxy_kwargs': {
                'username': '1',
                'password': '1',
            },
            'connect_timeout': 200,
        }
        self.updater = Updater(
            token=token, use_context=True, request_kwargs=REQ)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_error_handler(error)
        start = CommandHandler('start', self.start)
        url_hndlr = MessageHandler(Filters.text,self.parse_url)

        self.dispatcher.add_handler(start)
        self.dispatcher.add_handler(url_hndlr)


        

    def start(self, update: Update, context: CallbackContext):
        update.message.reply_text(messages["start"],disable_web_page_preview=True)

    def get_urls_list(self,url):
        links = []
        res = requests.get(f"{url}photos/")
        soup = BeautifulSoup(res.text,'lxml')
        div = soup.find('div',attrs={'class':"product-images_official-images"})
        for a in div.find_all("a"):
            url = a.get('href')
            print(url)
            links.append(url)

        return links
    def parse_url(self, update: Update, context: CallbackContext):
        raw_url = update.message.text
        if 'zoomit' not in raw_url or len(set(raw_url.split('/'))) !=5 or raw_url[-1] != '/':
            return update.message.reply_text(messages["bad_url"])

        update.message.reply_text(messages["working"])
        
        slug = raw_url.split('/')[-2]
        # it means user send a url without last slash
        if len(slug) < 2:
            slug = raw_url.split('/')[-1]

        user_id = update.effective_user.id
        context.user_data[user_id] = {}

        # get urls to downlaod
        # print(raw_url)
        links = self.get_urls_list(str(update.message.text))
        # make a folder with userid 
        try:
            os.mkdir(f"{user_id}")
        except:
            print("user existed")
        finally:
            os.chdir(f"{user_id}/")
        
        try:
            os.mkdir(f"{slug}")
        except:
            print("slug already exist")
        finally:
            os.chdir(f"{slug}")

 


        for num,link in enumerate(links):
            
            with open(f'img_{num}.jpg','wb') as img_file:
                res = requests.get(link)
                img_file.write(res.content)

        print("Downloaded all")
        os.chdir('../')
        zipe_file_name = f'{slug}.zip'
        zipf = zipfile.ZipFile(zipe_file_name, 'w', zipfile.ZIP_DEFLATED)
        self.zip_dir(f'{slug}/', zipf)
        zipf.close()

        print('ziped it')


        context.bot.send_document(chat_id=update.effective_chat.id ,
        document=open(zipe_file_name, 'rb'),caption=messages["photos"].format(slug),timeout=500, reply_to_message_id=update.effective_message.message_id)
        # send as album

        photo_list = [InputMediaPhoto(media=url) for url in links ]
        context.bot.sendMediaGroup(chat_id=update.effective_chat.id,media=photo_list,timeout=500)
        # delete files 

        os.chdir('../')
        for root,dirs,files in os.walk(f"{user_id}/"):
            for file in files:
                os.remove(os.path.join(root,file))
        shutil.rmtree(f"./{user_id}")


        update.message.reply_text(messages["send_new"],disable_web_page_preview=True,)
        

    
    def zip_dir(self,path,ziph):
        for root,dirs,files in os.walk(path):
            for file in files:
                ziph.write(os.path.join(root,file),os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()



token = "your Token"
bot = Bot(token).run()