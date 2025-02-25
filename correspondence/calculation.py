

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

import binascii
import hashlib
import json
import random
from correspondence import bitcoind
import globalVariable
from setting import server_log, LogTypes, ServerException


def len_var(value: int) -> str:
    if value < 253:
        return value.to_bytes(1, byteorder='little').hex()
    if value <= 65535:
        return "fd" + value.to_bytes(2, byteorder='little').hex()
    if value <= 4294967295:
        return "fe" + value.to_bytes(4, byteorder='little').hex()
    return "ff" + value.to_bytes(8, byteorder='little').hex()

def re_order(hash_string: str) -> str:
    return bytearray.fromhex(hash_string)[::-1].hex()

def re_order_block_hash(block_hash: str) -> str:
    result = ''
    for i in range(0, len(block_hash), 8):
        result += re_order(block_hash[i:i + 8])
    return result

def sha256(data: str) -> str:
    return hashlib.sha256(bytearray.fromhex(data)).hexdigest()

def double_sha256(data: str) -> str:
        return sha256(sha256(data))

def double_sha256_reverse(data: str) -> str:
    return bytearray.fromhex(sha256(sha256(data)))[::-1].hex().zfill(64)

def header_hash(header: str) -> str:
    solution_hash = hashlib.sha256(
        hashlib.sha256(bytearray.fromhex(header)).digest()
    ).digest()[::-1].hex()
    return solution_hash


def merkle_branch(branch_list: list, helper: list = None, loop_counter: int = 0) -> list:
    if helper is None: # first loop
        helper = []
        branch_list.insert(0, None) # as coinbase trx id
    if len(branch_list) == 1:
        return helper
    else:
        # make list len even if its is odd
        if len(branch_list) % 2 == 1:
            branch_list.append(branch_list[-1])
        merkle_branch_temp = []
        for i in range(0, len(branch_list), 2):
            if branch_list[i] is None:
                helper.append(re_order(branch_list[i + 1]))
                merkle_branch_temp.append(None)
            else:
                merkle_branch_temp.append(merkle_hash(branch_list[i], branch_list[i + 1]))
        return merkle_branch(merkle_branch_temp, helper, loop_counter + 1)

def merkle_root(branch_list: list) -> str:
    if len(branch_list) == 1:
        return branch_list[0]
    else:
        # make list len even if it is odd
        if len(branch_list) % 2 == 1:
            branch_list.append(branch_list[-1])
        merkle_root_temp = []
        for i in range(0, len(branch_list), 2):
            merkle_root_temp.append(merkle_hash(branch_list[i], (branch_list[i + 1])))
        return merkle_root(merkle_root_temp)

def merkle_hash(trx1: str, trx2) -> str:
    return double_sha256_reverse(re_order(trx1) + re_order(trx2))

