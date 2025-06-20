import sys
import os
import json
import datetime
import shutil

import matplotlib

RESULT_FOLDER = "result"

def clean_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return
    
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def copy_all(src, dst):

    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)

        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)

def parse_args():
    DEFAULT_INPUT_DIRECTORY = "input_files"
    USAGE = ""

    if not os.path.exists(DEFAULT_INPUT_DIRECTORY):
        os.makedirs(DEFAULT_INPUT_DIRECTORY)

    if os.name == 'nt':
        USAGE = "Usage: venv\\Scripts\\python main.py <path_to_json>"
    elif os.name == 'posix':
        USAGE = "Usage: venv/bin/python main.py <path_to_json>"
    else:
        print("Unknown OS")
        sys.exit(1)
    
    args = sys.argv

    if len(args) > 2:
        print(USAGE)
        sys.exit(1)
    
    json_path = ""

    if len(args) == 1:
        input_files = [f for f in os.listdir(DEFAULT_INPUT_DIRECTORY) if f.endswith('.json')]
        if len(input_files) != 1:
            print(f"There has to be exactly 1 json file in {DEFAULT_INPUT_DIRECTORY}, but there are {len(input_files)}")
            print(USAGE)
            sys.exit(1)
        
        json_path = os.path.join(DEFAULT_INPUT_DIRECTORY, input_files[0])

    else:
        json_path = args[1]

    if not os.path.isfile(json_path):
        print(f"The provided path is invalid or not a file: '{json_path}'")
        print(USAGE)
        sys.exit(1)
    
    if not json_path.endswith('.json'):
        print(f"The provided file is not a JSON file: '{json_path}'")
        print(USAGE)
        sys.exit(1)
    
    return json_path




def collect_statistics(data):
    statistics = {}
    messages = data['messages']
    statistics['total_messages'] = len(messages)
    statistics['user2'] = data['name']
    for msg in messages:
        if 'from' in msg and msg['from'] != statistics['user2']:
            statistics['user1'] = msg['from']
    user1_messages = [msg for msg in messages if 'from' in msg and msg['from'] == statistics['user1']]
    user2_messages = [msg for msg in messages if 'from' in msg and msg['from'] == statistics['user2']]
    statistics['user1.total_messages'] = len(user1_messages)
    statistics['user2.total_messages'] = len(user2_messages)

    statistics['user1.percent_messages'] = len(user1_messages) / len(messages)
    statistics['user2.percent_messages'] = len(user2_messages) / len(messages)

    start_time = int(messages[0]['date_unixtime'])
    end_time = int(messages[len(messages)-1]['date_unixtime'])
    statistics['start_date_unix'] = start_time
    statistics['end_date_unix'] = end_time

    statistics['start_date'] = datetime.datetime.fromtimestamp(start_time).strftime("%B %d, %Y")
    statistics['end_date'] = datetime.datetime.fromtimestamp(end_time).strftime("%B %d, %Y")

    total_seconds = end_time - start_time
    total_days = total_seconds / 86400

    statistics['total_days'] = total_days

    return statistics


def sanitize_statistics(stats):
    result = {}

    #list of values to be copied to result from stats
    to_copy = ['user1', 'user2', 'total_messages', 'user1.total_messages', 'user2.total_messages', 'start_date', 'end_date'] 

    for key in to_copy:
        result[key] = str(stats[key])

    #list of numbers to be rounded and copied to result from stats
    to_round = ['user1.percent_messages', 'user2.percent_messages']

    for key in to_round:
        result[key] = "{:.2f}".format(stats[key])

    #list of numbers to be fully rounded to an integer and copied to result from stats
    to_round = ['total_days']

    for key in to_round:
        result[key] = str(int(stats[key]))

    return result


def generate_result(stats):
    clean_folder(RESULT_FOLDER)
    copy_all("template", RESULT_FOLDER)

    html_path = os.path.join(RESULT_FOLDER, "index.html")

    with open(html_path, "r", encoding="utf-8") as file:
        content = file.read()

    sanitized_stats = sanitize_statistics(stats)

    for key in sanitized_stats:
        content = content.replace("{" + key + "}", sanitized_stats[key])

    with open(html_path, "w", encoding="utf-8") as file:
        file.write(content)


def main():
    json_path = parse_args()

    with open(json_path, 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    statistics = collect_statistics(data)
    
    print(statistics)

    generate_result(statistics)

if __name__ == "__main__":
    main()