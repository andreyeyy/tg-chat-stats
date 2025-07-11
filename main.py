import sys
import os
import json
import datetime
import shutil

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
    USAGE = "py main.py"

    if not os.path.exists(DEFAULT_INPUT_DIRECTORY):
        os.makedirs(DEFAULT_INPUT_DIRECTORY)
    
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


def unix_to_string(unix_date):
    return datetime.datetime.fromtimestamp(unix_date).strftime("%B %d, %Y")

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

    statistics['start_date'] = unix_to_string(start_time)
    statistics['end_date'] = unix_to_string(end_time)

    total_seconds = end_time - start_time
    total_days = total_seconds / 86400

    statistics['total_days'] = total_days

    statistics['avg_messages_per_day'] = len(messages) / total_days

    common_words = {}
    common_long_words = {}

    for msg in messages:
        if not 'text' in msg or not isinstance(msg['text'], str):
            continue
        for word in msg['text'].split():
            word = word.lower()
            if (len(word) > 3):
                if not word in common_long_words:
                    common_long_words[word] = 1
                else:
                    common_long_words[word] += 1
            
            if not word in common_words:
                common_words[word] = 1
            else:
                common_words[word] += 1

    statistics['total_different_words'] = len(common_words)

    top_words = dict(sorted(common_words.items(), key=lambda item: item[1], reverse=True)[:20])
    top_long_words = dict(sorted(common_long_words.items(), key=lambda item: item[1], reverse=True)[:20])
    statistics['top_words'] = top_words
    statistics['top_long_words'] = top_long_words


    last_message_day = int(messages[0]['date_unixtime']) // 86400
    current_streak = 1
    longest_streak = 0
    last_date = 0

    for msg in messages:
        day = int(msg['date_unixtime']) // 86400

        if day == last_message_day:
            continue
        elif day == last_message_day + 1:
            current_streak += 1
        else:
            current_streak = 1

        if current_streak > longest_streak:
            longest_streak = current_streak
            last_date = day

        last_message_day = day

    statistics['longest_streak'] = longest_streak
    statistics['longest_streak.first_date'] = unix_to_string((last_date - longest_streak + 1) * 86400)
    statistics['longest_streak.last_date'] = unix_to_string(last_date * 86400)


    message_time_distribution = [0] * 24 # an array with 24 zeros (24 hours in a day)

    for msg in messages:
        date = msg['date']
        hour = int(date.split('T', 1)[1][:2]) # this turns "2023-01-31T09:05:28" into int 9
        message_time_distribution[hour] += 1

    statistics['message_time_distribution_values'] = message_time_distribution
    hours = list(range(24))
    for i, value in enumerate(hours):
        hour_string = '0'
        if value > 9:
            hour_string = ''
        hour_string += str(value)
        hours[i] = hour_string + ':00'


    statistics['message_time_distribution_hours'] = hours

    activity_splits = 20

    statistics['activity_over_time'] = [0] * activity_splits
    statistics['activity_over_time_dates'] = []
    

    split_size_seconds = total_seconds / activity_splits

    statistics['activity_over_time_period_size'] = int(split_size_seconds / 86400)

    print(f"split_size_seconds: {split_size_seconds}")

    prev_slot = 0
    for msg in messages:
        unix_date = int(msg['date_unixtime']) 
        curr_slot = int((unix_date - start_time) / split_size_seconds)
        
        if curr_slot != prev_slot:
            prev_slot = curr_slot

            date_string = unix_to_string(unix_date - (split_size_seconds / 2))
            statistics['activity_over_time_dates'].append(date_string)

        if curr_slot >= activity_splits:
            break # probably not the best way to do it but whatever

        statistics['activity_over_time'][curr_slot] += 1

    print(statistics)
    return statistics


def sanitize_statistics(stats):
    result = {}

    #list of values to be copied to result from stats
    to_copy = ['user1', 'user2', 'total_messages', 'user1.total_messages', 'user2.total_messages', 'start_date', 'end_date', 'total_different_words', 'longest_streak', 'longest_streak.first_date', 'longest_streak.last_date'] 

    for key in to_copy:
        result[key] = str(stats[key])

    #list of numbers to be rounded and copied to result from stats
    to_round = ['user1.percent_messages', 'user2.percent_messages']

    for key in to_round:
        result[key] = "{:.2f}".format(stats[key])

    #list of numbers to be fully rounded to an integer and copied to result from stats
    to_round = ['total_days', 'avg_messages_per_day', 'activity_over_time_period_size']

    for key in to_round:
        result[key] = str(int(stats[key]))

    #list of dictionaries to be concatenated into a string (to then be used to build a chart)
    to_concatenate = ['top_words', 'top_long_words']

    for key in to_concatenate:
        result[key] = ""
        result[key+'_count'] = ""

        for i, word in enumerate(stats[key]):
            comma = ", "
            if i == len(stats[key]) - 1:
                comma = ""
            result[key] += "'" + word + "'" + comma
            result[key+'_count'] += str(stats[key][word]) + comma


    #list of arrays to be concatenated into a string (to then be used to build a chart)
    to_concatenate = ['message_time_distribution_values', 'message_time_distribution_hours', 'activity_over_time', 'activity_over_time_dates']

    for key in to_concatenate:
        result[key] = ""

        for i, value in enumerate(stats[key]):
            comma = ", "
            if i == len(stats[key]) - 1:
                comma = ""
            result[key] += "'" + str(value) + "'" + comma

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

    generate_result(statistics)

    print("Done! Check out result/index.html")

if __name__ == "__main__":
    main()