def coinbase(
        height: int,
        coinbase_amount: int,
        script_pubkey_witness: str,
        script_pubkey: str) -> tuple[str, str]:
    try:
        version = '01000000'
        height_little = (height.to_bytes((height.bit_length() + 7) // 8, 'little')).hex()
        len_height_little = str(len_var(len(height_little) // 2))
        ascii_message = '746f6b696d617940676d61696c2e636f6d'
        len_ascii_message = str(
            len_var((len(ascii_message) // 2) + globalVariable.LEN_EXTRANONCE_1 + globalVariable.LEN_EXTRANONCE_2))

        script_sig = len_height_little + height_little + len_ascii_message + ascii_message
        len_script_sig = str(
            len_var((len(script_sig) // 2) + globalVariable.LEN_EXTRANONCE_1 + globalVariable.LEN_EXTRANONCE_2))
        coin_base1 = (version + '010000000000000000000000000000000000000000000000000000000000000000ffffffff' +
                len_script_sig + script_sig)  # + extra nonce
        coinbase_amount = (coinbase_amount.to_bytes(8, byteorder='little')).hex()
        script_pubkey_size = len_var(len(script_pubkey) // 2)
        script_pubkey_witness_size = len_var(len(script_pubkey_witness) // 2)
        coin_base2 = ('ffffffff02' + coinbase_amount + script_pubkey_size + script_pubkey + '0000000000000000' +
                      script_pubkey_witness_size + script_pubkey_witness + '00000000')
        return coin_base1, coin_base2
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation coinbase", er)

def notify_body(current_block_height: int) -> tuple[list, int]:
    coinbase1 = ''
    coinbase2 = ''
    merkle = ''
    version = ''
    bits = ''
    time = ''
    previous_block_hash = ''
    params = []
    forgot_prior_job = False
    block_height = 0
    job = None
    try:
        block = bitcoind.get_block_template(worker_id=random.randint(0x0, 0xf))
        if not block:
            raise ServerException('getting block template failed')

        previous_block_hash_job = re_order(block['result']['previousblockhash'])
        # https://stackoverflow.com/questions/66412968/hash-of-previous-block-from-stratum-protocol
        previous_block_hash = re_order_block_hash(block_hash=previous_block_hash_job)

        coinbase1, coinbase2 = coinbase(
            height=block['result']['height'],
            coinbase_amount=block['result']['coinbasevalue'],
            script_pubkey_witness=block['result']['default_witness_commitment'],
            script_pubkey=globalVariable.SCRIPT_PUBKEY)

        merkle_trx = []
        if len(block['result']['transactions']) > 0:
            for trx in block['result']['transactions']:
                merkle_trx.append(trx['txid'])

        merkle = merkle_branch(merkle_trx)

        version_job = block['result']['version']
        version = (hex(version_job)[2:]).zfill(8)

        time_job = block['result']['curtime']
        time = (hex(time_job)[2:]).zfill(8)

        bits = (block['result']['bits']).zfill(8)

        block_height = block['result']['height']

        job_id = (time.zfill(10)) + ((hex(block_height)[2:]).zfill(10))

        # create job
        job = {
            "job_id": job_id, "previous_block_hash": previous_block_hash_job,
            "coinbase1": coinbase1, "coinbase2": coinbase2,
            "merkle_branch": merkle, "version": version_job, "bits": bits, "time": time_job, "block": block}

    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation notifyBody", er)

    try:
        # save Job to disk
        json.dump(job, open(f"activeJobs/BTC_{job_id}.json", 'w'))
        if block_height > current_block_height:
            forgot_prior_job = True
        params = [job_id, previous_block_hash, coinbase1, coinbase2,
                  merkle, version, bits, time, forgot_prior_job]
    except Exception as er:
        server_log(LogTypes.WARNING, f"Calculation notifyBody",
                   f"{er}{LogTypes.WARNING} skipping current job")

    return params, block_height

def get_block_row(job_id: str,  extra_nonce1: str, extra_nonce2: str, time: str, nonce: str
                  ) -> tuple[str, str, float]:
    try:
        if len(extra_nonce1) != globalVariable.LEN_EXTRANONCE_1 * 2:  # 4 bytes * 2 = 8 hexString
            print('extra_nonce1', extra_nonce1, len(extra_nonce1))
            raise ServerException('received extraNonce1 len')

        if len(extra_nonce2) != globalVariable.LEN_EXTRANONCE_2 * 2:  # 4 bytes * 2 = 8 hexString
            raise ServerException('received extraNonce2 len')

        if len(time) != 8:  # 4 bytes = 8 hexString
            raise ServerException('received time len')

        if len(nonce) != 8:  # 4 bytes = 8 hexString
            raise ServerException('received nonce len')

        try:
            job = json.load(open(f"activeJobs/BTC_{job_id}.json"))
        except Exception as er:
            raise ServerException(f"{LogTypes.TEXT} can not open job {LogTypes.IMPORTANT}{job_id}{LogTypes.TEXT}. {er}")
        ''' block header '''
        # 4 bytes version in little-endian
        version = job['version']
        version = re_order(hex(version)[2:])

        # 32 bytes previous block hash in natural byte order
        previous_block_hash = job['previous_block_hash']

        transactions_raw = ''
        if len(job['block']['result']['transactions']) > 0:
            for trx in job['block']['result']['transactions']:
                transactions_raw = transactions_raw + trx['data']

        coin_base = job['coinbase1'] + extra_nonce1 + extra_nonce2 + job['coinbase2']

        # 32 bytes merkle root in natural byte order
        merkle = job['merkle_branch']

        cb_id = hashlib.sha256(hashlib.sha256(binascii.unhexlify(coin_base)).digest()).digest()
        cb_id = cb_id.hex()

        root = cb_id
        for tx_id in merkle:
            root = double_sha256(root + tx_id)

        # 4 bytes time in little-endian
        time = re_order(time)

        # 4 bytes bits in little-endian
        bits = job['bits']
        bits = (re_order(bits)).zfill(8)

        # 4 bytes nonce in little-endian
        nonce = re_order(nonce.zfill(8))

        # coinbase transaction ID as first transaction
        merkle.insert(0, cb_id)
        len_transactions = len_var(len(merkle))
        transactions_raw = coin_base + transactions_raw

        target = bits_to_target(bits)

        block_header = version + previous_block_hash + root + time + bits + nonce
        block_raw = block_header + len_transactions + transactions_raw

        return block_raw, block_header, target
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation getBlockRow", er)
        return '', '', 0.0

def generate_block(job_id: str, extra_nonce1: str, extra_nonce2: str, time: str, nonce: str) -> int:
    try:
        block_raw, block_header, target = get_block_row(job_id, extra_nonce1, extra_nonce2, time, nonce)
        submit_result = bitcoind.submit_block(worker_id=random.randint(0x0, 0xf), hex_data=block_raw)
        if submit_result:
            server_log(LogTypes.WARNING, f"Submitting the block to the blockchain returns the result",
                       F"{submit_result['result']}")
            if submit_result['result'] is None:
                return 0  # no error
            elif submit_result['result'] == 'high-hash':
                return 23  # Low difficulty share
        else:
            return 20  # Other/Unknown
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation generateBlock", er)
        return 20  # Other/Unknown

def check_header_hash(job_id: str, extra_nonce1: str, extra_nonce2: str, time: str, nonce: str,
                      client_difficulty: float) -> bool:
    result = False
    try:
        block_raw, block_header, target = get_block_row(job_id, extra_nonce1, extra_nonce2, time, nonce)
        h_hash = header_hash(block_header)
        server_log(LogTypes.WARNING, f"Worker   solution", F"{h_hash}")
        solution_difficulty = difficulty_to_target(client_difficulty)
        server_log(LogTypes.WARNING, f"Worker difficulty", F"{solution_difficulty}")
        result = int(h_hash, 16) < int(solution_difficulty, 16)
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation checkHeaderHash", er)
    finally:
        return result

def difficulty_to_target(difficulty: float) -> str:
    target = ''
    try:
        base_difficulty = 0x00000000ffff0000000000000000000000000000000000000000000000000000
        target = hex(int(base_difficulty / difficulty))[2:].zfill(64)
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation targetToDifficulty", er)
    finally:
        return target

def bits_to_target(bits: str) -> float:
    target = 0.0
    try:
        if not bits:
            return 0
        bits = int(bits, 16)
        bits_bytes = bits.to_bytes(4, 'big')
        exponent = bits_bytes[0]
        coefficient = int.from_bytes(b'\x00' + bits_bytes[1:], 'big')
        target = coefficient * 256 ** (exponent - 3)
        # return hex(target)[2:].zfill(64)
    except Exception as er:
        server_log(LogTypes.ERROR, f"Calculation bitsToTarget", er)
    finally:
        return target
