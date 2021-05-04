import requests,os,json,logging,sys
from pathlib import Path
from dotenv import load_dotenv

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

_telegramAPI = 'https://api.telegram.org'
_last_update_id = 0


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
      
      for chat_id in _bot_chatIDS:
        send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + bot_message      
        try:
          response = requests.get(send_text)
          logging.info(response)
        except Exception as e:
          logging.error(e)

def main():
  #for coin in _coins:
    #getCotizacion(coin['name'],'ars',coin['vol'])
  getNewUsers()

  sys.exit(0)

def bold(str):
  return '*'+str+'*'

def italic(str):
  return '_'+str+'_'

def getNewUsers():
  try:
    response = requests.get(_telegramAPI +'/bot' + _bot_token + '/getUpdates')
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

        bot_message = f'Hi {first_name} {last_name}, welcome.'

        if update['message']['text'] == '/start':
          send_text = _telegramAPI + '/bot' + _bot_token + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + bot_message      
          try:
            response = requests.get(send_text)
            logging.info(response)
          except Exception as e:
            logging.error(e)





if __name__ == '__main__':
  main()
