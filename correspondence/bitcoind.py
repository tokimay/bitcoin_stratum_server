

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

import json
import urllib.request
from setting import server_log, ServerException, LogTypes
import globalVariable


def get_block_template(worker_id: int, template_request: dict = None) -> dict:
    """
    :return: It returns data needed to construct a block to work on.
    """
    try:
        if template_request is None:
            template_request = {"rules": ["segwit"]}
        data = json.dumps({
            "jsonrpc": "1.0",
            "id": worker_id,
            "method": "getblocktemplate",
            "params": [template_request]
        }).encode()
        request = urllib.request.Request(url=globalVariable.bitcoinCore_rpcUrl, data=data,
                                         headers={"Authorization": b"Basic " + globalVariable.bitcoinCore_authenticate})
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
        if 'result' in response and response['error'] is None:
            return response
        else:
            return {}
    except Exception as er:
        server_log(LogTypes.ERROR, f"BitcoinCore getBlockTemplate", er)
        return {}


def submit_block(worker_id: int, hex_data, dummy: str = 'ignored') -> dict:
    """
    hexData:
    Type: string, required
    the hex-encoded block data to submit

    dummy:
    Type: string, optional, default=ignored
    dummy value, for compatibility with BIP22. This value is ignored.

    :return:
    """
    try:
        data = json.dumps({
            "id": worker_id,
            "method": "submitblock",
            "params": [hex_data]
        }).encode()
        request = urllib.request.Request(url=globalVariable.bitcoinCore_rpcUrl, data=data,
                                         headers={"Authorization": b"Basic " + globalVariable.bitcoinCore_authenticate})
        # Send the RPC and parse response.
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
        if 'result' in response:
            return response
        else:
            raise ServerException(str(response))
    except Exception as er:
        server_log(LogTypes.ERROR, f"BitcoinCore submitBlock", er)
        return {}


def get_difficulty(worker_id: int) -> float:
    """
    :return: Returns the proof-of-work difficulty as a multiple of the minimum difficulty.
    """
    try:
        data = json.dumps({
            "id": worker_id,
            "method": "getdifficulty",
            "params": []
        }).encode()
        request = urllib.request.Request(url=globalVariable.bitcoinCore_rpcUrl, data=data,
                                         headers={"Authorization": b"Basic " + globalVariable.bitcoinCore_authenticate})
        # Send the RPC and parse response.
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
        if 'result' in response and response['error'] is None:
            return response['result']
        else:
            return 0.0
    except Exception as er:
        server_log(LogTypes.ERROR, f"BitcoinCore getdifficulty", er)
        return 0.0

def get_address_info(worker_id: int, address: str = None) -> dict:
    """
    address: string, required
    The bitcoin address for which to get information.

    :return: Return information about the given bitcoin address.
    """
    try:
        if address is None:
            return {}
        data = json.dumps({
            "jsonrpc": "1.0",
            "id": worker_id,
            "method": "getaddressinfo",
            "params": [address]
        }).encode()
        request = urllib.request.Request(url=globalVariable.bitcoinCore_rpcUrl, data=data,
                                         headers={"Authorization": b"Basic " + globalVariable.bitcoinCore_authenticate})
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
        if 'result' in response and response['error'] is None:
            return response
        else:
            return {}
    except Exception as er:
        server_log(LogTypes.ERROR, f"BitcoinCore getBlockTemplate", er)
        return {}