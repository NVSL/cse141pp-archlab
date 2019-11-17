# Imports the Google Cloud client library
from google.cloud import datastore

# name is the id/key for the entry (must be unique)
def pull(job_id):
	# Instantiates a client
	datastore_client = datastore.Client(namespace='CSE141')

	# The kind for the new entity
	kind = 'CSE141L-Job'

	query = datastore_client.query(kind=kind)
	query.add_filter('job_id', '=', job_id)
	query_iter = query.fetch()
	for entity in query_iter:
                return entity
