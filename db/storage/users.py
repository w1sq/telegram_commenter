from ..db import DB
from typing import Union, List
from dataclasses import dataclass

@dataclass
class User:
    ADMIN = "admin"
    GOD = "god"

    id:int
    role:str

class UserStorage():
    __table = "users"
    def __init__(self, db:DB):
        self._db = db
    
    async def init(self):
        await self._db.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.__table} (
                id BIGINT PRIMARY KEY,
                role TEXT
            ) 
        ''')

    async def get_by_id(self, id:int) -> User | None:
        data = await self._db.fetchrow(f"SELECT * FROM {self.__table} WHERE id = $1", id)
        if data is None:
            return None
        return User(data[0], data[1])

    async def get_gods(self) -> List[User] | None:
        gods = await self._db.fetch(f"SELECT * FROM {self.__table} WHERE role = $1", User.GOD)
        if gods is None:
            return None
        return [User(god[0], god[1]) for god in gods]

    async def get_admins(self) -> List[User] | None:
        admins = await self._db.fetch(f"SELECT * FROM {self.__table} WHERE role = $1", User.ADMIN)
        if admins is None:
            return None
        return [User(admin[0], admin[1]) for admin in admins]

    async def create(self, user:User):
        await self._db.execute(f'''
            INSERT INTO {self.__table} (id, role) VALUES ($1, $2)
        ''', user.id, user.role)

    async def delete(self, user_id:int):
        await self._db.execute(f'''
            DELETE FROM {self.__table} WHERE id = $1
        ''', user_id)