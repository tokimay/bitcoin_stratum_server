import os
import socket
import configparser
from datetime import datetime
import globalVariable


class FStyle:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    NORMAL = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class LogTypes:
    ERROR = FStyle.RED
    WARNING = FStyle.YELLOW
    INFO = FStyle.PINK
    SUCCEED = FStyle.GREEN
    IMPORTANT = FStyle.BOLD
    TEXT = FStyle.NORMAL
    SPECIAL = FStyle.CYAN


class ServerException(Exception):
    def __init__(self, error_message: str):
        self._errorMessage = str(error_message)

    def __str__(self):
        return self._errorMessage


def server_log(log_type: str, server_message: str, error_message: Exception or str = ''):
    if error_message:
        server_message = str(server_message) + ': '

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {log_type}{server_message}"
          f"{FStyle.PINK}{error_message}{FStyle.NORMAL}")


def load_setting() -> bool:
    try:
        config = configparser.ConfigParser()
        config.read('setting.ini')

        globalVariable.bitcoinCore_host = config['bitcoin.conf']['host']
        globalVariable.bitcoinCore_user = config['bitcoin.conf']['rpcuser']
        globalVariable.bitcoinCore_password = config['bitcoin.conf']['rpcpassword']
        globalVariable.bitcoinCore_port = config['bitcoin.conf']['port']
        globalVariable.START_DIFFICULTY = int(config['difficulty']['start_difficulty'])
        globalVariable.BTC_ADDRESS = config['address']['btc_address']
        return True
    except Exception as er:
        server_log(LogTypes.ERROR, f"load_setting", er)
        return False


def delete_btc_prior_job_data(active_job: str):
    try:
        job_dir = 'activeJobs'
        for fileName in os.listdir(job_dir):
            if fileName.startswith("BTC_") and not fileName.endswith(active_job):
                os.remove(os.path.join(job_dir, fileName))
                server_log(LogTypes.TEXT, f"{fileName.split('.json')[0]} is no longer an active job.")
    except Exception as er:
        server_log(LogTypes.ERROR, f"deleteBtcPrionJobData", er)


def is_port_available(port: int) -> bool:
    status = is_port_in_use(port)
    if status:
        server_log(LogTypes.WARNING, f"Port {FStyle.UNDERLINE}3333{FStyle.NORMAL}{FStyle.YELLOW} is in use."
                   ,f"\nEnter your sudo password for see details:")
        os.system(f"sudo lsof -i -n -P | grep {port}")
        server_log(LogTypes.WARNING, f"You can use {FStyle.CYAN}'sudo kill -9 {FStyle.BLUE}PID_NUMBER'"
                                    f"{FStyle.NORMAL}{FStyle.YELLOW} to kill process.")
    return not status


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0
