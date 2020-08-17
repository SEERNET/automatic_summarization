#!/usr/bin/env python3
# Copyright 2017-2020  SeerNet Technologies, LLC

"""
usage: python3 deepaffects_summary_api.py <infolder> <outfolder>
<infolder> : folder path of the transcripts to be processed
<outfolder>: folder path of the summary output

NOTE:
This script requires python3
Make sure requests module is installed. You can install it with the command: "pip3 install requests"

Replace the APIKEY with your own apikey
"""

import json
import os
import sys
import time
import getopt

import requests

APIKEY = "YOUR_API_KEY"


def read_text_to_segments(file_path):
    """
    This method reads the transcript saved in DeepAffects transcript format and returns
    list of segments objects with keys: text, speakerId
    text      -> segment text
    speakerId -> speaker id corresponding to the segment

    data format of the input file
    [speaker_id : start_time - end_time : text]
    eg:
    speaker_0 : 00:00:02.3 - 00:00:08.3 : This call is being recorded for quality training purposes.
    speaker_1 : 00:00:08.4 - 00:00:10.5 : Hello, This is Ryan.
    OR
    [speaker_id : text]
    eg:
    speaker_0 : This call is being recorded for quality training purposes.
    speaker_1 : Hello, This is Ryan.
    """

    def get_speaker_id(label):
        # len("speaker_") = 8
        label = label.strip()
        return label[label.startswith("speaker_") and 8:]

    output_segments = []
    with open(file_path) as f:
        for line in f:
            text = ""
            line = line.strip()
            if not line:
                continue
            line = line.split(": ", 1)
            speaker_id = get_speaker_id(line[0])
            line = line[1].rsplit(": ", 1)
            if len(line) >= 1:
                text = line[-1].strip()
            output_segments.append({
                "speakerId": speaker_id,
                "text": text
            })
    return output_segments


def read_json_to_segments(file_path):
    """
    This method reads the DeepAffects interaction analytics json output and returns
    list of segments objects with keys: text, speakerId
    text      -> segment text
    speakerId -> speaker id corresponding to the segment

    data format of the input file.
    {'segments': [
    {'speaker_id': '0', 'text': 'This call is being recorded for quality training purposes.'},
    {'speaker_id': '1', 'text': 'Hello, This is Ryan.'}
    ]}
    """
    with open(file_path) as f:
        output_segments = json.load(f)["segments"]
    for x in output_segments:
        x["speakerId"] = x["speaker_id"]
    return output_segments


def send_request(file_path, model="iamus"):
    """
    This methods reads the data from transcript file and post async summary api request.
    Returns the unique request id generated from the api.

    For different input format, generate the segments in the following format
    [{"speakerId": "0", "text": "your text"}, {"speakerId": "1", "text": "your text"}]
    """
    try:
        url = "https://proxy.api.deepaffects.com/text/generic/api/v1/async/summary"

        querystring = {"apikey": APIKEY}
        if os.path.splitext(file_path)[1] == ".json":
            segments = read_json_to_segments(file_path)
        else:
            segments = read_text_to_segments(file_path)
        payload = {"summaryType": "abstractive", "summaryData": segments, "model": model}

        headers = {'Content-Type': "application/json"}
        response = requests.post(url, json=payload, headers=headers, params=querystring)
        response = response.json()
        request_id = response.get("request_id", None)
        return request_id
    except Exception as ex:
        print(ex)
    return None


def get_response(request_id):
    """
    This method takes request_id as parameter and retrieves its corresponding response using
    DeepAffects Status API. If result is still 'In Progress', it sleeps for 10 sec and then return.
    In case of any error, returns response as FAILED
    """
    url = "https://proxy.api.deepaffects.com/transaction/generic/api/v1/async/status"

    querystring = {"apikey": APIKEY,
                   "request_id": request_id}

    payload = ""
    headers = {'cache-control': "no-cache"}
    response = requests.get(url, data=payload, headers=headers, params=querystring)
    try:
        response = response.json()
        status = response['status'].lower().strip()
        if "progress" in status:
            time.sleep(10)
            summary = "IN PROGRESS"
        elif "completed" in status:
            summary = response['response']['response']
        else:
            print("request_id: {} status: {}".format(request_id, status))
            summary = "FAILED"
    except Exception as ex:
        print(ex)
        summary = "FAILED"
    return summary


def process_summary_request(file_name, out_folder, model):
    """
    This method takes path of transcript file to be processed and then sends the request and save the response.
    Response are saved in the out_folder.
    """
    print("Processing file : {}".format(file_name))
    request_id = send_request(file_name, model)
    completed = True

    while completed:
        response = get_response(request_id)
        if isinstance(response, dict):
            out_filename = os.path.join(out_folder, os.path.basename(file_name) + ".output.json")
            with open(out_filename, 'w') as f:
                json.dump({"response": response}, f)
            print("Completed summary for  file :: {}".format(file_name))
            print("Output written to {}".format(out_filename))
            completed = False
        elif response == "FAILED":
            completed = False
        else:
            print("Summarization is in progress")


def usage():
    print('Usage: ' + sys.argv[0] + ' [options]')
    print('Options:')
    print('-i --input_file_path=    Must be valid txt or json file path of the transcript')
    print('-o --output_folder=      Must be valid directory where the summary output json would be written')
    print('-m --model=              [default: iamus]. Must be iamus or cassandra')


if __name__ == '__main__':
    if APIKEY in "YOUR_API_KEY":
        print("Please update your valid api key")
        exit(0)

    input_file_path = None
    output_folder = None
    model = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:", ["input_file_path=", "output_folder="])
    except getopt.GetoptError as err:
        if len(sys.argv) > 1:
            if not sys.argv[1] in ["-h", "--help"]:
                print('%s: %s' % (sys.argv[0], err))
                print('%s: Try --help or -h for usage details.' % (sys.argv[0]))
            else:
                usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-i", "--input_file_path"):
            input_file_path = arg
        elif opt in ("-o", "--output_folder"):
            output_folder = arg
        elif opt in ("-m", "--model"):
            model = arg

    if input_file_path is None or len(input_file_path) <= 0 or output_folder is None or len(output_folder) <= 0:
        usage()
        sys.exit(2)
    elif not (input_file_path.endswith(".json") or input_file_path.endswith(".txt")):
        print("Invalid input file. Should be either json or txt file")
        sys.exit(2)
    elif model not in ["cassandra", "iamus"]:
        print("Invalid model param. Should be either cassandra or iamus")
        sys.exit(2)
    elif not os.path.isdir(output_folder):
        print("Invalid output folder. Output folder does not exists")
        sys.exit(2)

    process_summary_request(input_file_path, output_folder)
