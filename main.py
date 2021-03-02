import requests,os,json,time
from pathlib import Path
from dotenv import load_dotenv

basepath = Path()
basedir = str(basepath.cwd())
envars = basepath.cwd() / 'config.env'
load_dotenv(envars)

_url = os.getenv("URL_CRYPTOYA")
_coins = os.getenv("COINS").split(',')
_bot_token = os.getenv("BOT_TOKEN")
_bot_chatID = os.getenv("BOT_CHAT_ID")
_percentageConfig = float(os.getenv("PERCENTAGE"))
_volumen = os.getenv("VOLUMEN")

def getCotizacion(coin,fiat,volumen):
  response = requests.get(_url + '/api/' + coin + '/'+ fiat+ '/' + str(volumen))
  if response:
    exchanges = json.loads(response.text)

    # TO-DO HORRIBLE
    _ask = {'exchange':'','price':''}
    _bid = {'exchange':'','price':''}
    _ask['exchange'] = 'argenbtc'
    _bid['exchange'] = 'argenbtc'
    _ask['price'] = exchanges[list(exchanges)[0]]['totalAsk']
    _bid['price'] = exchanges[list(exchanges)[0]]['totalBid']

    # set bet prices
    for exchange in exchanges:
      if _ask['price']> exchanges[exchange]['totalAsk']:
        _ask['price'] = exchanges[exchange]['totalAsk']
        _ask['exchange'] = exchange
      if _bid['price']< exchanges[exchange]['totalBid']:
        _bid['price'] = exchanges[exchange]['totalBid']
        _bid['exchange'] = exchange

    #set %
    percentage = float(_ask['price'])-float(_bid['price'])*100/float(_bid['price'])

    #check if worth notifing.    
    if  _ask['price']<_bid['price']:# and percentage>=_percentageConfig:
      print(f'Moneda: {coin} para valores de {volumen} con {percentage}%')
      print('Comprar en ' + _ask['exchange'] + ' a: ' + str(_ask['price']))
      print('Vender en ' + _bid['exchange'] + ' a: ' + str(_bid['price']))
      print('spread= ' + str( float(_bid['price']) - float(_ask['price'])))

      bot_message = f'Moneda: {coin} para valores de {volumen}\nComprar en ' + _ask['exchange'] + ' a: ' + str(_ask['price']) + '\nVender en ' + _bid['exchange'] + ' a: ' + str(_bid['price'])   
      
      send_text = 'https://api.telegram.org/bot' + _bot_token + '/sendMessage?chat_id=' + _bot_chatID + '&parse_mode=Markdown&text=' + bot_message
      #response = requests.get(send_text)
  
while True:
  print('Start Run')
  for coin in _coins:
    getCotizacion(coin,'ars',_volumen)
  time.sleep(60)
