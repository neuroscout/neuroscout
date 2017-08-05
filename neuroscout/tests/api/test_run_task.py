from tests.request_utils import decode_json

def test_get_run(auth_client, add_dataset):
	# List of runs
	resp = auth_client.get('/api/runs')
	assert resp.status_code == 200
	run_list = decode_json(resp)
	assert type(run_list) == list

	# Get first dataset
	first_run_id = run_list[0]['id']
	assert 'dataset_id' in run_list[0]

	# Get first dataset by external id
	resp = auth_client.get('/api/runs/{}'.format(first_run_id))
	assert resp.status_code == 200
	run = decode_json(resp)
	assert first_run_id == run['id']
	assert 'task' in run
	assert 'id' in run['task']

	assert run['dataset_id'] == add_dataset
	assert run['subject'] == '01'

	# Try getting nonexistent run
	resp = auth_client.get('/api/runs/{}'.format('123'))
	assert resp.status_code == 404

	# Test parameters
	resp = auth_client.get('/api/runs', params={'dataset_id' : add_dataset})
	assert resp.status_code == 200
	run_p = decode_json(resp)
	assert type(run_p) == list
	for run in run_p:
		assert run['dataset_id'] == add_dataset

	resp = auth_client.get('/api/runs', params={'dataset_id' : '1232'})
	assert resp.status_code == 200
	assert len(decode_json(resp)) == 0

	# Test getting all fields
	resp = auth_client.get('/api/runs', params={'dataset_id' : add_dataset,
											'all_fields' : 'True'})
	assert 'task' in decode_json(resp)[0]
	assert len(decode_json(resp)[0]['task']) == 2
	task_id = decode_json(resp)[0]['task']['id']

	# Test filtering by multiple parameters
	resp = auth_client.get('/api/runs', params={'number': '01,02',
											'task': 'bidstest'})
	assert resp.status_code == 200
	run_p = decode_json(resp)
	assert len(run_p) == 4

	# Test task route
	resp = auth_client.get('/api/tasks/{}'.format(task_id))
	assert 'description' in decode_json(resp)

	# Test task route filtering
	resp = auth_client.get('/api/tasks', params={'dataset_id' : add_dataset})
	assert 'description' in decode_json(resp)[0]
