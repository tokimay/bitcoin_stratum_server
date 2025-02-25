

# This file is part of https://github.com/tokimay/bitcoin_stratum_server
# Copyright (C) 2016 https://github.com/tokimay
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# This software is licensed under GPLv3. If you use or modify this project,
# you must include a reference to the original repository: https://github.com/tokimay/bitcoin_stratum_server

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
        self._Job_Ids = []
        self._extraNonce1 = ''
        self._currentDifficulty = globalVariable.START_DIFFICULTY
        self._lastShareTime = datetime.now()
        self._blockFound = 0
        self._foundedShare = []

    def get_writer(self) -> asyncio.streams.StreamWriter:
        return self._writer

    def set_worker_name(self, worker_name: str):
        self._name = worker_name

    def set_worker_pass(self, worker_pass: str):
        self._password = worker_pass

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

    def get_last_job_id(self) -> list:
        return self._Job_Ids

    def set_last_job_id(self, _job_id: str):
        self._Job_Ids.append(_job_id)

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

    def set_block_found(self):
        self._blockFound += 1

    def set_founded_share(self, difficulty: float):
        self._foundedShare.append(difficulty)

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
            if 'method' in response_message and response_message['method'] == 'mining.notify':
                self.set_last_job_id(response_message['params'][0])
            return True
        except Exception as er:
            server_log(LogTypes.ERROR, f"Worker sendResponseToClient", er)
            return False
