from tests.request_utils import decode_json
from models import Analysis, Run

def test_get(session, auth_client, add_analysis):
	# List of analyses
	resp= auth_client.get('/api/analyses')
	assert resp.status_code == 200
	analysis_list = decode_json(resp)
	assert type(analysis_list) == list
	assert len(analysis_list) == 0 # Analysis is private by default

	# Make analysis public
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	analysis.private = False
	session.commit()

	# List of analyses
	resp= auth_client.get('/api/analyses')
	assert resp.status_code == 200
	analysis_list = decode_json(resp)
	assert type(analysis_list) == list
	assert len(analysis_list) == 1 # Analysis should now be public

	# Get first analysis
	assert 'hash_id' in decode_json(resp)[0]
	first_analysis_id = decode_json(resp)[0]['hash_id']

	# Get first analysis by id
	resp= auth_client.get('/api/analyses/{}'.format(first_analysis_id))
	assert resp.status_code == 200
	analysis = decode_json(resp)
	assert analysis_list[0] == analysis

	for required_fields in ['name', 'description']:
		assert analysis[required_fields] != ''

	# Try getting nonexistent analysis
	resp= auth_client.get('/api/analyses/{}'.format(987654))
	assert resp.status_code == 404
	# assert 'requested URL was not found' in decode_json(resp)['message']

def test_post(auth_client, add_dataset):
	## Add analysis
	test_analysis = {
	"dataset_id" : add_dataset,
	"name" : "some analysis",
	"description" : "pretty damn innovative"
	}

	resp= auth_client.post('/api/analyses', data = test_analysis)
	assert resp.status_code == 200
	rv_json = decode_json(resp)
	assert type(rv_json) == dict
	for field in ['dataset_id', 'name', 'description', 'hash_id']:
		assert field in rv_json

	## Check db directly
	assert Analysis.query.filter_by(hash_id = rv_json['hash_id']).count() == 1
	assert Analysis.query.filter_by(hash_id = rv_json['hash_id']).one().name == 'some analysis'

	## Re post analysis, check that id is diffeent
	rv_2 = auth_client.post('/api/analyses', data = test_analysis)
	assert rv_2.status_code == 200
	assert decode_json(rv_2)['hash_id'] != decode_json(resp)['hash_id']

    ## Test incorrect post
	dataset_id = decode_json(auth_client.get('/api/datasets'))[0]['id']

	bad_post = {
	"dataset_id" : "234234",
	"name" : "some analysis",
	"description" : "pretty damn innovative"
	}

	resp= auth_client.post('/api/analyses', data = bad_post)
	assert resp.status_code == 422
	assert decode_json(resp)['message']['dataset_id'][0] == 'Invalid dataset id.'

	bad_post_2 = {
	"dataset_id" : dataset_id,
	"description" : "pretty damn innovative"
	}

	resp= auth_client.post('/api/analyses', data = bad_post_2)
	assert resp.status_code == 422
	assert decode_json(resp)['message']['name'][0] == 'Missing data for required field.'

def test_clone(session, auth_client, add_dataset, add_analysis):
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	# Clone analysis by id
	resp= auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))
	assert resp.status_code == 422

	# Make uneditable and try again
	analysis.locked = True
	session.commit()

	resp= auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))
	clone_json = decode_json(resp)
	assert clone_json['hash_id'] != analysis.hash_id

def test_put(auth_client, add_analysis):
	# Get analysis to edit
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	analysis_json = decode_json(
		auth_client.get('/api/analyses/{}'.format(analysis.hash_id)))

	analysis_json['name'] = 'NEW NAME!'

	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=analysis_json)
	assert resp.status_code == 200
	new_analysis = decode_json(resp)
	assert new_analysis['name'] == "NEW NAME!"

	# Test adding a run_id
	analysis_json['runs'] = [{'id' : Run.query.first().id }]

	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=analysis_json)
	assert resp.status_code == 200
	new_analysis = decode_json(resp)
	assert new_analysis['runs'] == [{'id' :	Run.query.first().id }]

	# Test adding an invalid run id
	analysis_json['runs'] = [{'id' : 9999 }]

	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=analysis_json)
	assert resp.status_code == 422
	assert 'runs' in  decode_json(resp)['message']

	# Test locking
	new_analysis['locked'] = True
	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=new_analysis)
	assert resp.status_code == 200
	locked_analysis = decode_json(resp)
	assert locked_analysis['locked'] == True
	assert locked_analysis['locked_at'] != ''

	locked_analysis['name'] = 'New name should not be allowed'
	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=locked_analysis)
	assert resp.status_code == 422
