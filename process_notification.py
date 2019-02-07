import base64
import json
import os
import re

import requests


def parse_message(config, message, subject):
    priority = 0
    if "Security System Armed Stay" in message:
        notification = "Armed Stay"
    elif "Security System Disarmed" in message:
        notification = "Disarmed"
    elif "Security System disarmed" in message:
        notification = "Disarmed"
    elif "Security System Armed Away" in message:
        notification = "Armed Away"
    elif "Attempt to set Security Panel Arm Mode" in message:
        notification = "Pulse failed to change state"
    elif "Security Panel AC power restored" in message:
        notification = "AC Power Restored"
    elif "Security Panel AC power loss" in message:
        notification = "AC Power Fail"
    elif "BURGLARY ALARM" in message:
        notification = "Alarm!"
        priority = 1

        m = re.findall(r'Sensor: (.*) \(', message)
        if m:
            notification += " " + m[0]
    elif "Alarm cleared" in message:
        notification = "Alarm cleared"
        priority = 1
    elif 'Security System Alarm' not in subject and 'by NWS' in subject:
        notification = subject
        priority = 1
    else:
        notification = "Donno..."

    m = re.findall(r'access code (\d+)', message)
    if m:
        user_id = int(m[0])
        users = config['user_names']
        notification += " by " + users.get(user_id, 'user {}'.format(user_id))

    return priority, notification


def send_notification(pulse_config, priority, notification_text):
    data = {'token': pulse_config['app_key'], 'user': ','.join(pulse_config['notify_keys']),
            'message': notification_text, 'priority': priority}
    requests.post('https://api.pushover.net/1/messages.json', data=data)


def load_config():
    return {'app_key': os.environ['PUSHOVER_APP_KEY'],
            'notify_keys': json.loads(base64.b64decode(os.environ['PUSHOVER_NOTIFY_KEYS'])),
            'user_names': json.loads(base64.b64decode(os.environ['USERNAME_MAPPING']))}


def main(event, context):
    form_data = event['extensions']['request'].POST
    input_message = form_data.get('body-plain', 'no-body')
    subject = form_data.get('subject', 'no-subject')
    config = load_config()
    priority, notification_text = parse_message(config, input_message, subject)
    send_notification(config, priority, notification_text)
    return "OK"
