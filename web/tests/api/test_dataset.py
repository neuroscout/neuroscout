from tests.request_utils import decode_json

def test_get_dataset(auth_client, add_dataset):
	# List of datasets
	rv = auth_client.get('/api/datasets')
	assert rv.status_code == 200
	dataset_list = decode_json(rv)
	assert type(dataset_list) == list
	assert 'description' not in dataset_list[0]

	# Test all_frields
	rv = auth_client.get('/api/datasets', data = {'all_fields' : 'True'})
	assert rv.status_code == 200
	assert 'description' in decode_json(rv)[0]

	# Get first dataset
	assert 'mimetypes' in dataset_list[0]
	assert 'tasks' in dataset_list[0]
	first_dataset_id = dataset_list[0]['id']

	# Get first dataset by external id
	rv = auth_client.get('/api/datasets/{}'.format(first_dataset_id))
	assert rv.status_code == 200
	dataset = decode_json(rv)
	assert first_dataset_id == dataset['id']
	assert dataset['mimetypes'] == ['image/jpeg']
	assert dataset['tasks'] == ['bidstest']

	# Try getting nonexistent datset
	rv = auth_client.get('/api/datasets/{}'.format('non-existent'))
	assert rv.status_code == 404
	assert 'requested URL was not found' in decode_json(rv)['message']
