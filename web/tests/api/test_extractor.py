from tests.request_utils import decode_json

def test_get(auth_client, add_extractor):
	# List of analyses
	rv = auth_client.get('/api/extractors')
	assert rv.status_code == 200
	extractor_list = decode_json(rv)
	assert type(extractor_list) == list	
	assert len(extractor_list) == 1

	# Get first extractior
	assert 'id' in decode_json(rv)[0]
	first_extractor_id = decode_json(rv)[0]['id']

	# Get first analysis by id
	rv = auth_client.get('/api/extractors/{}'.format(first_extractor_id))
	assert rv.status_code == 200
	extractor = decode_json(rv)
	assert extractor_list[0] == extractor

	# Try getting nonexistent extractor
	rv = auth_client.get('/api/extractors/{}'.format(987654))
	assert rv.status_code == 400
	assert 'does not exist' in decode_json(rv)['message']
