from unittest.mock import DEFAULT
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
  CallbackQueryHandler, ContextTypes, filters
import requests
import argparse
import math
from pyquery import PyQuery as pq

host = 'http://ORANG-PC:5555'

async def VolumeHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  chat_id, msg_text = (update.message.chat_id, update.message.text)
  list = msg_text.split(" ")
  if len(list) == 1:
    res = requests.get(f"{host}/info")
    await context.bot.send_message(chat_id=chat_id, text=f'Громкость: {int(res.json()["volume"])}')
    return
  try:
    res = requests.get(f'{host}/volume?value={list[1]}')
    if res.status_code == 400:
        raise ValueError
  except ValueError:
    await context.bot.send_message(chat_id=chat_id, text='Error value', \
      reply_markup={'keyboard': reply_kb})
  except ConnectionError:
    await context.bot.send_message(chat_id=chat_id, text='Connection error', \
      reply_markup={'keyboard': reply_kb})

async def NextHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  chat_id, msg_text = (update.message.chat_id, update.message.text)
  list = msg_text.split(' ', 1)
  if len(list) == 1:
    requests.get(f'{host}/next')
  else:
    pass#todo постановка в очередь

async def PrevHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  requests.get(f'{host}/prev')

async def PauseHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  requests.get(f'{host}/pause')

async def PlayHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  chat_id, msg_text = (update.message.chat_id, update.message.text)
  list = msg_text.split(' ', 1)
  if len(list) == 1:
    await context.bot.send_message(chat_id=chat_id, text='Need value', \
      reply_markup={'keyboard': reply_kb})
    return
  else:
    try:
      res = requests.get(f'{host}/play?id={int(list[1])}')
      if res.status_code == 400:
        await context.bot.send_message(chat_id=chat_id, text='Number too big', \
          reply_markup={'keyboard': reply_kb})
        return
    except ValueError:
      res = requests.get(f'{host}/play?text={list[1]}')
      if res.status_code == 204:
        await context.bot.send_message(chat_id=chat_id, text='Not found', \
          reply_markup={'keyboard': reply_kb})
        return
      arr = res.json()
      if arr is not None:
        kb = []
        i = 0
        while i < math.ceil(len(arr)):
          kb.append([{'text': t['Id'] + 1, 'callback_data': t['Id'] + 1} \
            for t in arr[i : i + 5]])
          i = i + 5

        await context.bot.send_message(chat_id=chat_id, \
          text='\n'.join([f"{t['Id'] + 1} - {t['Song']}" for t in arr]), \
          reply_markup={'inline_keyboard': kb})

async def CallbackHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query_id, query_data = (update.callback_query.id, update.callback_query.data)
  requests.get(f'{host}/play?id={int(query_data)}')
  await context.bot.answer_callback_query(query_id)

