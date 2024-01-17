import openai
import json
import os
import re

from prompts import SYSTEM_PROMPT
from datetime import datetime
from utils import get_screen_layout, build_image_message, execute_action, IMAGE_FILEPATH

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
LOGS_PATH = os.path.join(DATA_PATH, 'logs.json')
GOALS_PATH = os.path.join(DATA_PATH, 'goals.json')
RESULTS_PATH = os.path.join(DATA_PATH, 'results.json')

CONTEXT_WINDOW_SIZE = 6
LAST_N_HISTORY_OBJECTS = 3


class MobileLLMAgent:
    def __init__(self, adb_filepath: str):
        self.client = openai.Client()
        self.chat_history = []
        self.thoughts = []
        self.initial_user_instruction = None
        self.adb_filepath = adb_filepath

    def call_llm_api(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=2000,
            temperature=0.0
        )
        return response.choices[0].message.content
    
    def start_agent(self):
        self.chat_history.append(
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        )
        self.initiate_memory()
        self.initial_user_instruction = input("You: ")
        user_text = f"current_timestamp: {datetime.now()}\nTarget question: {self.initial_user_instruction}"
        screen_layout = get_screen_layout(self.adb_filepath)
        self.append_message_to_history(user_text, screen_layout, 'user', append_image=False)
        while True:
            self.act()

    @staticmethod
    def initiate_memory():
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        for filepath, key in zip([LOGS_PATH, GOALS_PATH, RESULTS_PATH], ['logs', 'goals', 'results']):
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    f.write('')

            if os.stat(filepath).st_size == 0:
                memory = {key: []}
                with open(filepath, 'w') as f:
                    json.dump(memory, f)

    @staticmethod
    def write_to_logs(new_logs: list):
        with open(LOGS_PATH, 'r') as f:
            logs = json.load(f)

        logs['logs'].extend(new_logs)
        with open(LOGS_PATH, 'w') as f:
            json.dump(logs, f)

    @staticmethod
    def read_from_memory(memory_filepath: list, key: str):
        with open(memory_filepath, 'r') as f:
            memory = json.load(f)
        return memory if memory and memory.get(key) else None

    def execute_system_actions(self, system_actions: str):
        new_logs = []
        execution_result = {}
        if re.findall(r'<append_goal>', system_actions):
            new_goal = system_actions.split('text:')[1].strip()
            new_goal = f'"current_timestamp": {datetime.now()}, {new_goal}'
            goals = self.read_from_memory(GOALS_PATH, 'goals')
            if goals:
                goals['goals'].append(new_goal)
            else:
                goals = {'goals': [new_goal]}

            with open(GOALS_PATH, 'w') as f:
                json.dump(goals, f)

            new_log = f'"current_timestamp": {datetime.now()}, Appended new goal: {new_goal}'
            new_logs.append(new_log)

        if re.findall(r'<get_goals>', system_actions):
            goals = self.read_from_memory(GOALS_PATH, 'goals')
            new_log = f'"current_timestamp": {datetime.now()}, Retrieved goals.'
            new_logs.append(new_log)
            execution_result['goals'] = goals['goals'] or "No goals found."

        if re.findall(r'<get_logs>', system_actions):
            logs = self.read_from_memory(LOGS_PATH, 'logs')
            new_log = f'"current_timestamp": {datetime.now()}, Retrieved logs.'
            new_logs.append(new_log)
            execution_result['logs'] = logs['logs'] or "No logs found."

        if re.findall(r'<append_result>', system_actions):
            new_result = system_actions.split('text:')[1].strip()
            results = self.read_from_memory(RESULTS_PATH, 'results')

            if results and results.get('results'):
                results['results'].append(new_result)
            else:
                results = {'results': [new_result]}

            with open(RESULTS_PATH, 'w') as f:
                json.dump(results, f)

            new_log = f'"current_timestamp": {datetime.now()}, Appended new result: {new_result}'
            new_logs.append(new_log)

        if re.findall(r'<get_results>', system_actions):
            results = self.read_from_memory(RESULTS_PATH, 'results')
            new_log = f'"current_timestamp": {datetime.now()}, Retrieved results.'
            new_logs.append(new_log)
            execution_result['results'] = results['results'] if results and results.get('results') else "No results found."

        if len(new_logs) > 0:
            self.write_to_logs(new_logs)

        return json.dumps(execution_result)

    def execute_model_actions(self, model_actions: str):
        is_multiple_actions = '|' in model_actions
        if is_multiple_actions:
            actions = model_actions.split('|')
        else:
            actions = [model_actions]

        for action in actions:
            execute_action(action.strip(), self.adb_filepath)

        new_logs = [f'"current_timestamp": {datetime.now()}, Executed agent actions: {model_actions}']
        self.write_to_logs(new_logs)

    def append_message_to_history(
            self, user_text: str, layout: dict, role: str,
            append_image: bool = True, remove_images_from_previous_user_messages: bool = False):

        if role == 'user':
            new_replica = {
                "text": user_text,
                "layout": layout
            }
        else:
            logs = self.read_from_memory(LOGS_PATH, 'logs')
            results = self.read_from_memory(RESULTS_PATH, 'results')
            last_n_thoughts = self.thoughts[-LAST_N_HISTORY_OBJECTS:] if len(self.thoughts) > 0 else ""
            last_n_logs = logs['logs'][-LAST_N_HISTORY_OBJECTS:] if logs and logs.get('logs') else ""
            last_n_results = results['results'][-LAST_N_HISTORY_OBJECTS:] if results and results.get('results') else ""
            new_replica = {
                "layout": layout,
                f"last_{LAST_N_HISTORY_OBJECTS}_thoughts": last_n_thoughts,
                f"last_{LAST_N_HISTORY_OBJECTS}_logs": last_n_logs,
                f"last_{LAST_N_HISTORY_OBJECTS}_results": last_n_results
            }
        new_message = {
            "role": role,
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(new_replica)
                }
            ]
        }
        if append_image:
            new_message['content'].append(build_image_message(IMAGE_FILEPATH))

        if remove_images_from_previous_user_messages:
            # Remove the images from the previous user messages keeping it only in the last one
            for message in self.chat_history:
                if message['role'] == 'user':
                    message['content'] = [content for content in message['content'] if content['type'] != 'image_url']

        self.chat_history.append(new_message)

    def act(self):
        screen_layout = get_screen_layout(self.adb_filepath)
        self.append_message_to_history("", screen_layout, 'assistant', append_image=True)

        print("Sending to GPT-4 Vision API...")
        if len(self.chat_history) > CONTEXT_WINDOW_SIZE:
            context_window = [
                                 self.chat_history[0], # System prompt
                                 self.chat_history[1] # User question
                             ] + self.chat_history[-(CONTEXT_WINDOW_SIZE - 1):] # Last N messages
        else:
            context_window = self.chat_history

        response = self.call_llm_api(context_window)
        print(f"🤔: {response}")
        self.chat_history.append({"role": "assistant", "content": response})
        response_json = json.loads(response)

        if response_json.get('thought_process') and response_json['thought_process'] != '':
            thought = response_json['thought_process']
            thought = f'"current_timestamp": {datetime.now()}, {thought}'
            self.thoughts.append(thought)

        if response_json.get('agent_action') and response_json['agent_action'] != '':
            self.execute_model_actions(response_json['agent_action'])

        if response_json.get('system_action') and response_json['system_action'] != '':
            system_response = self.execute_system_actions(response_json['system_action'])
            if system_response:
                post_system_response = {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": system_response
                        }
                    ]
                }
                self.chat_history.append(post_system_response)

