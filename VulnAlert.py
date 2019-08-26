#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Andrey Glauzer'
__license__ = "MIT"

import json
import sqlite3
import logging
import urllib3
import requests
import os
import sys
import csv
import logging
import argparse
import time
import yaml
from email import encoders
from xlsxwriter.workbook import Workbook
from io import BytesIO
from zipfile import ZipFile
from datetime import date
from bs4 import BeautifulSoup
import smtplib
from urllib.request import urlopen, Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from datetime import datetime, timedelta


class DataBase:
	def __init__(self,
		database_path=None,
		database_name=None,
		splunk_dir=None,
		chat_id=None,
		token=None,
		templatemail=None,
		sendermail=None,
		smtpmail=None,
		portmail=None,
		passwdmail=None,
		mail=None):
		self.today = date.today()
		self.logger = logging.getLogger('DataBaseCVES')
		self.database_path = database_path
		self.database_name = database_name
		self.logs_save_splunk = splunk_dir
		self.chat_id = chat_id
		self.token = token
		self.templatemail=templatemail
		self.sendermail=sendermail
		self.smtpmail=smtpmail
		self.portmail=portmail
		self.passwdmail=passwdmail
		self.mail=mail

		if database_path is not None:
			if not os.path.exists('{path}/{filename}'.format(path=database_path, filename=database_name)):
				self.logger.info('Database does not exist I am creating a new one.')
				conn = sqlite3.connect('{path}/{filename}'.format(path=database_path, filename=database_name))
				cursor = conn.cursor()

				cursor.execute('CREATE TABLE IF NOT EXISTS CVES ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,'
				'name TEXT, product TEXT, referencesCVES TEXT, date TEXT, score NUMERIC, severity TEXT, description TEXT, date_register TEXT);')

				conn.commit()
				conn.close()
			else:
				self.logger.debug(' Banco de dados não existe estou criando um novo.')
				conn = sqlite3.connect('{path}/{filename}'.format(path=database_path, filename=database_name))
				cursor = conn.cursor()

				cursor.execute('CREATE TABLE IF NOT EXISTS CVES ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,'
				'name TEXT, product TEXT, referencesCVES TEXT, date TEXT, score NUMERIC, severity TEXT, description TEXT, date_register TEXT);')

				conn.commit()
				conn.close()

	def email(self,
		logs_save_splunk=None,
		name=None,
		product=None,
		score=None,
		severity=None,
		references=None,
		description=None):

		if logs_save_splunk is not None:
			if not os.path.exists(logs_save_splunk ):
				arquivo = open(logs_save_splunk , 'w', encoding="utf8")
				arquivo.close()
				with open(logs_save_splunk , 'w') as csvfile:
					filewriter = csv.writer(csvfile, delimiter=',')
					filewriter.writerow(['Name', 'Product', 'Score', 'Severity', 'References', 'Description'])
			with open(logs_save_splunk , 'a') as csvfile:
				filewriter = csv.writer(csvfile, delimiter=',')
				filewriter.writerow([name, product, score, severity, references, description])

	def sendemail(self, logs_save_splunk=None):
		if self.mail is not None:
			assunto =  'New CVES newsletter found!'

			num_lines = 0
			with open(logs_save_splunk, 'r') as f:
				for line in f:
					num_lines += 1

			dic_template = {
				'ASSUNTO': assunto,
				'DATE': '{day} de {month} de {year}'.format(day=self.today.day, month=date, year=self.today.year),
				'TOTAL': num_lines-1,
			}

			with open('utils/template/mail.html', 'r') as file :
			  filedata = file.read()
			  format_template = filedata.format(**dic_template)

			mail_content = format_template
			sender_address = self.sendermail
			recipients = [self.mail]

			message = MIMEMultipart()
			message['From'] = sender_address
			message['To'] = ', '.join(recipients)
			message['Subject'] = assunto
			message.attach(MIMEText(mail_content, 'html'))

			mailfilename = logs_save_splunk
			attachment = open(mailfilename, "rb")

			part = MIMEBase('application', 'octet-stream')
			part.set_payload((attachment).read())
			encoders.encode_base64(part)
			part.add_header('Content-Disposition', "attachment; filename= %s" % mailfilename)

			message.attach(part)
			session = smtplib.SMTP('{0}:{1}'.format(self.smtpmail, self.portmail))
			text = message.as_string()
			session.sendmail(sender_address, recipients, text)



	def telegram(self,
		name=None,
		product=None,
		score=None,
		severity=None,
		references=None,
		description=None,
		chat_id=None,
		token=None):

		if token is not None:
			text =  "CVE: {name}\nProduct: {product}\nScore: {score}\nSeverity: {severity}\nReferences: {references}\n".format(
				name=name,
				product=product,
				score=score,
				severity=severity,
				references=references)

			url = "https://api.telegram.org/bot{token}/sendMessage".format(token=token)

			alert = text.replace('\t', '')
			params = {'chat_id': chat_id, 'text': alert}
			response = requests.post(url, data=params)


	def save(
		self,
		name=None,
		product=None,
		references=None,
		date=None,
		score=None,
		severity=None,
		description=None,
		mydate=None,
		myproducts=None,
		checkproducts=None,
		notification=None,):

		if name is not None:
			conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
			cursor = conn.cursor()
			r = cursor.execute("SELECT name FROM CVES WHERE name='{id}';".format(id=name))

			if r.fetchall():
				self.logger.debug('CVE {cve} is already in the database.'.format(cve=name))
			else:

				conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
				cursor = conn.cursor()
				cursor.execute("""
				INSERT INTO CVES (name,product,referencesCVES,date,score,severity,description,date_register)
				VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
				""" % (name,product,references,date,score,severity,description,self.today))
				conn.commit()
				conn.close()

				if checkproducts:
					for check in myproducts:
						if product.lower() in check['name']['id'].lower():
							if 'mail' in notification.lower():
								self.email(logs_save_splunk=self.logs_save_splunk ,
									name=name,
									product=product,
									score=score,
									severity=severity,
									references=references,
									description=description,)

							elif 'telegram' in notification.lower():

								self.telegram(name=name,
									product=product,
									score=score,
									severity=severity,
									references=references,
									description=description,
									chat_id=self.chat_id,
									token=self.token,)

							elif 'all' in notification.lower():

								self.email(logs_save_splunk=self.logs_save_splunk ,
									name=name,
									product=product,
									score=score,
									severity=severity,
									references=references,
									description=description)

								self.telegram(name=name,
									product=product,
									score=score,
									severity=severity,
									references=references,
									description=description,
									chat_id=self.chat_id,
									token=self.token,)
				else:
					if 'mail' in notification.lower():
						self.email(logs_save_splunk=self.logs_save_splunk ,
							name=name,
							product=product,
							score=score,
							severity=severity,
							references=references,
							description=description,)

					elif 'telegram' in notification.lower():

						self.telegram(name=name,
							product=product,
							score=score,
							severity=severity,
							references=references,
							description=description,
							chat_id=self.chat_id,
							token=self.token,)

					elif 'all' in notification.lower():

						self.email(logs_save_splunk=self.logs_save_splunk ,
							name=name,
							product=product,
							score=score,
							severity=severity,
							references=references,
							description=description)

						self.telegram(name=name,
							product=product,
							score=score,
							severity=severity,
							references=references,
							description=description,
							chat_id=self.chat_id,
							token=self.token,)




