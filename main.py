import asyncio
import requests
import random
import sys
import os

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.methods import DeleteWebhook
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile
from simpledemos import Demotivator
from database import User
from utils import HelpCommand, create_chart, create_pie_chart, resource_fix, add_fix, wrap_media
from PIL import Image
from logger import logger

os.chdir(sys.path[0])

TOKEN = ''

if TOKEN == '':
    logger.error('Enter bot token')
    quit()
    
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

dp = Dispatcher()
router = Router()

if not os.path.exists('resources/'):
    logger.info('Create a resources folder')
    os.mkdir('resources')

if not os.path.exists('temp/'):
    logger.info('Create a temp folder')
    os.mkdir('temp')

resources = os.listdir('resources/')
resources_len = len(resources)

if resources_len == 0:
    logger.error("You don't have any pictures in the resources folder")
    quit()

admins = []

usage_list = []

commands = [
    HelpCommand('random', 'Выдаёт рандомную картинку'),
    HelpCommand('stats', 'Ваша статистика'),
    HelpCommand('dem', 'Создаёт демотиватор', ('текст 1', 'текст 2')),
    HelpCommand('lowres', 'Делает картинку низкого качества')
]

@dp.message(CommandStart())
async def start_command(message: types.Message):
    
    User(message).add_user()

    await message.reply(f'Привет, у меня есть очень много картинок с никитой, около {resources_len} штук!\nНапиши /random чтобы получить одну из них')

@dp.message(Command(commands='refresh'))
async def refresh_images(message: types.Message):
    if message.from_user.id in admins:
        global resources, resources_len

        old_array = resources

        resources = os.listdir('resources/')

        new_elements = set(resources) - set(old_array)

        length = len(new_elements)

        await message.reply(f'Обновляем базу ресурсов, {add_fix(length) + resource_fix(length)}\nНовые элементы ({length}): <code>{", ".join(new_elements)}</code>')
    else:
        await message.reply('Только для владельцев')

@dp.message(Command(commands='random'))
async def send_random_photo(message: types.Message):
    user = User(message)
    user.add_user()

    rnd_file = random.choice(resources)

    logger.debug(f'User ({user.get_info()}) executed /random')

    if rnd_file.endswith(('.jpg', '.png', '.jpeg')):
        await message.reply_photo(FSInputFile('resources/' + rnd_file), caption=f'<code>{rnd_file}</code>')
        user.increase_random()
    
    elif rnd_file.endswith(('.mp4')) and rnd_file.startswith('doc_'):
        await message.reply('Вы выбили легендарный кружок, +10 очков в /stats')
        await message.reply_video_note(FSInputFile('resources/' + rnd_file))

        user.increase_random(10)

    elif rnd_file.endswith(('.mp4')) and rnd_file.startswith('video_'):
        await message.reply_video(FSInputFile('resources/' + rnd_file), caption=f'<code>{rnd_file}</code>')
        user.increase_random()

@dp.message(Command(commands='stats'))
async def stats(message: types.Message):
    logger.debug('User executed /stats')
    try:
        await message.reply(f'Вы использовали команду /random {User(message).get()[0][2]} раза!')
    except IndexError:
        await message.reply('Вы ещё не использовали бота, напишите /random!')

@dp.message(Command(commands='dem'))
async def demotivator(message: types.Message):
    try: 
        if message.text != None:
            text = ' '.join(message.text.split(' ')[1:]).split('-')
            logger.debug(f'User executed /dem, {text}')
        else:
            return

    except IndexError:
        await message.reply('Пожалуйста введите текст, пример: <code>Я ничего - Не сливал</code>')
        return
    

    top_text = text[0]

    try:
        down_text = text[1]
    except IndexError:
        down_text = ''
    
    if message.reply_to_message == None or message.reply_to_message.photo == None:
        await message.reply('Ответьте на сообщение с фотографией')
        return

    user = User(message)
    user.add_user()
    user.increase_dem()

    dem = Demotivator(top_text, down_text)
    
    dem_orig_file = f'temp/demotivator-{message.message_id}_orig.jpg'
    dem_work_file = f'temp/demotivator-{message.message_id}_work.jpg'

    await bot.download(message.reply_to_message.photo[-1].file_id, dem_orig_file)
    
    dem.create(dem_orig_file, watermark='@veryenten_bot', result_filename=dem_work_file)

    await message.reply_photo(FSInputFile(dem_work_file))

    os.remove(dem_orig_file)
    os.remove(dem_work_file)

@dp.message(Command(commands='lowres'))
async def lowres(message: types.Message):
    User(message).add_user()

    if message.reply_to_message == None or message.reply_to_message.photo == None:
        await message.reply('Ответьте на сообщение с фотографией')
        return
    
    try:
        quality = int(message.text.split(' ')[1])
        if quality > 100 or quality < 0:
            await message.reply('Напишите цифру от 1 до 100!')
            return
        
    except IndexError:
        quality = 25

    file = f'{message.message_id}-lowres.jpg'
    file_done = f'{message.message_id}-lowres-done.jpg'

    await bot.download(message.reply_to_message.photo[-1].file_id, file)
  
    image_file = Image.open(file)
    image_file.save(file_done, quality=quality) 

    await message.reply_photo(FSInputFile(file_done))

    os.remove(file)
    os.remove(file_done)

@dp.message(Command(commands='add'))
async def add(message: types.Message):
    if message.from_user.id in admins:
        logger.debug('Admin requested add picture')

        if message.reply_to_message == None:
            await message.reply('Ответьте на сообщение с медиа')
            return

        file = 'IMG_' + message.reply_to_message.date.strftime("%Y%m%d_%H%M%S_%f")[:-3] + '.jpg'
        
        if not os.path.exists('resources/' + file):
            await bot.download(message.reply_to_message.photo[-1].file_id, './resources/' + file)

            await refresh_images(message)
        else:
            await message.reply('Эта картинка уже добавлена в бота')

    else:
        await message.reply('Только для владельцев')

@dp.message(Command(commands='help'))
async def help(message: types.Message):
    text = []

    for c in commands:
        text.append(c.formatted)

    await message.reply('\n'.join(text))

@dp.message(Command(commands='usage'))
async def usage(message: types.Message):
    if message.from_user.id in admins or message.from_user.id in usage_list:
        logger.debug('Admin/Usage user requested usage chart')

        try:
            type = message.text.split(' ')[1]
        except IndexError:
            create_chart()
            
            await message.reply_photo(FSInputFile('temp/usage_chart.png'))

            os.remove('temp/usage_chart.png')

        else:
            if type == 'pie':
                create_pie_chart()
            
                await message.reply_photo(FSInputFile('temp/pie_chart.png'))

                os.remove('temp/pie_chart.png')

            elif type == 'grafana':
                with open('temp/grafana.png', 'wb') as image:
                    image.write(requests.get('enter grafana path (with render)').content)

                await message.reply_photo(FSInputFile('temp/grafana.png'), caption='<b>Grafana Dashboard</b> <code>SQlite Monitoring</code>')

                os.remove('temp/grafana.png')
    else:
        await message.reply('Только для владельцев')

async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    
    logger.info('Starting bot..')

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
