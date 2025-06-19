import sys
import os
import json

import matplotlib

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



def main():
    print(parse_args())

if __name__ == "__main__":
    main()