async def LyricsHandle(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message is None:
    return
  chat_id, msg_text = (update.message.chat_id, update.message.text)
  list = msg_text.split(' ', 1)
  if len(list) == 1:
    info = requests.get(f"{host}/info").json()
    page = requests.get(f'https://google.com/search?q={info["artist"]} {info["title"]} lyrics').text
    p = pq(page)
    title = p('span').filter(lambda i, this: pq(this).html().lower() == info['title'].lower())
    if len(title) > 0:
      parent = title.parent().parent().next().next()
      text = pq(parent.find('div:first-child').filter(lambda i, this: len(this.classes) > 0 and pq(this).html().find('<') == -1)[1]).html()
    else:
      text = 'Not found'
  else:
    page = requests.get(f'https://google.com/search?q={list[1]} lyrics').text
    p = pq(page)
    words = list[1].split(' ')
    for i in range(1, len(words) - 1):
      for j in range(len(words) - 1 - i):
        title = p('span').filter(lambda i, this: pq(this).html().lower() == ' '.join(words[j:j + i]).lower())
        if len(title) > 0:
          break
      if j != len(words) - 1 - i:
        break
    
    if i != len(words) - 1:
      parent = title.parent().parent().next().next()
      text = pq(parent.find('div:first-child').filter(lambda i, this: len(this.classes) > 0 and pq(this).html().find('<') == -1)[1]).html()
    else:
      text = 'Not found'
  
  await context.bot.send_message(chat_id=chat_id, text=text, \
    reply_markup={'keyboard': reply_kb})

async def MessageHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  text = ''
  msg_text, chat_id = (update.message.text, update.message.chat_id)
  info = requests.get(f"{host}/info").json()
  match msg_text:
    case '⏮':
      requests.get(f'{host}/prev')
    case '⏯':
      requests.get(f'{host}/pause')
    case '⏭':
      requests.get(f'{host}/next')
    case '🔂':
      requests.get(f'{host}/repeat')
      text=f'Режим повторения {"включён" if info["repeat"] else "выключен"}'
    case '🔀':
      requests.get(f'{host}/shuffle')
      text=f'Режим перемешивания {"включён" if info["shuffle"] else "выключен"}'
    case '🔇':
      requests.get(f'{host}/mute')
    case '⤵':
      pass
    case 'ℹ':
      text=f'Трек: {info["index"] + 1}. {info["artist"]} - {info["title"]}\n' +\
        f'Состояние: {"▶" if info["playing"] else "⏸"} Повтор: {"🔂" if info["repeat"] else "🔁"}' + \
        f'Перемешивание: {"🔀" if info["shuffle"] else "➡"}'
    case '📜':
      page = requests.get(f'https://google.com/search?q={info["artist"]} {info["title"]} lyrics').text
      p = pq(page)
      title = p('span').filter(lambda i, this: pq(this).html().lower() == info['title'].lower())
      if len(title) > 0:
        parent = title.parent().parent().next().next()
        text = pq(parent.find('div:first-child').filter(lambda i, this: len(this.classes) > 0 and pq(this).html().find('<') == -1)[1]).html()
      else:
        text = 'Not found'
    case _:
      try:
        res = requests.get(f'{host}/play?id={int(msg_text)}')
        if res.status_code == 400:
          await context.bot.send_message(chat_id=chat_id, text='Number too big', \
            reply_markup={'keyboard': reply_kb})
          return
      except ValueError:
        res = requests.get(f'{host}/play?text={msg_text}')
        if res.status_code == 204:
          await context.bot.send_message(chat_id=chat_id, text='Not found', \
            reply_markup={'keyboard': reply_kb})
          return
        arr = res.json()
        if arr is not None:
          kb = []
          i = 0
          while i < math.ceil(len(arr)):
            kb.append([{'text': t['Id'] + 1, 'callback_data': t['Id'] + 1} \
              for t in arr[i : i + 5]])
            i = i + 5

          await context.bot.send_message(chat_id=chat_id, \
            text='\n'.join([f"{t['Id'] + 1} - {t['Song']}" for t in arr]), \
            reply_markup={'inline_keyboard': kb})

  if len(text) > 0:
    await context.bot.send_message(chat_id=chat_id, text=text, \
      reply_markup={'keyboard': reply_kb})

async def InfoHandle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if update.message is None:
    return
  chat_id = update.message.chat_id
  info = requests.get("{host}/info").json()
  await context.bot.send_message(chat_id=chat_id, \
    text=f'Трек: {info["index"] + 1}. {info["artist"]} - {info["title"]}\n' +\
      f'Состояние: {"▶" if info["playing"] else "⏸"} Повтор: {"🔂" if info["repeat"] else "🔁"}' + \
      f'Перемешивание: {"🔀" if info["shuffle"] else "➡"}', \
      reply_markup={'keyboard': reply_kb})

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='get token and other? bot parametrs')
  parser.add_argument('--token', type=str, default='')

  args = parser.parse_args()
  if len(args.token) == 0:
    raise argparse.ArgumentError(message='Token is not defined')
  app =  ApplicationBuilder().token(args.token).build()

  global reply_kb
  reply_kb = [
    [{'text': '⏮'}, {'text': '⏯'}, {'text': '⏭'}],
    [{'text': '🔂'}, {'text': '🔀'}, {'text': '🔇'}],
    [{'text': '⤵' }, {'text': 'ℹ'  }, {'text': '📜'}]
  ]

  app.add_handler(CommandHandler(['volume', 'v'], VolumeHandle))
  app.add_handler(CommandHandler(['pause', 'p'], PauseHandle))
  app.add_handler(CommandHandler('next', NextHandle))
  app.add_handler(CommandHandler('prev', PrevHandle))
  app.add_handler(CommandHandler('play', PlayHandle))
  app.add_handler(CommandHandler(['info', 'i'], InfoHandle))
  app.add_handler(CommandHandler(['lyrics', 'l'], LyricsHandle))
  #app.add_handler(CommandHandler(['queue', 'q'], InfoHandle))

  app.add_handler(MessageHandler(filters.TEXT, MessageHandle))

  app.add_handler(CallbackQueryHandler(CallbackHandle))

  app.run_polling()