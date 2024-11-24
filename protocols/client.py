import asyncio
import json
from datetime import datetime
import globalVariable
from setting import server_log, LogTypes


class Worker:
    def __init__(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        self._reader = reader
        self._writer = writer
        self._ip = writer.get_extra_info('peername')[0]
        self._requestId = 0
        self._id = 0
        self._password = ''
        self._name = ''
        self._softWare = ''
        self._subscribed = False
        self._authorized = False
        self._hasPriorJob = False
        self._extranonceSubscribe = False
        self._lastJobId = ''
        self._extraNonce1 = ''
        self._cionBase1 = ''
        self._coinBase2 = ''
        self._currentDifficulty = globalVariable.START_DIFFICULTY
        self._lastShareTime = datetime.now()
        self._blockFound = 0
        self._foundedShare = []

    def get_reader(self) -> asyncio.streams.StreamReader:
        return self._reader

    def get_writer(self) -> asyncio.streams.StreamWriter:
        return self._writer

    def get_worker_id(self) -> int:
        return self._id

    def set_worker_id(self, worker_id: int):
        self._id = worker_id

    def get_worker_name(self) -> str:
        return self._name

    def set_worker_name(self, worker_name: str):
        self._name = worker_name

    def get_worker_pass(self) -> str:
        return self._password

    def set_worker_pass(self, worker_pass: str):
        self._password = worker_pass

    def get_worker_ip(self) -> str:
        return self._ip

    def set_worker_ip(self, worker_ip: str):
        self._ip = worker_ip

    def get_worker_soft(self) -> str:
        return self._softWare

    def set_worker_soft(self, worker_soft: str):
        self._softWare = worker_soft

    def get_subscribed(self) -> bool:
        return self._subscribed

    def set_subscribed(self, status: bool):
        self._subscribed = status

    def get_authorized(self) -> bool:
        return self._authorized

    def set_authorized(self, status: bool):
        self._authorized = status

    def get_request_id(self) -> int:
        return self._requestId

    def set_request_id(self):
        self._requestId += 1

    def get_has_prior_job(self) -> bool:
        return self._hasPriorJob

    def set_has_prior_job(self, status: bool):
        self._hasPriorJob = status

    def get_extranonce_subscribe(self, status: bool):
        self._extranonceSubscribe = status

    def set_extranonce_subscribe(self, status: bool):
        self._extranonceSubscribe = status

    def get_last_job_id(self):
        return self._lastJobId

    def set_last_job_id(self, status: str):
        self._lastJobId = status

    def get_worker_extra_nonce1(self) -> str:
        return self._extraNonce1

    def set_worker_extra_nonce1(self, extra_nonce1: str):
        self._extraNonce1 = extra_nonce1

    def get_current_difficulty(self) -> float:
        return self._currentDifficulty

    def set_current_difficulty(self, difficulty: float):
        self._currentDifficulty = difficulty

    def get_last_share_time(self) -> datetime:
        return self._lastShareTime

    def set_last_share_time(self, time: datetime):
        self._lastShareTime = time

    def get_block_found(self) -> int:
        return self._blockFound

    def set_block_found(self):
        self._blockFound += 1

    def get__founded_share(self) -> list:
        return self._foundedShare

    def set_founded_share(self, difficulty: float):
        self._foundedShare.append(difficulty)

    def get_coinbase1(self):
        return self._cionBase1

    def set_coinbase1(self, cion_base1: str):
        self._cionBase1 = cion_base1

    def get_coin_base2(self):
        return self._coinBase2

    def set_coin_base2(self, coin_base2: str):
        self._coinBase2 = coin_base2

    async def get_client_request(self) -> dict:
        try:
            read_task = await self._reader.readline()
            if read_task:
                request_body = json.loads(read_task.decode())
                return request_body
            else:
                return {}
        except Exception as er:
            server_log(LogTypes.ERROR, f"Worker getClientRequest", er)
            return {}


    async def send_response_to_client(self, response_message: dict) -> bool:
        try:
            if 'method' in response_message:
                if not self._hasPriorJob and response_message['method'] == 'mining.notify':
                    response_message['params'][-1] = True

            response_message_bytes = (json.dumps(response_message).replace('\n', '')) + '\n'
            response_message_bytes = response_message_bytes.encode('UTF-8')
            self._writer.write(response_message_bytes)
            await self._writer.drain()
            if 'method' in response_message:
                self.set_last_job_id(response_message['params'][0])
            return True
        except Exception as er:
            server_log(LogTypes.ERROR, f"Worker sendResponseToClient", er)
            return False
