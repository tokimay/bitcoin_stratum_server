import base64
import _asyncio
import asyncio
import os
import random
from datetime import timedelta, datetime
from correspondence import calculation
from correspondence.bitcoind import get_address_info
from protocols.stratum import requestParser
from protocols.stratum.stratum import notify, set_difficulty
from protocols.client import Worker
from setting import is_port_available, load_setting, server_log, LogTypes, delete_btc_prior_job_data
import globalVariable

class Server:
    def __init__(self, bind_ip='localhost', bind_port=3333):
        self._loop = asyncio.get_event_loop()
        self._bindPort = bind_port
        self._bindIp = bind_ip
        self._onLineUsers = []
        self._serverTask = None
        self._currentBitcoinNotifyTemplate = ['BTC_00000000']
        self._bitcoinCurrentBlockHeight = 0
        if load_setting():
            globalVariable.bitcoinCore_rpcUrl = globalVariable.bitcoinCore_host + ":" + globalVariable.bitcoinCore_port
            globalVariable.bitcoinCore_authenticate = base64.b64encode(
                bytes(globalVariable.bitcoinCore_user + ":" + globalVariable.bitcoinCore_password, "utf8"))
            globalVariable.SCRIPT_PUBKEY = get_address_info(random.randint(0x0, 0xf),
                                                            globalVariable.BTC_ADDRESS)['result']['scriptPubKey']
        else:
            exit(1)
        if not is_port_available(self._bindPort):
            exit(1)

    def run_server(self):
        self._serverTask = self._loop.create_task(self._run_server(), name='PyPool')
        asyncio.ensure_future(self.send_clients_job(), loop=self._loop)
        asyncio.ensure_future(self.bitcoin_block(), loop=self._loop)
        asyncio.ensure_future(self.set_difficulty(), loop=self._loop)
        self._loop.run_forever()

    async def _run_server(self):
        self.server = await asyncio.start_server(self.client_handler, host=self._bindIp, port=self._bindPort)
        for sock in self.server.sockets:
            server_log(LogTypes.SUCCEED, f"Serving on {sock.getsockname()}")
        async with self.server:
            await self.server.serve_forever()

    def server_status(self, task: _asyncio.Task or None = None):
        if self.server.is_serving():
            for sock in self.server.sockets:
                server_log(LogTypes.SUCCEED, f"Serving on {sock.getsockname()}")
        else:
            server_log(LogTypes.ERROR, f"Server is dead")

    async def client_handler(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        client = Worker(reader, writer)
        if not writer.get_extra_info('socket') in self._onLineUsers:
            self._onLineUsers.append({str(writer.get_extra_info('peername')): client})
            server_log(LogTypes.IMPORTANT, f"client at {client.get_writer().get_extra_info('peername')}"
                                          f" is online now")
        request_handler_task = asyncio.create_task(self._request_handler(client))
        request_handler_task.add_done_callback(self.server_status)
        await request_handler_task

    async def request_handler(self, client: Worker):
        get_request = True
        while get_request:
            get_request = asyncio.run_coroutine_threadsafe(self._request_handler(client), self._loop)
            await asyncio.sleep(1)
            get_request = get_request.result()

    async def _request_handler(self, client: Worker):
        try:
            request_body = await client.get_client_request()
            if request_body:
                server_log(LogTypes.TEXT,
                          f"Receive {LogTypes.SPECIAL}'{request_body['method']}'{LogTypes.TEXT} request"
                          f" from client at {client.get_writer().get_extra_info('peername')}")
                response_message = requestParser.pars_method(request_body, client)
                if response_message:
                    is_send = await client.send_response_to_client(response_message)
                    if is_send:
                        server_log(LogTypes.TEXT,
                                  f"Send response to client at"
                                  f" {client.get_writer().get_extra_info('peername')}")
                    return await self._request_handler(client)
            else:
                return False
        except Exception as er:
            server_log(LogTypes.ERROR, f"Server requestHandler", er)
            return False

    async def send_clients_job(self):
        alive_job_interval = 180  # 180 second = 3 min for resend data to client. client will recognize server is alive
        while True:
            await asyncio.sleep(1)  # start next loop to send job after 1 sec
            result_job = asyncio.run_coroutine_threadsafe(self._send_clients_job(alive_job_interval), self._loop)
            if alive_job_interval == 0:
                alive_job_interval = 180  # refresh
                self.server_status()
            else:
                alive_job_interval -= 1  # means 1 sec pass

    async def _send_clients_job(self, send_alive_job_interval: int):
        for i in range(len(self._onLineUsers)):
            key = list(self._onLineUsers[i].keys())[0]
            client = self._onLineUsers[i][key]
            if (((client.get_subscribed() or client.get_authorized()) and not client.get_has_prior_job())
                    or (send_alive_job_interval == 0)):
                is_send_job = False
                if not is_send_job:
                    is_send_job = await client.send_response_to_client(
                        response_message=notify(client, notify_body=self._currentBitcoinNotifyTemplate))
                if is_send_job:
                    server_log(LogTypes.TEXT, f"Send job to client at"
                                             f" {client.get_writer().get_extra_info('peername')}")
                    client.set_has_prior_job(True)
                else:
                    server_log(LogTypes.IMPORTANT, f"Client connection at"
                                                  f" {client.get_writer().get_extra_info('peername')} lost")
                    self._onLineUsers.pop(i)
                    client.get_writer().close()

    async def set_difficulty(self):
        while True:
            await asyncio.sleep(60)  # start next loop to send job after 1 min
            result_difficulty = asyncio.run_coroutine_threadsafe(self._set_difficulty(), self._loop)

    async def _set_difficulty(self):
        for i in range(len(self._onLineUsers)):
            key = list(self._onLineUsers[i].keys())[0]
            client = self._onLineUsers[i][key]
            if client.get_subscribed() or client.get_authorized():
                # if True client did not submit share for 4 minute
                if datetime.now() - client.get_last_share_time() > timedelta(minutes=4):
                    client.set_last_share_time(datetime.now())

                    # decrease client difficulty
                    _currentDifficulty = client.get_current_difficulty()
                    if _currentDifficulty > 2:
                        client.set_current_difficulty(_currentDifficulty / 2)

                    is_send_dif = False
                    if not is_send_dif:
                        is_send_dif = await client.send_response_to_client(
                            response_message=set_difficulty(client, client.get_current_difficulty()))
                    if is_send_dif:
                        server_log(LogTypes.TEXT, f"Work difficulty set to "
                                                 f"{LogTypes.IMPORTANT}{client.get_current_difficulty()}{LogTypes.TEXT}"
                                                 f" for client at"
                                                 f" {client.get_writer().get_extra_info('peername')}")
                    else:
                        server_log(LogTypes.IMPORTANT, f"Client connection at"
                                                      f" {client.get_writer().get_extra_info('peername')} lost")
                        self._onLineUsers.pop(i)
                        client.get_writer().close()

    async def bitcoin_block(self):
        while True:
            get_block = asyncio.run_coroutine_threadsafe(self._bitcoin_block(), self._loop)
            await asyncio.sleep(1)
            get_block = get_block.result()
            # sleep for 1 min
            if get_block:
                await asyncio.sleep(60)

    async def _bitcoin_block(self):
        tmp = self._bitcoinCurrentBlockHeight
        self._currentBitcoinNotifyTemplate, self._bitcoinCurrentBlockHeight = calculation.notify_body(
            current_block_height=self._bitcoinCurrentBlockHeight)
        if self._currentBitcoinNotifyTemplate:
            if tmp != self._bitcoinCurrentBlockHeight and tmp: # and tmp means tmp is not 0
                delete_btc_prior_job_data()
                await self.cancel_all_prior_jobs()
            return True
        else:
            server_log(LogTypes.WARNING, f"Getting bitcoin block template failed")
            return False

    async def cancel_all_prior_jobs(self):
        if len(self._onLineUsers) > 0:
            server_log(LogTypes.WARNING, f"A new block was received, canceling all other jobs.")
            for i in range(len(self._onLineUsers)):
                key = list(self._onLineUsers[i].keys())[0]
                client = self._onLineUsers[i][key]
                client.set_has_prior_job(False)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # setWorking directory an scrypt location
    delete_btc_prior_job_data()
    stratumServer = Server(bind_ip='localhost', bind_port=3333)
    stratumServer.run_server()
