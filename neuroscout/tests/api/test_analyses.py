from tests.request_utils import decode_json
from ...models import Analysis, Run
import pytest
import os
import time

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
	assert len(analysis_list) == 0 # Analysis should not be displayed, yet...

	# Get first analysis
	first_analysis_id = analysis.hash_id

	# Get first analysis by id
	resp= auth_client.get('/api/analyses/{}'.format(first_analysis_id))
	assert resp.status_code == 200
	analysis = decode_json(resp)

	for required_fields in ['name', 'description']:
		assert analysis[required_fields] != ''

	# Try getting nonexistent analysis
	resp= auth_client.get('/api/analyses/{}'.format(987654))
	assert resp.status_code == 404
	# assert 'requested URL was not found' in decode_json(resp)['message']

	# Test getting resources
	resp = auth_client.get('/api/analyses/{}/resources'.format(first_analysis_id))
	assert resp.status_code == 200
	assert 'dataset_address' in decode_json(resp)
	assert 'mask_paths' in decode_json(resp)
	assert 'preproc_address' in decode_json(resp)

def test_post(auth_client, add_task, add_predictor):
	## Add analysis
	test_analysis = {
	"dataset_id" : add_task,
	"name" : "some analysis",
	"description" : "pretty damn innovative",
	"model" : {
	  "name": "test_model1",
	  "description": "this is a sample",
	  "input": {
	    "task": "bidstest"
	  },
	  "blocks": [
	    {
	      "level": "run",
	      "transformations": [
	        {
	          "name": "scale",
	          "input": [
	            "BrightnessExtractor.brightness"
	          ]
	        }
	      ],
	      "model": {
	        "HRF_variables": [
	          "BrightnessExtractor.brightness",
	          "VibranceExtractor.vibrance"
	        ],
	        "variables": [
	          "BrightnessExtractor.brightness",
	          "VibranceExtractor.vibrance"
	        ]
	      },
	      "contrasts": [
	        {
	          "name": "BvsV",
	          "condition_list": [
	            "BrightnessExtractor.brightness",
	            "VibranceExtractor.vibrance"
	          ],
	          "weights": [
	            1,
	            -1
	          ],
	          "type": "T"
	        }
	      ]
	    },
	    {
	      "level": "session",
	    },
	    {
	      "level": "subject",
	      "model": {
	        "variables": [
	          "BvsV"
	        ]
	      },
	    },
	    {
	      "level": "dataset",
	      "model": {
	        "variables": [
	          "session_diff"
	        ]
	      },
	    }
	  ]
	}
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
	assert decode_json(resp)['message']['name'][0] == \
			'Missing data for required field.'

def test_clone(session, auth_client, add_task, add_analysis, add_users):
	(id1, id2), _ = add_users
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	# Clone analysis by id
	resp= auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))
	clone_json = decode_json(resp)
	assert clone_json['hash_id'] != analysis.hash_id

	# Check that runs and predictors have been copied
	assert len(clone_json['runs']) == len(analysis.runs)
	assert len(clone_json['predictors']) == len(analysis.predictors)

	# Change user ID to someone else's and try again
	analysis.status = 'DRAFT'
	analysis.user_id = id2
	session.commit()

	resp = auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))
	assert resp.status_code == 422

def test_put(auth_client, add_analysis, add_task, session):
	# Get analysis to edit
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	analysis_json = decode_json(
		auth_client.get('/api/analyses/{}'.format(analysis.hash_id)))

	analysis_json['name'] = 'NEW NAME'

	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=analysis_json)
	assert resp.status_code == 200
	new_analysis = decode_json(resp)
	assert new_analysis['name'] == "NEW NAME"

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

	# Add and delete analysis
	## Add analysis
	test_analysis = {
	"dataset_id" : add_task,
	"name" : "some analysis",
	"description" : "pretty damn innovative"
	}

	resp = auth_client.post('/api/analyses', data = test_analysis)
	analysis_json = decode_json(resp)

	# Test adding a run_id
	analysis_json['runs'] = [{'id' : Run.query.first().id }]

	resp = auth_client.put('/api/analyses/{}'.format(analysis_json['hash_id']),
						data=analysis_json)
	assert resp.status_code == 200

	# Try deleting anlaysis
	delresp = auth_client.delete('/api/analyses/{}'.format(analysis_json['hash_id']))
	assert delresp.status_code == 200

	assert Analysis.query.filter_by(hash_id=decode_json(resp)['hash_id']).count() == 0

@pytest.mark.skipif('CELERY_BROKER_URL' not in os.environ,
                    reason="requires redis")
def test_compile(auth_client, add_analysis, add_analysis_fail):
	analysis  = Analysis.query.filter_by(id=add_analysis).first()
	analysis_bad = Analysis.query.filter_by(id=add_analysis_fail).first()

	# Test analysis from user 2 - should fail compilation
	resp = auth_client.post('/api/analyses/{}/compile'.format(analysis_bad.hash_id))
	assert resp.status_code == 200
	locked_analysis = decode_json(resp)

	# Test status after some time
	resp = auth_client.get('/api/analyses/{}/status'.format(analysis_bad.hash_id))
	timeout = time.time() + 60*1   # 1 minute timeout
	while decode_json(resp)['status'] == 'PENDING':
		time.sleep(0.2)
		resp = auth_client.get('/api/analyses/{}/status'.format(analysis_bad.hash_id))
		if time.time() > timeout:
			assert 0
			break

	new_analysis = decode_json(resp)
	if new_analysis['status'] !=  'FAILED':
		assert 0

	# Test getting bundle prior to compiling
	resp = auth_client.get('/api/analyses/{}/bundle'.format(analysis.hash_id))
	assert resp.status_code == 404

	# Test compiling
	resp = auth_client.post('/api/analyses/{}/compile'.format(analysis.hash_id))
	assert resp.status_code == 200
	locked_analysis = decode_json(resp)

	assert locked_analysis['status'] == 'PENDING'
	assert locked_analysis['compiled_at'] != ''

	# Test editing locked
	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data={'name' : "New name should not be allowed"})
	assert resp.status_code == 422

	# Test editing status
	locked_analysis['private'] = False
	locked_analysis['new_name'] = "Should not change to this"
	resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
						data=locked_analysis)
	assert resp.status_code == 200
	assert decode_json(resp)['private'] == False
	assert decode_json(resp)['name'] != "Should not change to this"

	# Test status after some time
	resp = auth_client.get('/api/analyses/{}/status'.format(analysis.hash_id))
	timeout = time.time() + 60*1   # 1 minute timeout
	while decode_json(resp)['status'] == 'PENDING':
		time.sleep(0.2)
		if time.time() > timeout:
			assert 0
			break
		resp = auth_client.get('/api/analyses/{}/status'.format(analysis.hash_id))

	if decode_json(resp)['status'] != 'PASSED':
		assert 0

	# Try deleting locked analysis
	resp = auth_client.delete('/api/analyses/{}'.format(analysis.hash_id))
	assert resp.status_code == 422

	# Test bundle is tarfile
	resp = auth_client.get('/api/analyses/{}/bundle'.format(analysis.hash_id))
	assert resp.status_code == 200
	assert resp.mimetype == 'application/x-tar'


def test_auth_id(auth_client, add_analysis_user2):
	# Try deleting analysis you are not owner of
	analysis  = Analysis.query.filter_by(id=add_analysis_user2).first()
	resp = auth_client.delete('/api/analyses/{}'.format(analysis.hash_id))

	assert resp.status_code == 401
