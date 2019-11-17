"""
pubsub_pull.

This program pulls CSE141 jobs from the pubsub queue.

Usage: pubsub_pull

"""

import os

from google.cloud import pubsub_v1
# from google.oauth2 import service_account
import google.auth

from docopt import docopt

def pull(GOOGLE_CLOUD_PROJECT=None, SUBSCRIPTION=None):
    credentials, project = google.auth.default()
    # credentials = service_account.Credentials.from_service_account_file('subscriber_credentials.json')

    subscriber = pubsub_v1.SubscriberClient()

    if GOOGLE_CLOUD_PROJECT is None:
        GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')

    if SUBSCRIPTION is None:
        SUBSCRIPTION = os.getenv('PUBSUB_SUBSCRIPTION')

    # requires python 3.6
    # subscription_name = f'projects/{GOOGLE_CLOUD_PROJECT}/subscriptions/{SUBSCRIPTION}' 

    # Packet servers running ubuntu 16.04 only have python 3.5
    subscription_name = 'projects/{GOOGLE_CLOUD_PROJECT}/subscriptions/{SUBSCRIPTION}'.format(GOOGLE_CLOUD_PROJECT=GOOGLE_CLOUD_PROJECT, SUBSCRIPTION=SUBSCRIPTION)

    subscription_path = subscriber.subscription_path(GOOGLE_CLOUD_PROJECT, SUBSCRIPTION)
    print(subscription_path)
    response = subscriber.pull(subscription_path, max_messages=1)

    if len(response.received_messages) > 0:
        for msg in response.received_messages:
            print('Received message:', msg.message)
            # with open('LAB_ID', 'w') as f:
            #     if 'lab_ID' in msg.message.attributes:
            #         f.write(str(msg.message.attributes['lab_ID']))
            # with open('STUDENT_ID', 'w') as f:
            #     if 'student_ID' in msg.message.attributes:
            #         f.write(str(msg.message.attributes['student_ID']))
            # with open('SUBMISSION_REPO', 'w') as f:
            #     if 'github_repo' in msg.message.attributes:
            #         f.write(str(msg.message.attributes['github_repo']))
            subscriber.acknowledge(subscription_path, [msg.ack_id])
            break
        return msg
    else:
        return None



    # def callback(message):
    #     print(message)
    #     message.ack()

    # future = subscriber.subscribe(subscription_name, callback)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='pubsub_pull 0.1')
    pull()
