import os
import time
from dataclasses import dataclass
from os import listdir
from os.path import isfile, join

from dataclasses_json import dataclass_json
from flask import Response
from flask import abort


@dataclass_json
@dataclass
class Observation:
    feature: str
    value: float
    unixtime: float = None


def get_files(mypath):
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return onlyfiles


def base_names(file_list):
    return [os.path.splitext(f)[0] for f in file_list]


def get_last_observation_line(filepath, valType="OBS"):
    lines = get_all_logged_lines(filepath, valType=valType)
    return lines[-1]

def get_all_logged_lines(filepath, valType="OBS"):
    with open(filepath, "rb") as f:
        observations = [x.decode("utf-8") for x in f.readlines()]
        obs_vals = [x for x in observations if x.startswith(valType)]
        list_of_pieces = [y.rstrip().split(",") for y in obs_vals]
        return list_of_pieces

def compose_CPU(name, value):
    return "CPU,%s,%s,%s\n" % (time.time(), name, value)


def compose_OBS(obs):
    return "OBS,%s,%s\n" % (time.time(), obs)


def is_normalized(float_number):
    return 0.0 <= float_number <= 1.0


def try_parse_object_as(inputObject, parseFunction):
    try:
        obs = parseFunction(inputObject)
        return obs
    except ValueError:
        abort(Response(
            "Error: Object is not parseable as a %s." % parseFunction.__name__,
            status=401))