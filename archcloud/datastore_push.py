

# Imports the Google Cloud client library
from google.cloud import datastore


# name is the id/key for the entry (must be unique)
def push(
	job_id,
	metadata, 
	job_submission_json, 
	manifest,
	output,
	status
):
	# Instantiates a client
	datastore_client = datastore.Client(namespace='CSE141')

	# The kind for the new entity
	kind = 'CSE141L-Job'
	# The Cloud Datastore key for the new entity
	job_key = datastore_client.key(kind, job_id)

	# Prepares the new entity
	job = datastore.Entity(key=job_key, exclude_from_indexes=('metadata', 'job_submission_json', 'manifest', 'output'))
	job['job_id'] = job_id
	job['metadata'] = metadata
	job['job_submission_json'] = job_submission_json
	job['manifest'] = manifest
	job['output'] = output
	job['status'] = status

	# Saves the entity
	datastore_client.put(job)

	print('Saved {}: {}'.format(job.key.name, str(job)))
