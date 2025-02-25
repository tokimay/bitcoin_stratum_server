

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

def errors(error_code: int) -> list:
    if error_code == 20:
        return [20, 'Other/Unknown.', None]
    elif error_code == 21:
        return [21, 'Job not found (=stale).', None]
    elif error_code == 22:
        return [22, 'Duplicate share.', None]
    elif error_code == 23:
        return [23, 'Low difficulty share.', None]
    elif error_code == 24:
        return [24, 'Unauthorized worker.', None]
    elif error_code == 25:
        return [25, 'Not subscribed.', None]
    # elif errorCode == 26:
    #    return [26, 'bad request.', None]
    # elif errorCode == 27:
    #    return [26, 'Not supported.', None]


def error_response(request_id: int, error_code: int, result: None or bool = None) -> dict:
    return {"id": request_id, "result": result, "error": errors(error_code)}


def response(request_id: int, error_code: int or None, result=None) -> dict:
    if error_code is None:
        return {"id": request_id, "result": result, "error": error_code}
    else:
        return error_response(request_id, error_code, result)


def job_response(request_id: int, params: list, method: str, error_code: int or None) -> dict:
    if error_code is None:
        return {"id": request_id, "method": method, "params": params}
    else:
        return error_response(request_id, error_code)


def login_response(result: str or None, request_id: int or str, error_code: int or None,
                   jsonrpc_version: str = "2.0", method: str = "login"):
    if error_code is None:
        return {"id": request_id, "jsonrpc": jsonrpc_version, "method": method, "result": result, "error": error_code}
    else:
        return error_response(1, error_code)
