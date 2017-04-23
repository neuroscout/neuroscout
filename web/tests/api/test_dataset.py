from tests.request_utils import decode_json

def test_get_dataset(auth_client, add_dataset):
	# List of datasets
	rv = auth_client.get('/api/datasets')
	assert rv.status_code == 200
	dataset_list = decode_json(rv)
	assert type(dataset_list) == list

	# Get first dataset
	assert 'mimetypes' in dataset_list[0]
	assert 'tasks' in dataset_list[0]
	first_dataset_id = dataset_list[0]['id']

	# Get first dataset by external id
	rv = auth_client.get('/api/datasets/{}'.format(first_dataset_id))
	assert rv.status_code == 200
	dataset = decode_json(rv)
	assert dataset_list[0]['id'] == dataset['id']
	assert dataset['mimetypes'] == ['image/jpeg']
	assert dataset['tasks'] == ['bidstest']

	# Try getting nonexistent datset
	rv = auth_client.get('/api/datasets/{}'.format('non-existent'))
	assert rv.status_code == 400
	assert 'does not exist' in decode_json(rv)['message']
