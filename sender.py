from hashlib import new
from typing import Union
from pyrogram.handlers import MessageHandler
from pyrogram import Client
from config import NeoConfig
from db.storage import ChannelStorage, Channel
import aiofiles
from pyrogram.enums import ChatType
import random
import asyncio

class MessageSender():
    def __init__(self, chat_storage:ChannelStorage):
        self._app = Client("commenter", api_id =NeoConfig.API_ID, api_hash=NeoConfig.API_HASH, phone_number=NeoConfig.PHONE_NUMBER)
        self._chat_storage = chat_storage
        self._status = True
        self._delay = 60*60
    
    async def _comment(self, client, message):
        if self.status:
            chat = await self.check_message(message)
            if chat is not None:
                async with aiofiles.open('comment1.txt', mode='r',encoding='utf-8') as comment1:
                    comment = await message.reply(await comment1.read())
                    await self._chat_storage.increase_messages(chat)
                    await asyncio.sleep(random.randint(3*60,5*60))
                    await comment.delete()
                    async with aiofiles.open('comment2.txt', mode='r',encoding='utf-8') as comment2:
                        comment = await message.reply(await comment2.read())
                        await asyncio.sleep(self._delay)
                        await comment.delete()

    async def leave_chat(self, chat_id:int):
        await self._app.leave_chat(chat_id)
    
    async def join_chat(self, chat_id:int):
        await self._app.join_chat(chat_id)

    async def get_channel_data(self, username:str):
        data = await self._app.get_chat(username)
        return data

    def _init_handler(self):
        self._app.add_handler(MessageHandler(self._comment))
    
    def init(self):
        self._init_handler()

    async def start(self):
        await self._app.start()

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, new_delay:int):
        self._delay = new_delay

    def enable(self):
        self._status = True

    def disable(self):
        self._status = False

    async def check_message(self, message) -> Channel | None:
        chat = await self._chat_storage.get_by_id(message.sender_chat.id)
        if chat:
            if message.chat.type == ChatType.SUPERGROUP and message.forward_from_chat.type == ChatType.CHANNEL\
                and message.chat.id == chat.chat_id and message.sender_chat.username == chat.username:
                return chat
        return None