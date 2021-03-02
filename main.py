import requests,os,json,logging,sys
from pathlib import Path
from dotenv import load_dotenv

LOG_FILENAME = 'Crypto.log'
LOG_LEVEL=logging.INFO

logging.basicConfig(filename=LOG_FILENAME,level=LOG_LEVEL)

basepath = Path()
basedir = str(basepath.cwd())
envars = basepath.cwd() / 'SECRETS.env'

try:
  load_dotenv(envars)
except Exception as e:
  logging.error(e)

#load secrets
_bot_token = os.getenv("BOT_TOKEN")
_bot_chatID = os.getenv("BOT_CHAT_ID")

try:
  with open('config.json', 'r') as f:
    config = json.load(f)
    logging.info("Config loaded")
except IOError as e:
  logging.error(e)

#load config into vars
_url = config["url"]
_coins = config["coins"]
_percentageConfig = float(config["percentage"])
_exchangesEnabled = config["exchanges"]


def getCotizacion(coin,fiat,volumen):
  
  try:
    response = requests.get(_url + '/api/' + coin + '/'+ fiat+ '/' + str(volumen))
  except Exception as e:
    logging.error(e)  

  if response:
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

      bot_message = f'Moneda: {coin} para valores de {volumen}\nComprar en **' + _ask['exchange'] + '** a: ' + str(_ask['price']) + '\nVender en **' + _bid['exchange'] + '** a: ' + str(_bid['price']) + '\n' + str(percentage) +'%'
      send_text = 'https://api.telegram.org/bot' + _bot_token + '/sendMessage?chat_id=' + _bot_chatID + '&parse_mode=Markdown&text=' + bot_message
      
      try:
        response = requests.get(send_text)
      except Exception as e:
        logging.error(e)

def printInfo():
  #TODO FIX this
  print(_coins)
  coins = ''
  for coin in _coins:
    coins += ',' + coin

  print(f'Configured Coins: {coins}' )
  exchanges = ','.join(_exchangesEnabled)
  print(f'Configured Exchanges: {exchanges}')

def main():
  #printInfo()
  for coin in _coins:
    getCotizacion(coin['name'],'ars',coin['vol'])

  sys.exit(0)


if __name__ == '__main__':
  main()