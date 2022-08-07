import logging
from flask import Flask
from threading import Thread

# Ping this server periodically with
# https://uptimerobot.com
app = Flask('')

@app.route('/')
def home():
    index = """
    <body style="background-color:#1c2333; color:white; font-family: monospace; font-size: 16px;">
    Flask server ready!
    </body>
    """
    return index

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
  log = logging.getLogger('werkzeug')
  log.disabled = True 
  t = Thread(target=run)
  t.start()