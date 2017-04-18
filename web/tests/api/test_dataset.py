from tests.request_utils import decode_json

def test_get_dataset(auth_client, add_dataset):
	# List of datasets
	rv = auth_client.get('/api/datasets')
	assert rv.status_code == 200
	dataset_list = decode_json(rv)
	assert type(dataset_list) == list

	# Get first dataset
	assert 'name' in decode_json(rv)[0]
	first_dataset_name = decode_json(rv)[0]['name']

	# Get first dataset by external id
	rv = auth_client.get('/api/datasets/{}'.format(first_dataset_name))
	assert rv.status_code == 200
	dataset = decode_json(rv)
	assert dataset_list[0]['name'] == dataset['name']

	assert dataset['name'] != ''

	# Try getting nonexistent datset
	rv = auth_client.get('/api/datasets/{}'.format('non-existent'))
	assert rv.status_code == 400
	assert 'does not exist' in decode_json(rv)['message']
