from aiogram.types import Message as TelegramMessage
from logger import logger
import sqlite3
import time
import sys
import os

os.chdir(sys.path[0])

class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file

    def condb(self):
        con = sqlite3.connect(self.db_file)
        return con

    def raw_execute(self, line: str, parameters: tuple = None):
        logger.debug(f'Database raw execute: {line}, {parameters}')
        con = self.condb()
        cursor = con.cursor()

        if parameters == None:
            cursor.execute(line)
        
        elif parameters != None:
            cursor.execute(line, parameters)

        data = cursor.fetchall()

        con.commit()
        con.close()

        return data

    def start(self):
        logger.info('Initializing database')
        if not os.path.isfile(self.db_file):
            try:
                con = self.condb()
                cursor = con.cursor()

                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    user_name STRING,
                    user_id INTEGER,
                    random_usage INTEGER,
                    dem_usage INTEGER);
                ''')

                con.commit()
                logger.info(f'Created DB ({self.db_file})')
            except sqlite3.Error as error:
                logger.error('Error', error)
            finally:
                if con:
                    con.close()
                    logger.info('DB close')

db = Database('database.db')
db.start()

class User:
    def __init__(self, message: TelegramMessage):
        self.user_id = message.from_user.id
        self.user_name = message.from_user.full_name

    def get_info(self):
        return f'{self.user_name}, {self.user_id}'

    def increase_random(self, multiplier: int = 1):
        logger.debug(f'Increased random for user: {self.get_info()}')
        db.raw_execute(f'UPDATE users SET random_usage = random_usage + {multiplier} WHERE user_id = ?', (self.user_id,))

    def increase_dem(self):
        db.raw_execute('UPDATE users SET dem_usage = dem_usage + 1 WHERE user_id = ?', (self.user_id,))
    
    def get(self):
        logger.debug(f'Get user {self.get_info()}')
        return db.raw_execute('SELECT * FROM users WHERE user_id = ?', (self.user_id,))

    def add_user(self):
        if self.get() == []:
            logger.info(f'Added user: {self.get_info()}')
            return db.raw_execute('INSERT INTO users VALUES(?, ?, ?, ?)', (self.user_name, self.user_id, 0, 0))