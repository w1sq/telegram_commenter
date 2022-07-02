from os import stat
import aiogram
import aiofiles
from typing import Callable
from config import NeoConfig
from datetime import datetime
from sender import MessageSender
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from db.storage import UserStorage, ChannelStorage, User, Channel
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from answers import messages_answer

class GetAnswer(StatesGroup):
    answer_admin = State()
    answer_channel = State()
    answer_message = State()
    answer_delay = State()


class NeoAdmin():
    def __init__(self, message_sender: MessageSender, user_storage: UserStorage, channel_storage: ChannelStorage):
        self._message_sender:MessageSender = message_sender
        self._user_storage:UserStorage = user_storage
        self._channel_storage:ChannelStorage = channel_storage
        self._bot:aiogram.Bot = aiogram.Bot(NeoConfig.API_KEY)
        self._storage:MemoryStorage = MemoryStorage()
        self._dispatcher:aiogram.Dispatcher = aiogram.Dispatcher(self._bot, storage=self._storage)
        self.disable_web_page:bool = True
        self._create_keyboards()

    async def init(self) :
        self._init_handler()

    async def start(self):
        print('Bot has started')
        await self._dispatcher.start_polling()

    def _init_handler(self) :
        self._dispatcher.register_message_handler(self._user_middleware(self._cmd_start), commands=['start'])
        self._dispatcher.register_message_handler(self._user_middleware(self._turn_bot_on), text='Включить бота')
        self._dispatcher.register_message_handler(self._user_middleware(self._turn_bot_off), text='Выключить бота')
        self._dispatcher.register_message_handler(self._user_middleware(self._add_administrator), text='Добавить администратора')
        self._dispatcher.register_message_handler(self._process_admin, state=GetAnswer.answer_admin)
        self._dispatcher.register_message_handler(self._process_channel, state=GetAnswer.answer_channel)
        self._dispatcher.register_message_handler(self._set_message, state=GetAnswer.answer_message)
        self._dispatcher.register_message_handler(self._set_delay, state=GetAnswer.answer_delay)
        self._dispatcher.register_callback_query_handler(self._add_admin, text='addadmin')
        self._dispatcher.register_callback_query_handler(self._add_chat_call, text='addchat')
        self._dispatcher.register_callback_query_handler(self._change_send_delay, text='change_send_delay')
        self._dispatcher.register_callback_query_handler(self._change_message_state, Text(startswith="changemess "))
        self._dispatcher.register_callback_query_handler(self._delete_admin, Text(startswith="delete_admin "))
        self._dispatcher.register_callback_query_handler(self._delete_channel, Text(startswith="delchannel "))
        self._dispatcher.register_message_handler(
            self._user_middleware(
                self._admin_or_god_required(self._change_message)), text='Изменить сообщение')
        self._dispatcher.register_message_handler(
            self._user_middleware(
                self._admin_or_god_required(self._add_chat)), text='Добавить чат')
        self._dispatcher.register_message_handler(
            self._user_middleware(
                self._admin_or_god_required(self._send_statistics)), text='Статистика')

    async def _set_delay(self, message: aiogram.types.Message, state: FSMContext):
        if message.text == 'ОТМЕНА':
            await state.finish()
            await message.answer('Успешно отменено')
            return
        try:
            self._message_sender.delay = int(message.text)
            await state.finish()
            await message.answer('Задержка установлена')
        except ValueError:
            await message.answer('Неправильно указана задержка, укажите целое число секунд или ОТМЕНА для отмены')

    async def _change_send_delay(self, call:aiogram.types.CallbackQuery):
        await call.message.answer('Отправьте новую задержку в секундах')
        await GetAnswer.answer_delay.set()

    async def _change_message(self, message: aiogram.types.Message, user:User):
            await message.delete()
            async with (
                aiofiles.open('comment1.txt', mode='r',encoding='utf-8') as comment1,
                aiofiles.open('comment2.txt', mode='r', encoding='utf-8') as comment2
            ):
                comment1_text = await comment1.read()
                comment2_text = await comment2.read()
            text = messages_answer.format(self._message_sender.delay, comment1_text, comment2_text)
            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text='1', callback_data='changemess 1'))
            keyb.add(InlineKeyboardButton(text='2', callback_data='changemess 2'))
            keyb.add(InlineKeyboardButton(text='3', callback_data='changedelay'))
            await message.answer(text, reply_markup = keyb,disable_web_page_preview= self.disable_web_page)

    async def _change_message_state(self, call:aiogram.types.CallbackQuery):
        await call.message.answer('Отправьте новое сообщение')
        await GetAnswer.answer_message.set()
        state = self._dispatcher.current_state()
        state.update_data(message_id=call.data.split()[1])

    async def _set_message(self, message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        state_data = await state.get_data()
        async with aiofiles.open(f'comment{state_data["message_id"]}.txt', mode='w',encoding='utf-8') as f:
                await f.write(message.text.strip())
        await message.answer(f'Сообщение{state_data["message_id"]} добавлено')

    async def _add_chat(self, message: aiogram.types.Message, user:User):
        await message.delete()
        all_channels = await self._channel_storage.get_all_channels()
        text = 'Здесь все каналы, нажмите на старый, чтобы удалить, или на плюс чтобы добавить новый'
        keyb = InlineKeyboardMarkup()
        if all_channels:
            for channel in all_channels:
                keyb.add(InlineKeyboardButton(text=str(channel.title[:12]),callback_data=f'delchannel {channel.id}'))
        keyb.add(InlineKeyboardButton(text='+', callback_data='addchat' ))
        await message.answer(text, reply_markup = keyb)

    async def _delete_channel(self, call:aiogram.types.CallbackQuery):
        id = int(call.data.split()[1])
        channel_to_delete = await self._channel_storage.get_by_id(id)
        if channel_to_delete:
            await self._message_sender.leave_chat(channel_to_delete.chat_id)
            await self._channel_storage.delete(channel_to_delete)
            await call.answer(f'Канал {channel_to_delete.title} был удален')
        else:
            await call.answer(f'Канал не был найден')

    async def _delete_admin(self, call:aiogram.types.CallbackQuery):
        user_id = int(call.data.split()[1])
        await self._user_storage.delete(user_id)
        await call.message.answer(f'Администратор {user_id} был удален')

    async def _cmd_start(self, message:aiogram.types.Message , user:User):
        if user and user.role == User.GOD:
            await message.answer('Меню', reply_markup=self._god_keyboard_off)
        elif user and user.role == User.ADMIN:
            await message.answer('Меню', reply_markup=self._menu_keyboard_off)

    async def _add_administrator(self, message:aiogram.types.Message, user:User):
        if user.role == User.GOD:
            await message.delete()
            text = 'Здесь все администраторы, нажмите на старого, чтобы удалить, или на плюс чтобы добавить нового'
            keyb = InlineKeyboardMarkup()
            admins = await self._user_storage.get_admins()
            if admins:
                for admin in admins:
                    keyb.add(InlineKeyboardButton(text=admin.id,callback_data=f'delete_admin {admin.id}'))
            keyb.add(InlineKeyboardButton(text='+', callback_data='addadmin' ))
            await message.answer(text, reply_markup = keyb)

    async def _add_chat_call(self, call:aiogram.types.CallbackQuery):
        await call.message.answer(f'Отправьте ссылку на нужный канал')
        await GetAnswer.answer_channel.set()

    async def _add_channel(self, message):
        channel_data = await self._message_sender.get_channel_data(message.text.split('/')[-1])
        await self._message_sender.join_chat(channel_data.linked_chat.id)
        await self._channel_storage.create(Channel(
                id = channel_data.id,
                username = channel_data.username,
                title = channel_data.title,
                messages= 0,
                chat_id = channel_data.linked_chat.id,
                last_updated_time= datetime.now()
        ))

    async def _process_channel(self, message: aiogram.types.Message, state: FSMContext):
        if message.text.strip() == 'ОТМЕНА':
            await state.finish()
            await message.answer('Отменено')
        else:
            await self._add_channel(message)
            await state.finish()
            await message.answer('Канал принят в работу')

    async def _add_admin(self, call):
        await call.message.answer('Отправьте id новго администратора')
        await GetAnswer.answer_admin.set()

    async def _process_admin(self, message: aiogram.types.Message, state: FSMContext):
        user_id = int(message.text.strip())
        user = await self._user_storage.get_by_id(user_id)
        if message.text.strip() == 'cancel':
            await state.finish()
            await message.answer('Отменено')
        elif user and user.role == User.ADMIN:
            await message.answer('Этот аккаунт уже администратор')
        else:
            await self._user_storage.create(User(user_id,User.ADMIN))
            await message.answer('Администратор добавлен')
        await state.finish()

    async def _turn_bot_on(self, message:aiogram.types.Message, user:User):
        await message.delete()
        self._message_sender.enable()
        if user.role == User.GOD:
            await message.answer('Бот включен', reply_markup=self._god_keyboard_off)
        elif user.role == User.ADMIN:
            await message.answer('Бот включен', reply_markup=self._menu_keyboard_off)

    async def _turn_bot_off(self, message:aiogram.types.Message, user:User):
        await message.delete()
        self._message_sender.disable()
        if user.role == User.GOD:
            await message.answer('Бот выключен', reply_markup=self._god_keyboard_on)
        elif user.role == User.ADMIN:
            await message.answer('Бот выключен', reply_markup=self._menu_keyboard_on)

    async def _send_statistics(self, message, user:User):
        await message.delete()
        channels = await self._channel_storage.get_all_channels()
        if channels is not None:
            text = ''
            for channel in channels:
                text += f'{channel.title} {channel.messages}\n'
            await message.answer(text)
        else:
            await message.answer('Бот отправил 0 сообщений')
    
    def _user_middleware(self, func:Callable) -> Callable:
        async def wrapper(message:aiogram.types.Message, *args, **kwargs):
            user = await self._user_storage.get_by_id(message.chat.id)
            if user is not None:
                await func(message, user)
        return wrapper
    
    def _admin_or_god_required(self, func:Callable) -> Callable:
        async def wrapper(message:aiogram.types.Message, user:User, *args, **kwargs):
            if user.role == User.ADMIN or user.role == User.GOD:
                await func(message, user)
        return wrapper
    
    def _create_keyboards(self):
        self._menu_keyboard_off = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Добавить чат'),KeyboardButton('Изменить сообщение'))\
                .row(KeyboardButton('Статистика'), KeyboardButton('Включить бота'))
        
        self._menu_keyboard_on = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Добавить чат'),KeyboardButton('Изменить сообщение'))\
                .row(KeyboardButton('Статистика'),(KeyboardButton('Выключить бота')))
        
        self._god_keyboard_off = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Добавить чат'),KeyboardButton('Изменить сообщение'))\
                .row(KeyboardButton('Статистика'), KeyboardButton('Добавить администратора'))\
                    .row(KeyboardButton('Выключить бота'))
        
        self._god_keyboard_on = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Добавить чат'),KeyboardButton('Изменить сообщение'))\
                .row(KeyboardButton('Статистика'), KeyboardButton('Добавить администратора'))\
                    .row(KeyboardButton('Включить бота'))