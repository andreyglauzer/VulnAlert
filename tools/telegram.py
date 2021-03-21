import time
import requests
import urllib.parse

class Telegram:
    def __init__(self, args:bytes, logger, config):
        self.logger = logger.logging()
        self.args = args
        self.config = config
        
    def send(self, message):
        alert = urllib.parse.quote(message.replace('\t', ''))
        token = self.config.cve['telegram']['token']
        chat = self.config.cve['telegram']['chat']
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat}&text={alert}&parse_mode=html&disable_web_page_preview=true"
        time.sleep(2)
        response = requests.post(url)
        if response.status_code in [200, 201, 202, 302, 304]:
            return True
        elif response.status_code in range(500, 506):
            self.logger.error(
                "It was not possible to send notification to Telegram.")
            return False
        else:
            self.logger.error(
                "A very crazy error occurred, I was unable to send the notification to Telegram.")
            return False
    