class AlertCVES:
	def __init__(self):
		logging.basicConfig(
				level=logging.INFO,
				format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S',
		)
		self.logger = logging.getLogger('Start Alert')

		parser = argparse.ArgumentParser()
		parser.add_argument('-c', '--config', help='The directory of the settings file, in Yaml format.',
						   action='store', dest = 'config')
		parser.add_argument('-i', '--initial', help='Use this command before --config, if it is the first time you are running the script, so that it can write to the database all CVES already reported to date, without the alert being sent.',
						   action='store_true', dest = 'initial')
		parser.add_argument('-p', '--products', help='Use this command before --config if you would like to receive only CVES alerts whose product is from the list in the configuration files.',
						   action='store_true', dest = 'products')
		parser.add_argument('-t', '--type', help='Enter the type of alert you want to send. Email or Telegram, if you want to use both use: all',
						   action='store', dest = 'type')
		args = parser.parse_args()


		frameworks = ['mail', 'telegram', 'all', 'email']

		if args.type.lower() in frameworks:
			self.logger.debug('You have entered a valid type alert.')
			self.type = args.type
		else:
			self.logger.error('Invalid Type Alert\n')
			sys.exit(1)

		self.initial = args.initial
		self.products = args.products

		if os.path.exists(args.config):
			if '.yml' in args.config:
				with open(args.config, 'r') as stream:
					data = yaml.load(stream, Loader=yaml.FullLoader)
					self.database_path = data.get('database_path', '')
					self.database_name = data.get('database_name', '')
					self.telegram = data.get('telegram', '')
					self.chat_id = data.get('chat_id', '')
					self.token = data.get('token', '')
					self.mail = data.get('mail', '')
					self.cc = data.get('cc', '')
					self.sendermail = data.get('sendermail', '')
					self.smtpmail = data.get('smtpmail', '')
					self.portmail = data.get('portmail', '')
					self.passwdmail = data.get('passwdmail', '')
					self.myproducts = data.get('products', '')
					self.debug = data.get('debug', '')
					self.score = data.get('score', '')
					self.templatemail = data.get('templatemail', '')
					self.splunk_dir = data.get('splunk_dir', '')
					self.today = date.today()


				self.logs_save_splunk = '{0}/CVES-{1}.csv'.format(self.splunk_dir, datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"))

				self.database = DataBase(
					database_path=self.database_path,
					database_name=self.database_name,
					splunk_dir=self.logs_save_splunk,
					chat_id=self.chat_id,
					token=self.token,
					templatemail=self.templatemail,
					sendermail=self.sendermail,
					smtpmail=self.smtpmail,
					portmail=self.portmail,
					passwdmail=self.passwdmail,
					mail=self.mail)

				self.url = [
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-modified.json.zip",
					   "https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-recent.json.zip",
					   "https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-{year}.json.zip".format(year=self.today.year)
				]

				self.olds = [
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2002.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2003.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2004.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2005.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2006.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2007.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2008.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2009.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2010.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2011.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2012.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2013.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2014.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2015.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2016.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2017.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-2018.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-modified.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-recent.json.zip",
					"https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-{year}.json.zip".format(year=self.today.year)
				]

				if self.debug:
					logging.basicConfig(
							level=logging.DEBUG,
							format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
							datefmt='%Y-%m-%d %H:%M:%S',
						)
				else:
					logging.basicConfig(
							level=logging.INFO,
							format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
							datefmt='%Y-%m-%d %H:%M:%S',
						)

				self.logger = logging.getLogger('Start:CVE')
			else:
				self.logger.error('Entered file type is not valid, must be of format yml.\n')
				sys.exit(1)
		else:
			self.logger.error('File does not exist or path is incorrect.\n')
			sys.exit(1)

	@property
	def start(self):
		self.logger.info('Starting CVE Download Process')
		self.download()
		if 'mail' in self.type.lower():
			self.logger.info('Sending Email ...')
			self.database.sendemail(logs_save_splunk=self.logs_save_splunk)
		elif 'all'  in self.type.lower():
			self.logger.info('Sending Email ...')
			self.database.sendemail(logs_save_splunk=self.logs_save_splunk)


	def data(self, loaded=None):
		if loaded is not None:
			self.logger.info("Debugging Json's information ..")

			for mycves in loaded['CVE_Items']:
				references = None
				date = None
				score = None
				severity = None
				description = None
				product = None

				if self.today.month <= 9:
					date_cve = '0{date}'.format(date=self.today.month)
				else:
					date_cve = self.today.month
				if mycves['publishedDate'].split('-')[1] == date_cve:

					for scores in mycves['impact']:
						if scores == 'baseMetricV3':
							score = mycves['impact'][scores]['cvssV3']['baseScore']
							severity = mycves['impact'][scores]['cvssV3']['baseSeverity']

					if score is not None:
						if float(score) >= self.score:
							description = mycves['cve']['description']['description_data'][0]['value'] \
								.replace("'", "") \
								.replace('"', '')
							name = mycves['cve']['CVE_data_meta']['ID']
							for vendor in mycves['cve']['affects']['vendor']['vendor_data']:
								product = vendor['vendor_name'] \
									.replace("'", "") \
									.replace('"', '').lower()

							references_cves = []
							for reference_data in mycves['cve']['references']['reference_data']:
								myreferences = reference_data['url'] \
									.replace("'", "") \
									.replace('"', '')
								references_cves.append(myreferences)

							if references_cves:
								references = references_cves[0]
							else:
								references =  "Null"

							date = mycves['publishedDate'].split('T')[0]

							if "** REJECT **" in description:
								self.logger.debug('CVE {cve} rejected'.format(cve=name))
							else:
								self.database.save(name=name,
									product=product,
									references=references,
									date=date,
									score=score,
									severity=severity,
									description=description,
									mydate=self.today,
									myproducts=self.myproducts,
									checkproducts=self.products,
									notification=self.type)

	def download(self):
		self.logger.info('Getting CVES')
		if self.initial:
			for urls in self.olds:
				self.logger.info('Getting from {url}'.format(url=urls))
				url = urlopen(urls)
				zf = ZipFile(BytesIO(url.read()))
				for item in zf.namelist():
					with zf.open(item) as f:
						 data = f.read()
						 loaded = json.loads(data)
				self.logger.debug('Data already obtained, now it must be processed.')
				self.data(loaded=loaded)
		else:
			for urls in self.url:
				self.logger.info('Getting from {url}'.format(url=urls))
				url = urlopen(urls)
				zf = ZipFile(BytesIO(url.read()))
				for item in zf.namelist():
					with zf.open(item) as f:
						 data = f.read()
						 loaded = json.loads(data)
				self.logger.debug('Data already obtained, now it must be processed.')
				self.data(loaded=loaded)


try:
	alerts = AlertCVES()
	alerts.start
except KeyboardInterrupt:
	print('\nIt looks like the script has been terminated by the user.')
	sys.exit(1)
