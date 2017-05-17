from tests.request_utils import decode_json
from models.analysis import Analysis

def test_get(auth_client, add_analysis):
	# List of analyses
	rv = auth_client.get('/api/analyses')
	assert rv.status_code == 200
	analysis_list = decode_json(rv)
	assert type(analysis_list) == list
	assert len(analysis_list) == 1

	# Get first analysis
	assert 'hash_id' in decode_json(rv)[0]
	first_analysis_id = decode_json(rv)[0]['hash_id']

	# Get first analysis by id
	rv = auth_client.get('/api/analyses/{}'.format(first_analysis_id))
	assert rv.status_code == 200
	analysis = decode_json(rv)
	assert analysis_list[0] == analysis

	for required_fields in ['name', 'description']:
		assert analysis[required_fields] != ''

	# Try getting nonexistent analysis
	rv = auth_client.get('/api/analyses/{}'.format(987654))
	assert rv.status_code == 404
	# assert 'requested URL was not found' in decode_json(rv)['message']

def test_post(auth_client, add_dataset):
	## Add analysis
	test_analysis = {
	"dataset_id" : add_dataset,
	"name" : "some analysis",
	"description" : "pretty damn innovative"
	}

	rv = auth_client.post('/api/analyses', data = test_analysis)
	assert rv.status_code == 200
	rv_json = decode_json(rv)
	assert type(rv_json) == dict
	for field in ['dataset_id', 'name', 'description', 'hash_id']:
		assert field in rv_json

	## Check db directly
	assert Analysis.query.filter_by(hash_id = rv_json['hash_id']).count() == 1
	assert Analysis.query.filter_by(hash_id = rv_json['hash_id']).one().name == 'some analysis'

	## Re post analysis, check that id is diffeent
	rv_2 = auth_client.post('/api/analyses', data = test_analysis)
	assert rv_2.status_code == 200
	assert decode_json(rv_2)['hash_id'] != decode_json(rv)['hash_id']

    ## Test incorrect post
	dataset_id = decode_json(auth_client.get('/api/datasets'))[0]['id']

	bad_post = {
	"dataset_id" : "234234",
	"name" : "some analysis",
	"description" : "pretty damn innovative"
	}

	rv = auth_client.post('/api/analyses', data = bad_post)
	assert rv.status_code == 422
	# assert decode_json(rv)['errors']['dataset_id'][0] == 'Invalid dataset id.'

	bad_post_2 = {
	"dataset_id" : dataset_id,
	"description" : "pretty damn innovative"
	}

	rv = auth_client.post('/api/analyses', data = bad_post_2)
	assert rv.status_code == 422
	# assert decode_json(rv)['errors']['name'][0] == 'Missing data for required field.'

def test_clone(auth_client, add_dataset):
	## Add analysis
	test_analysis = {
	"dataset_id" : add_dataset,
	"name" : "some analysis 2",
	}

	rv = auth_client.post('/api/analyses', data = test_analysis)
	analysis_id = decode_json(rv)['hash_id']

	# Clone analysis by id
	rv = auth_client.post('/api/analyses/{}/clone'.format(analysis_id))
	assert rv.status_code == 422

	# PUT to uneditable and try again
	# analysis = decode_json(rv)
	# assert analysis['hash_id'] != analysis_id

def test_put():
	pass
