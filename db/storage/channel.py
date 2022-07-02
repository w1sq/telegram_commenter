from ..db import DB
from datetime import datetime
from typing import Union, List
from dataclasses import dataclass

@dataclass
class Channel:
    id:int
    username:str
    title:str
    chat_id:int
    messages:int 
    last_updated_time:datetime

class ChannelStorage():
    __table = "channels"
    def __init__(self, db:DB) -> None:
        self._db = db
    
    async def init(self) -> None:
        await self._db.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.__table} (
                id BIGINT PRIMARY KEY,
                username TEXT,
                title TEXT,
                chat_id BIGINT,
                messages int,
                last_updated_time timestamp
            ) 
        ''')

    async def get_by_id(self, channel_id:int) -> Union[Channel, None]:
        channel = await self._db.fetchrow(f"SELECT * FROM {self.__table} WHERE id = $1", channel_id)
        if channel is None:
            return None
        return Channel(channel[0], channel[1], channel[2], channel[3], channel[4], channel[5])

    async def get_all_channels(self) -> Union[List[Channel], None]:
        channels = await self._db.fetch(f"SELECT * FROM {self.__table}")
        if channels is None:
            return None
        return [Channel(channel[0], channel[1], channel[2], channel[3], channel[4], channel[5]) for channel in channels]

    async def create(self, channel:Channel):
        await self._db.execute(f'''
            INSERT INTO {self.__table} (id, username, title, chat_id, messages, last_updated_time) VALUES ($1, $2, $3, $4, $5, $6)
        ''', channel.id, channel.username, channel.title, channel.chat_id, channel.messages, channel.last_updated_time)

    async def increase_messages(self, chat:Channel):
        await self._db.execute(f"UPDATE {self.__table} SET messages = messages + 1 WHERE id = $1", chat.id)

    async def delete(self, channel:Channel) -> None:
        await self._db.execute(f'''
            DELETE FROM {self.__table} WHERE id = $1
        ''', channel.id)