import smtplib
from email.mime.base import MIMEBase
from email import encoders
from email import generator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import os
import json
import pprint
from jinja2 import Template

class Emails:
    def __init__(self, logger, config:dict):
        self.logger = logger.logging()
        self.config = config

    def sendmail(self,
        template:str,
        subject:str,
        fromm:str,
        to:list,
        cc=None,
        attachment=None,
        infos=None):

        self.logger.info("Gerando o email.")
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = fromm
        msg['To'] = ", ".join(to)
        if cc is not None:
            msg['Cc'] = ", ".join(cc)

        if infos is not None:
            with open(template, 'r') as file:
                html = Template(file.read())
            html = html.render(**infos)
        else:
            html = open(template, "r").read()

        msg.attach(MIMEText(html, 'html'))

        if attachment is not None:
            attachmentopen = open(attachment, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachmentopen).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={attachment}")

            msg.attach(part)

        try:
            session = smtplib.SMTP(f"{self.config.general['emails']['smtp']}:{self.config.general['emails']['port']}")
            text = msg.as_string()
            session.sendmail(fromm, to, text)
        except (smtplib.SMTPConnectError, ConnectionRefusedError) as e:
            self.logger.error(f"It was not possible to send the email, the server was not found or does not allow sending the source.")
