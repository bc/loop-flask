import os
import time
import uuid

from flask import Flask, abort, Response
from loop_helpers.datafunctions import get_files, base_names, compose_CPU, compose_OBS


def active_tokens(datapath: str):
    return base_names(get_files(datapath))

def is_valid_uuid(uuid_to_test: str) -> bool:
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=4)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def validate_token(request: Flask.request_class, datapath: str):
    token = str(request.args.get("token"))
    if is_valid_uuid(token) and token in active_tokens(datapath):
        return token
    else:
        abort(Response(
            "Error: The token `%s` is not active. Go make a new token." % token, status=401))


def gen_new_token(datapath: str):
    new_token = uuid.uuid4()
    targetAbspath = os.path.join(datapath, "%s.txt" % new_token)
    user_file = open(targetAbspath, "a")
    now = time.time()
    L = ["APN:unknown\n", "init:%s\n" % now]
    user_file.writelines(L)
    user_file.write(compose_OBS(-1))
    user_file.write(compose_CPU("INIT", -1))
    user_file.close()
    return new_token