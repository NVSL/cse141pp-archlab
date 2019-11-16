"""
pubsub_push.

This program pushes CSE141 jobs to the pubsub queue.

Usage: pubsub_push <job_id> <metadata> <job_submission_json> <manifest>

"""

import os

from google.cloud import pubsub_v1
import google.auth

from docopt import docopt

def push(
	job_id
):
	credentials, project = google.auth.default()

	publisher = pubsub_v1.PublisherClient()
	GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
	TOPIC = os.getenv('PUBSUB_TOPIC')
	topic_name = f'projects/{GOOGLE_CLOUD_PROJECT}/topics/{TOPIC}'
	print(topic_name)
	# publisher.create_topic(topic_name)

	# studentID = 'A091234123'
	# github_repo = 'https://github.com/choltz95/SA-PCB'

	print('Publishing')
	publisher.publish(
		topic_name, 
		b'new CSE141 job submission', 
		job_id=job_id
	)
	print('Published')

if __name__ == '__main__':
    arguments = docopt(__doc__, version='pubsub_push 0.2')
    print(arguments)
    push(
    	job_id=arguments['<job_id>']
    )