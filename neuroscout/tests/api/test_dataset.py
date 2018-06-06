from tests.request_utils import decode_json

def test_get_dataset(auth_client, add_task):
	# List of datasets
	resp = auth_client.get('/api/datasets')
	assert resp.status_code == 200
	dataset_list = decode_json(resp)
	assert type(dataset_list) == list

	# Get first dataset
	assert 'tasks' in dataset_list[0]
	first_dataset_id = dataset_list[0]['id']

	# Get first dataset by external id
	resp = auth_client.get('/api/datasets/{}'.format(first_dataset_id))
	assert resp.status_code == 200
	dataset = decode_json(resp)
	assert first_dataset_id == dataset['id']
	assert dataset['tasks'][0]['name'] == 'bidstest'
	assert dataset['name'] == 'Test Dataset'

	# Try getting nonexistent datset
	resp = auth_client.get('/api/datasets/{}'.format('1324'))
	assert resp.status_code == 404
