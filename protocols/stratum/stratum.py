import datetime
import random
import globalVariable
from correspondence import calculation
from correspondence.server2client import response, job_response
from protocols.client import Worker
from setting import ServerException, server_log, LogTypes


def subscribe(request_body: dict, client: Worker) -> dict:
    try:
        client.set_request_id()
        request_id = client.get_request_id()
        try:
            if isinstance(request_body['params'], list) or len(request_body['params']) > 0:
                worker_software = request_body['params'][0]
                client.set_worker_soft(worker_software)
                worker_session_id = request_body['params'][1]  # or null
                worker_host = request_body['params'][2]  # or null
                worker_port_host = request_body['params'][3]  # or null
            else:
                return response(request_id=request_id, error_code=20)
        except Exception as er:
            server_log(LogTypes.INFO, f"Stratum subscribe reading params", er)

        notify_ = ''  # session id
        extra_nonce1 = str(("%0.2X" % random.randint(
            0x0, globalVariable.EXTRANONCE_1_RANGE)).zfill(globalVariable.LEN_EXTRANONCE_1 * 2))

        client.set_worker_extra_nonce1(extra_nonce1)
        extra_nonce2_byte_count = globalVariable.LEN_EXTRANONCE_2
        #result = [[["mining.set_difficulty", 8192], ["mining.notify", None]],
        #          extra_nonce1, extra_nonce2_byte_count]
        result = [[["mining.set_difficulty", globalVariable.START_DIFFICULTY]],
                  extra_nonce1, extra_nonce2_byte_count]
        # result = [None, extra_nonce1, extra_nonce2_byte_count]
        client.set_subscribed(True)
        return response(request_id=request_id, error_code=None, result=result)
    except Exception as er:
        server_log(LogTypes.ERROR, f"stratum subscribe", er)
        pass


def authorize(request_body: dict, client: Worker) -> dict:
    try:
        client.set_request_id()
        request_id = client.get_request_id()
        client.set_worker_name(request_body['params'][0])
        client.set_worker_pass(request_body['params'][1])
        client.set_authorized(True)
        return response(request_id=request_id, error_code=None, result=True)
    except Exception as er:
        server_log(LogTypes.ERROR, f"stratum authorize", er)
        return response(request_id=request_body['id'], error_code=24, result=False)


def extranonce_subscribe(client: Worker) -> dict:
    try:
        client.set_request_id()
        request_id = client.get_request_id()
        # if not support
        return response(request_id=request_id, error_code=None, result=False)
        # if support
        # client.set_extranonceSubscribe(True)
        # return response(request_id=request_id, errorCode=None, result=True)
    except Exception as er:
        server_log(LogTypes.ERROR, f"stratum extranonceSubscribe", er)
        return response(request_id=0, error_code=25, result=False)


def set_difficulty(client: Worker, target: float) -> dict:
    try:
        client.set_request_id()
        request_id = client.get_request_id()
        return job_response(request_id=request_id, params=[target], method='mining.set_difficulty', error_code=None)
    except Exception as er:
        server_log(LogTypes.ERROR, f"stratum notify", er)
        return response(request_id=0, error_code=20, result=False)


def notify(client: Worker, notify_body: list) -> dict:
    try:
        client.set_request_id()
        request_id = client.get_request_id()
        return job_response(request_id=request_id, params=notify_body, method='mining.notify', error_code=None)
    except Exception as er:
        server_log(LogTypes.ERROR, f"stratum notify", er)
        return response(request_id=0, error_code=20, result=False)


def submit(request_body: dict, client: Worker) -> dict:
    error_code = 20
    try:
        #client.set_request_id()
        #request_id = client.get_request_id()
        worker_name = request_body['params'][0]
        job_id = request_body['params'][1]
        if job_id != client.get_last_job_id():
            error_code = 21
            raise ServerException(f"received job id {LogTypes.SPECIAL}{job_id}{LogTypes.TEXT} expect "
                                  f"{LogTypes.SPECIAL}{client.get_last_job_id()}")
        extra_nonce1 = client.get_worker_extra_nonce1()
        extra_nonce2 = request_body['params'][2]
        time = request_body['params'][3]
        nonce = request_body['params'][4]

        error_code = calculation.generate_block(job_id=job_id,
                                                extra_nonce1=extra_nonce1, extra_nonce2=extra_nonce2,
                                                time=time, nonce=nonce)
        client.set_last_share_time(datetime.datetime.now())
        #            client.set_current_difficulty(client.get_current_difficulty() * 2)

        if error_code == 0:
            client.set_block_found()
            client.set_founded_share(client.get_current_difficulty())
            server_log(LogTypes.SUCCEED, f"{LogTypes.IMPORTANT}FOUND A BLOCK",
                       f" by client at {client.get_writer().get_extra_info('peername')}")
            # block is submitted
            return response(request_id=request_body['id'], error_code=None, result=True)
        elif error_code == 23:
            if calculation.check_header_hash(job_id, extra_nonce1, extra_nonce2, time, nonce,
                                             client.get_current_difficulty()):
                server_log(LogTypes.INFO, f"{client.get_writer().get_extra_info('peername')}"
                                         f" share {LogTypes.SUCCEED} accepted")
                client.set_founded_share(client.get_current_difficulty())
                # it means client share was accepted for payment
                # block is not submitted by current network difficulty
                return response(request_id=request_body['id'], error_code=None, result=True)
            else:
                # sent share by client is not correct by current client work difficulty
                # network difficulty is different by work difficulty
                server_log(LogTypes.INFO, f"{client.get_writer().get_extra_info('peername')}"
                                         f" share {LogTypes.ERROR} rejected")
                return response(request_id=request_body['id'], error_code=error_code, result=False)
        else:
            return response(request_id=request_body['id'], error_code=error_code, result=False)
    except Exception as er:
        server_log(LogTypes.ERROR, f"Stratum submit", er)
        return response(request_id=request_body['id'], error_code=error_code, result=False)
