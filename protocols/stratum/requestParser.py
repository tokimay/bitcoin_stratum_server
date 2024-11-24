from correspondence import calculation
from correspondence.server2client import response
import protocols.stratum.stratum
from protocols.client import Worker
from setting import server_log, LogTypes


def pars_method(request_body: dict, client: Worker) -> dict:
    if request_body['method'] == 'mining.subscribe':
        return protocols.stratum.stratum.subscribe(request_body, client)

    elif request_body['method'] == 'mining.authorize':
        return protocols.stratum.stratum.authorize(request_body, client)

    elif request_body['method'] == 'mining.submit':
        server_log(LogTypes.IMPORTANT, f"client at {client.get_writer().get_extra_info('peername')}"
                                      f" send solution in job {LogTypes.SPECIAL}{request_body['params'][1]}")
        return protocols.stratum.stratum.submit(request_body, client)

    elif request_body['method'] == 'mining.notify':
        current_bitcoin_notify_template, bitcoin_current_block_height = calculation.notify_body(current_block_height=0)
        if bitcoin_current_block_height:
            return protocols.stratum.stratum.notify(client, notify_body=current_bitcoin_notify_template)
        else:
            return {}

    elif request_body['method'] == 'mining.set_difficulty':
        return {}
    elif request_body['method'] == 'mining.suggest_difficulty':
        return {}
    elif request_body['method'] == 'mining.suggest_target':
        return {}
    elif request_body['method'] == 'mining.get_transactions':
        return {}
    elif request_body['method'] == 'mining.set_extranonce':
        return {}
    elif request_body['method'] == 'mining.configure':
        return {}
    elif request_body['method'] == 'mining.extranonce.subscribe':
        return protocols.stratum.stratum.extranonce_subscribe(client)

    elif request_body['method'] == 'getblocktemplate':
        return {}
    elif request_body['method'] == 'login':
        return protocols.stratum.stratum.login(request_body, client)

    else:
        response(request_id=request_body['id'], error_code=20)
