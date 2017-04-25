from tests.request_utils import decode_json

def test_get_run(auth_client, add_dataset):
	# List of runs
	rv = auth_client.get('/api/runs')
	assert rv.status_code == 200
	run_list = decode_json(rv)
	assert type(run_list) == list

	# Get first dataset
	first_run_id = run_list[0]['id']
	assert 'dataset_id' in run_list[0]
	assert 'task_description' not in run_list[0]

	# Get first dataset by external id
	rv = auth_client.get('/api/runs/{}'.format(first_run_id))
	assert rv.status_code == 200
	run = decode_json(rv)
	assert first_run_id == run['id']
	assert 'task_description' in run

	assert run['TR'] == 2
	assert run['dataset_id'] == 'Test Dataset'
	assert run['subject'] == '01'

	# Try getting nonexistent run
	rv = auth_client.get('/api/runs/{}'.format('123'))
	assert rv.status_code == 404
	assert 'requested URL was not found' in decode_json(rv)['message']

	# Test parameters
	rv = auth_client.get('/api/runs', data={'dataset_id' : add_dataset})
	assert rv.status_code == 200
	run_p = decode_json(rv)
	assert type(run_p) == list
	for run in run_p:
		assert run['dataset_id'] == add_dataset

	rv = auth_client.get('/api/runs', data={'dataset_id' : 'non-existent'})
	assert rv.status_code == 200
	assert len(decode_json(rv)) == 0

	# Test getting all fields
	rv = auth_client.get('/api/runs', data={'dataset_id' : add_dataset,
											'all_fields' : 'True'})
	assert 'TR' in decode_json(rv)[0]

	# Test filtering by multiple parameters
	rv = auth_client.get('/api/runs', data={'number': '01,02',
											'task': 'bidstest'})
	assert rv.status_code == 200
	run_p = decode_json(rv)
	assert len(run_p) == 4
