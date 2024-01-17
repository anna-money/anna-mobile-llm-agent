import os
import re
import base64
import xmltodict

from time import sleep
from subprocess import Popen, PIPE, check_output

LAYOUT_KEEP_KEYS = ['index', 'text', 'resource-id', 'class', 'bounds']
LAYOUT_PARAM_KEYS = [
    'checkable', 'checked', 'clickable',
    'enabled', 'focusable', 'focused', 'scrollable',
    'long-clickable', 'password', 'selected'
]

UI_AUTO_DUMP_PATH = '/sdcard/window_dump.xml'
TIMEOUT_TO_WAIT_FOR_SCREEN_TO_UPDATE_SECONDS = 2

# The sequence of keycodes to ensure that all text is deleted
BACKSPACE_KEYCODE_REPEATED = '67', '67', '67', '67', '67', '67', '67', '67', '67'

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
IMAGE_FILEPATH = os.path.join(DATA_PATH, 'screen.png')


def get_screen_layout(adb_path=os.getenv('ADB_PATH')):
    process_screenshot = check_output([adb_path, 'exec-out', 'screencap', '-p'])
    with open(IMAGE_FILEPATH, "wb") as newFile:
        newFile.write(process_screenshot)

    execute_popen_command([adb_path, 'shell', 'uiautomator', 'dump'])
    dump_stdout = execute_popen_command([adb_path, 'shell', 'cat', UI_AUTO_DUMP_PATH])

    all_lines = ''
    for line in dump_stdout:
        all_lines += line + '\n'
    layout = xmltodict.parse(all_lines, attr_prefix='')
    processed_nodes = process_nodes(layout['hierarchy'])

    return processed_nodes


def build_image_message(image_path: str = None):
    encoded_string = ""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    image_message = {
        "type": "image_url",
        "image_url": {
          "url": f"data:image/png;base64,{encoded_string}",
          "detail": "high"
        }
    }
    return image_message


def process_nodes(node):
    """Recursively process the node to keep only the necessary keys"""
    if isinstance(node, list):
        processed_nodes = []
        for sub_node in node:
            processed = process_nodes(sub_node)
            processed_nodes.append(processed)
        return processed_nodes

    elif isinstance(node, dict):
        new_node = {k: v for k, v in node.items() if k in LAYOUT_KEEP_KEYS}
        new_node['params'] = [k for k, v in node.items() if k in LAYOUT_PARAM_KEYS and v == 'true']
        if 'node' in node:
            new_node['node'] = process_nodes(node['node'])
        return new_node

    return node

def execute_popen_command(command: list, stdout=PIPE, text=True):
    process = Popen(command, stdout=stdout, text=text)
    process.wait()
    return process.stdout


def execute_action(action, adb_path=os.getenv('ADB_PATH')):
    if action.startswith('<tap>'):
        bounds = re.findall(r'\[(.*?)\]', action)
        bounds = bounds[0].split(',') + bounds[1].split(',')
        x = (int(bounds[0]) + int(bounds[2])) / 2
        y = (int(bounds[1]) + int(bounds[3])) / 2
        print(f"Tapping on {x},{y}")
        execute_popen_command([adb_path, 'shell', 'input', 'tap', str(x), str(y)])

    elif action.startswith('<scroll_'):
        point_from, point_to = re.findall(r'\[(.*?)\]', action)
        point_from, point_to = point_from.split(','), point_to.split(',')
        x1, y1, x2, y2 = point_from[0], point_from[1], point_to[0], point_to[1]
        mid_x = str(abs(int(x1) - int(x2)) / 2)
        print(f"Scrolling from {mid_x},{y1} to {mid_x},{y2}")
        execute_popen_command([adb_path, 'shell', 'input', 'swipe', mid_x, y1, mid_x, y2])

    elif action.startswith('<swipe_'):
        left_down, right_upper = re.findall(r'\[(.*?)\]', action)
        left_down, right_upper = left_down.split(','), right_upper.split(',')
        x1, y1, x2, y2 = left_down[0], left_down[1], right_upper[0], right_upper[1]
        # invert swipe for the convenience of the user
        x1, y1, x2, y2 = x2, y2, x1, y1
        print(f"Swiping from {x1},{y1} to {x2},{y2}")
        execute_popen_command([adb_path, 'shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2)])

    elif action == '<back>':
        execute_popen_command([adb_path, 'shell', 'input', 'keyevent', 'KEYCODE_BACK'])

    elif action.startswith('<input_text>'):
        text = re.findall(r"text:'(.*?)'", action)[0]
        print(f"Inputting text: {text}")
        execute_popen_command([adb_path, 'shell', 'input', 'text', f'"{text}"'])

    elif action == '<delete_all_text>':
        print(f"Deleting all text")
        execute_popen_command([adb_path, 'shell', 'input', 'keyevent', '--longpress', BACKSPACE_KEYCODE_REPEATED])

    # Wait until everything is happened on the screen after the action is executed
    sleep(TIMEOUT_TO_WAIT_FOR_SCREEN_TO_UPDATE_SECONDS)

