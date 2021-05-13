import requests,os,json,logging,sys
from pathlib import Path
from dotenv import load_dotenv
import sqlite3

basepath = Path()

LOG_FILENAME = basepath.cwd() / 'crypto.log'
LOG_LEVEL=logging.INFO

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',filename=LOG_FILENAME,level=LOG_LEVEL,datefmt='%Y-%m-%d %H:%M:%S')

try:
  envars = basepath.cwd() / 'SECRETS.env'
  load_dotenv(envars)
  logging.info("ENV loaded")
except Exception as e:
  logging.error(e)

#load secrets
_bot_token = os.getenv("BOT_TOKEN")
_bot_chatIDS = os.getenv("BOT_CHAT_IDS").split(',')

try:
  configFile = basepath.cwd() / 'config.json'
  with open(configFile, 'r') as f:
    config = json.load(f)
    logging.info("Config loaded")
except IOError as e:
  logging.error(e)

#load config into vars
_url = config["url"]
_percentageConfig = float(config["percentage"])
_exchangesEnabled = config["exchanges"]
_coins = config["coins"]

_telegramAPI = 'https://api.telegram.org'


try:
  conn = sqlite3.connect('telegram.db')
  cur = conn.cursor()
  #cur.execute("create table user(user_id)")
  #cur.execute("create table parameters (name, value)")
  #cur.execute("insert into parameters values (?,?)", ("last_update_id",1))
  #conn.commit()
except IOError as e:
  logging.error(e)


cur.execute("select * from parameters where name=:name ", {"name": "last_update_id"})
res = cur.fetchone()
_last_update_id = res[1]+1

def main():
  for coin in _coins:
    getCotizacion(coin['name'],'ars',coin['vol'])
  getNewUsers()
  conn.close()
  sys.exit(0)

def getCotizacion(coin,fiat,volumen):
  logging.info(f'Coin: %s Fiat: %s Vol: %s' % (coin,fiat,volumen))
  try:
    response = requests.get(_url + '/api/' + coin + '/'+ fiat+ '/' + str(volumen))
    logging.info(response)
  except Exception as e:
    logging.error(e)

  if response.status_code == 200:
    exchanges = json.loads(response.text)

    # init vars
    _ask = {'exchange':'','price':''}
    _bid = {'exchange':'','price':''}
    _ask['exchange'] = list(exchanges)[0]
    _bid['exchange'] = list(exchanges)[0]
    _ask['price'] = exchanges[list(exchanges)[0]]['totalAsk']
    _bid['price'] = exchanges[list(exchanges)[0]]['totalBid']

    # set bet prices
    for exchange in exchanges:
      if _ask['price'] > exchanges[exchange]['totalAsk'] and exchange in _exchangesEnabled:
        _ask['price'] = exchanges[exchange]['totalAsk']
        _ask['exchange'] = exchange
      if _bid['price'] < exchanges[exchange]['totalBid'] and exchange in _exchangesEnabled:
        _bid['price'] = exchanges[exchange]['totalBid']
        _bid['exchange'] = exchange

    #set %
    percentage = float((_bid['price'])-float(_ask['price']))*100/float(_bid['price'])

    #check if worth notifing.    
    if  _ask['price']<_bid['price'] and percentage>=_percentageConfig:
      logging.info(f'Moneda: {coin} para valores de {volumen} con {percentage}%')
      logging.info('Comprar en ' + _ask['exchange'] + ' a: ' + str(_ask['price']))
      logging.info('Vender en ' + _bid['exchange'] + ' a: ' + str(_bid['price']))
      logging.info('spread= ' + str(float(_bid['price']) - float(_ask['price'])))
      
      sPercentage = "%.2f" % round(percentage, 2)
      bot_message = f'Moneda: {bold(coin)} para volumen de {volumen}\nComprar en ' + bold(_ask['exchange']) + ' a'+ italic('_(ARS)_') +': ' + str(_ask['price']) + '\nVender en ' + bold(_bid['exchange']) + ' a'+ italic('_(ARS)_') +': ' + str(_bid['price']) + '\n Spread: ' + sPercentage +'%'
      
      cur.execute("select * from user ")
      users_ids = cur.fetchone()
      if users_ids:
        for chat_id in users_ids:
          send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + bot_message      
          try:
            response = requests.get(send_text)
            logging.info(response)
          except Exception as e:
            logging.error(e)


def bold(str):
  return '*'+str+'*'

def italic(str):
  return '_'+str+'_'

def getNewUsers():
  global _last_update_id
  try:
    response = requests.get(_telegramAPI +'/bot' + _bot_token + '/getUpdates?offset='+ str(_last_update_id))
    logging.info(response)
  except Exception as e:
    logging.error(e)

  if response.status_code == 200:
    updates = json.loads(response.text)
    if updates['ok']:
      for update in updates['result']:
        chat_id = update['message']['from']['id']
        first_name = update['message']['from']['first_name']
        last_name = update['message']['from']['last_name']
        _last_update_id = update['update_id']
        update_param(conn,'last_update_id',_last_update_id)
        logging.info(str(chat_id) + first_name + last_name + str(_last_update_id))

        if update['message']['text'] == '/start':
          
          bot_message = f'Hi {first_name} {last_name}, welcome. the script runs every 30 minutes, please be patient.'
          existing = insert_user(conn,str(chat_id))
          if existing:
            bot_message = bot_message + f' You already were in the database of this bot.'
          send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + bot_message      
          try:
            response = requests.get(send_text)
            logging.info(response)
          except Exception as e:
            logging.error(e)

        if update['message']['text'] == '/getexchanges':
          bot_message = 'Exchanges: '
          for exchange in _exchangesEnabled:
            bot_message = f'{bot_message} {exchange}'
          send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + bot_message      
          try:
            response = requests.get(send_text)
            logging.info(response)
          except Exception as e:
            logging.error(e)

        if update['message']['text'] == '/getcoins':
          bot_message = 'Configured Coins:'
          for coin in _coins:
            bot_message = f'{bot_message}, {coin}'
          send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + bot_message      
          try:
            response = requests.get(send_text)
            logging.info(response)
          except Exception as e:
            logging.error(e)

def update_param(conn, name,value):
    sql = ''' UPDATE parameters
              SET value = :value
              WHERE name = :name '''
    cur = conn.cursor()
    cur.execute(sql,  {"name": name, "value":value})
    conn.commit()

def insert_user(conn, chat_id):
    cur = conn.cursor()
    cur.execute("select * from user where user_id=:chat_id ", {"chat_id": chat_id})
    users_ids = cur.fetchone()
    if not(users_ids):
      sql = ''' INSERT INTO user
                (user_id) 
                VALUES (:chat_id)'''      
      cur.execute(sql,  {"chat_id": chat_id})
      conn.commit()
      return False
    return True


if __name__ == '__main__':
  main()
