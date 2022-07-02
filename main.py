import asyncio
from db.db import DB
from config import NeoConfig
from neo_admin import NeoAdmin
from sender import MessageSender
from db.storage import UserStorage, ChannelStorage 


async def init_db():
    db = DB(host=NeoConfig.host, port=NeoConfig.port, login=NeoConfig.login, password=NeoConfig.password, database = NeoConfig.database)
    await db.init()
    user_storage = UserStorage(db)
    await user_storage.init()
    channel_storage = ChannelStorage(db)
    await channel_storage.init()
    return user_storage, channel_storage

async def main():
    user_storage, channel_storage = await init_db()
    message_sender = MessageSender(channel_storage)
    message_sender.init()
    neo_admin = NeoAdmin(message_sender, user_storage, channel_storage)
    await neo_admin.init()
    await asyncio.gather(neo_admin.start(), message_sender.start())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())