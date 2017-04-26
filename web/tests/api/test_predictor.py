from tests.request_utils import decode_json
def test_get_predictor(auth_client, add_dataset):
	# List of runs
	rv = auth_client.get('/api/predictors')
	assert rv.status_code == 200
	pred_list = decode_json(rv)
	assert type(pred_list) == list

	# Get first dataset
	first_pred_id = pred_list[0]['id']
	assert 'name' in pred_list[0]
	assert 'predictor_events' not in pred_list[0]

	# Get first dataset by external id
	rv = auth_client.get('/api/predictors/{}'.format(first_pred_id))
	assert rv.status_code == 200
	pred = decode_json(rv)
	assert first_pred_id == pred['id']
	assert 'predictor_events' in pred

	# Try getting nonexistent predictor
	rv = auth_client.get('/api/predictors/{}'.format('123'))
	assert rv.status_code == 404
	assert 'requested URL was not found' in decode_json(rv)['message']

	# Test parameters
	ds = decode_json(
		auth_client.get('/api/datasets', data={'all_fields' : 'True'}))
	run_id = ds[0]['runs'][0]
	rv = auth_client.get('/api/predictors', data={'run_id' : run_id})
	assert rv.status_code == 200
	pred_select = decode_json(rv)
	assert type(pred_select) == list


	rv = auth_client.get('/api/predictors', data={'run_id' : '123123'})
	assert rv.status_code == 200
	assert len(decode_json(rv)) == 0

	# Test getting all fields
	rv = auth_client.get('/api/predictors', data={'all_fields' : 'True'})
	assert 'predictor_events' in decode_json(rv)[0]

	# Test filtering by multiple parameters
	rv = auth_client.get('/api/predictors', data={'name': 'rt',
											'run_id': run_id})
	assert rv.status_code == 200
	pred_p = decode_json(rv)
	assert len(pred_p) == 1
