import json
from dataclasses import dataclass

import requests
from dataclasses_json import dataclass_json
from requests import Response

from loop_helpers.datafunctions import Observation
from flask import abort

def get_telegram_token(loop_token: str):
    # TODO make non-hardcoded. will only ping brian via bot.
    return "911638276:AAEe7XkH3B_YNg1mpfRZsjt0jm7QX3nZaCg"
import os

def get_telegram_chat_id(loop_token):
    # TODO make non-hardcoded. will only ping brian via bot.
    return 97634578


def push_telegram_notification(loop_token, message):
    telegram_token = get_telegram_token(loop_token)
    telegram_chat_id = get_telegram_chat_id(loop_token)
    url = "https://api.telegram.org/bot%s/sendMessage" % telegram_token
    payload = 'chat_id=%s&text=%s' % (telegram_chat_id, message)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.json()["ok"]:
            return True
        else:
            return False
    except:
        return False

@dataclass_json
@dataclass
class DiscordID:
    # phone address is a phone number with the country code in front e.g. 13237775555. no + or - or ()
    value: int

@dataclass_json
@dataclass
class Predicate:
    token: str
    feature: str
    trigger_on_true: str
    value: float
    # true if the trigger is true with a given observation, for the matching observation type
    def evaluate(self, o: Observation):
        if o.feature != self.feature:
            raise Exception(
                "wrong observation type %s given to predicate that was expecting a %s" % (o.feature, self.feature))
        else:
            return trigger_on_true_evaluation(self.trigger_on_true, current_observation=o.value,threshold=self.value)

def get_predicates(token, DATAFOLDERPATH):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    if not os.path.isfile(target_filepath):
        return []
    with open(target_filepath, 'r') as f:
        firstline = f.readline()
        preds = json_to_list_of_predicates(firstline)  # [Person(name='lidatong')]
    return preds

def list_of_predicate_to_json(L):
    return Predicate.schema().dumps(L, many=True)


def json_to_list_of_predicates(firstline):
    return Predicate.schema().loads(firstline, many=True)



def parse_predicate(token, ss):
    if len(ss) < 1:
        abort(Response(
            "Error: input was empty.",
            status=401))
    input_string = ss.replace("=", "").replace(" ", "")


    if ">" in input_string:
        eqn_sides = input_string.split(">")
        eq_type = ">"
    elif "<" in input_string:
        eqn_sides = input_string.split("<")
        eq_type = "<"
    else:
        abort(Response(
            "Error: input should have a > or a < in the statement yours had neither: (%s)." % input_string,
            status=401))

    if len(eqn_sides) != 2:
        abort(Response(
            "Error: input didn't have an element on both sides of the input > or < (%s)." % input_string,
            status=401))
    if eq_type not in accepted_comparator_operators():
        raise Exception("input comparator operator is not valid. input was: %s, should be one of these:" % (
            eq_type, ",".join(accepted_comparator_operators())))

    if eqn_sides[0] == "predicate_form_obs":
        return Predicate(token, "obs", eq_type, eqn_sides[1])
    elif eqn_sides[0] == "predicate_form_cpu":
        return Predicate(token, "cpu", eq_type, eqn_sides[1])
    else:
        abort(Response(
            "Error: input was not predicate_form_obs or predicate_form_cpu:" % input_string,
            status=401))



def accepted_comparator_operators():
    return [">=","<=","==","!=",">","<"]

def trigger_on_true_evaluation(trigger_on_true, current_observation, threshold):
    if trigger_on_true == ">":
        return current_observation > threshold
    elif trigger_on_true == ">=":
        return current_observation >= threshold
    elif trigger_on_true == "<":
        return current_observation < threshold
    elif trigger_on_true == "<=":
        return current_observation <= threshold
    elif trigger_on_true == "==":
        return current_observation == threshold
    elif trigger_on_true == "!=":
        return current_observation != threshold
    else:
        raise Exception("input trigger was invalid. Input was %s; accepted ones are: %s" % (trigger_on_true,",".join(accepted_comparator_operators())))


def predicate_is_triggered(token, o: Observation, DATAFOLDERPATH):
    predicates = get_predicates(token, DATAFOLDERPATH)
    if len(predicates) == 0:
        # if there are no predicates, they can't be triggered
        return False
    relevant_predicates = [p for p in predicates if p.feature == o.feature]
    predicate_matches = [p.evaluate(o) for p in relevant_predicates]
    print(predicate_matches)
    result = any(predicate_matches)
    if result == True:
        clear_all_predicates(token, DATAFOLDERPATH)
    return result

def clear_all_predicates(token, DATAFOLDERPATH):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    if os.path.isfile(target_filepath):
        os.remove(target_filepath)
    print("rm predicates for token %s" % token)

def clear_contactinfo(token,DATAFOLDERPATH):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_contactinfo.txt" % token)
    if os.path.isfile(target_filepath):
        os.remove(target_filepath)
    print("rm contactinfo for token %s" % token)

def get_contactinfo(token, DATAFOLDERPATH):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_contactinfo.txt" % token)
    if not os.path.isfile(target_filepath):
        # a cell equal to 0 means they don't have one
        return DiscordID(0)
    with open(target_filepath, 'r') as f:
        firstline: str = f.readline()
        contactinfo: DiscordID = DiscordID.from_json(firstline)
        return contactinfo