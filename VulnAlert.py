import argparse
import os
from engines.vulnerability.cve import CVE
from tools.loghandler import *
from tools.configfile import *
from tools.database import *
from tools.emails import *
from tools.telegram import Telegram

class VulnAlert:
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='VulnAlert',
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument('--config',
            dest="configfile",
            required=True,
            help='Configuration directory and file name.')


        parser.add_argument('--service',
            help="If the script is being used as a service use this parameter in conjunction with --timeleep",
            action='store_true',
            dest="argservice")

        parser.add_argument('--timesleep',
            dest="argtimesleep",
            help='Defines the waiting time for the next round, together with the --service parameter')

        parser.add_argument("--log",
            dest="logLevel",
            default='INFO',
            choices=[
                'DEBUG',
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL'],
            help="Enter the type of log you would like to view. INFO is standard.")

        parser.add_argument("--engine",
            dest="engine",
            choices=[
                'cve'
            ],
            help="Inform which engine you want to run to start the detection process.")

        args = parser.parse_args()
        if args.argservice:
            while True:
                Ingestor(args).start
                time.sleep(int(args.argtimesleep))
        else:
            Ingestor(args).start



class Ingestor:
    def __init__(self, args: object):
        self.config = Config(
            args.configfile)

        log = LoggerHandler(args.logLevel, "ingestor", self.config)
        self.logger = log.logging()
        self.args = args
        self.logger.info("CVE")

        if self.config.general['proxy']['active']:
            self.logger.info("O proxy está ativo e as informações de proxy que estão no arquivo de configurações serão utilizadas.")
            os.environ['http_proxy'] = f"http://{self.config.general['proxy']['ip']}" \
               + f":{self.config.general['proxy']['port']}"
            os.environ['HTTP_PROXY'] = f"https://{self.config.general['proxy']['ip']}" \
                + f":{self.config.general['proxy']['port']}"
            os.environ['https_proxy'] = f"https://{self.config.general['proxy']['ip']}" \
                + f":{self.config.general['proxy']['port']}"
            os.environ['HTTPS_PROXY'] = f"https://{self.config.general['proxy']['ip']}" \
                + f":{self.config.general['proxy']['port']}"

    @property
    def start(self):
        self.logger.info("Start Engine")

        database = DataBase(
            self.args,
            LoggerHandler(
                self.args.logLevel,
                "Database",
                self.config
            ), self.config
        )

        email = Emails(
            LoggerHandler(
                self.args.logLevel,
                "Emails",
                self.config
            ), self.config
        )
        
        telegram = Telegram(
            self.args,
            LoggerHandler(
                self.args.logLevel,
                "Telegram",
                self.config
            ),
            self.config
        )
        
        if self.args.engine is not None:
            if str(self.args.engine).lower() == 'cve':
                CVE(LoggerHandler(self.args.logLevel, "CVE", self.config),
                    self.config,
                    self.args,
                    database,
                    email,
                    telegram).start
            else:
                self.logger.error(f"{self.args.engine} does not correspond to CVE")


VulnAlert()
