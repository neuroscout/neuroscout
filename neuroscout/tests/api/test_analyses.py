from ..request_utils import decode_json
from ...models import Analysis, Run, Report
from ...tasks import report
from ...core import app
import pytest


def test_get(session, auth_client, add_analysis):
    # List of analyses
    resp = auth_client.get('/api/analyses')
    assert resp.status_code == 200
    analysis_list = decode_json(resp)
    assert type(analysis_list) == list
    assert len(analysis_list) == 0  # Analysis is private by default

    # Make analysis public
    analysis = Analysis.query.filter_by(id=add_analysis).first()
    dataset_id = analysis.dataset_id
    name = analysis.name
    analysis.private = False
    analysis.status = "PASSED"
    session.commit()

    # List of analyses
    resp = auth_client.get('/api/analyses')
    assert resp.status_code == 200
    analysis_list = decode_json(resp)
    assert type(analysis_list) == list
    assert len(analysis_list) == 1

    # Filter by dataset_id and name
    resp = auth_client.get('/api/analyses',
                           params=dict(dataset_id=dataset_id, name=name))
    assert resp.status_code == 200
    analysis_list = decode_json(resp)
    assert len(analysis_list) == 1

    # Filter with wrong name
    resp = auth_client.get('/api/analyses',
                           params=dict(dataset_id=100, name='sds'))
    assert resp.status_code == 200
    analysis_list = decode_json(resp)
    assert len(analysis_list) == 0

    # Get first analysis
    first_analysis_id = analysis.hash_id

    # Get first analysis by id
    resp = auth_client.get('/api/analyses/{}'.format(first_analysis_id))
    assert resp.status_code == 200
    analysis = decode_json(resp)

    for required_fields in ['name', 'description']:
        assert analysis[required_fields] != ''

    # Try getting nonexistent analysis
    resp = auth_client.get('/api/analyses/{}'.format(987654))
    assert resp.status_code == 404
    # assert 'requested URL was not found' in decode_json(resp)['message']

    # Test getting resources
    resp = auth_client.get('/api/analyses/{}/resources'.format(
        first_analysis_id))
    assert resp.status_code == 200
    assert 'dataset_address' in decode_json(resp)
    assert 'preproc_address' in decode_json(resp)


def test_post(auth_client, add_task, add_predictor):
    # Add analysis
    test_analysis = {
        "dataset_id": add_task,
        "name": "some analysis",
        "description": "pretty damn innovative",
        "model": {
          "Name": "test_model1",
          "Description": "this is a sample",
          "Input": {
            "task": "bidstest"
          },
          "Steps": [
            {
              "Level": "Run",
              "Transformations": [
                {
                  "Name": "Scale",
                  "Input": [
                    "BrightnessExtractor.brightness"
                  ]
                }
              ],
              "Model": {
                "X": [
                  "BrightnessExtractor.brightness",
                  "VibranceExtractor.vibrance"
                ]
              },
              "Contrasts": [
                {
                  "Mame": "BvsV",
                  "ConditionList": [
                    "BrightnessExtractor.brightness",
                    "VibranceExtractor.vibrance"
                  ],
                  "Weights": [
                    1,
                    -1
                  ],
                  "Type": "T"
                }
              ]
            },
            {
              "Level": "Session",
            },
            {
              "Level": "Subject",
              "Model": {
                "X": [
                  "BvsV"
                ]
              },
            },
            {
              "Level": "Dataset",
              "Model": {
                "X": [
                  "session_diff"
                ]
              },
            }
          ]
        }
        }

    resp = auth_client.post('/api/analyses', data=test_analysis)
    assert resp.status_code == 200
    rv_json = decode_json(resp)
    assert type(rv_json) == dict
    for field in ['dataset_id', 'name', 'description', 'hash_id']:
        assert field in rv_json

    # Check db directly
    assert Analysis.query.filter_by(hash_id=rv_json['hash_id']).count() == 1
    assert Analysis.query.filter_by(
        hash_id=rv_json['hash_id']).one().name == 'some analysis'

    # Re post analysis, check that id is diffeent
    rv_2 = auth_client.post('/api/analyses', data=test_analysis)
    assert rv_2.status_code == 200
    assert decode_json(rv_2)['hash_id'] != decode_json(resp)['hash_id']

    # Test incorrect post
    dataset_id = decode_json(auth_client.get('/api/datasets'))[0]['id']

    bad_post = {
        "dataset_id": "234234",
        "name": "some analysis",
        "description": "pretty damn innovative"
        }

    resp = auth_client.post('/api/analyses', data=bad_post)
    assert resp.status_code == 422
    assert decode_json(resp)['message']['dataset_id'][0] == \
        'Invalid dataset id.'

    bad_post_2 = {
        "dataset_id": dataset_id,
        "description": "pretty damn innovative"
        }

    resp = auth_client.post('/api/analyses', data=bad_post_2)
    assert resp.status_code == 422
    assert decode_json(resp)['message']['name'][0] == \
        'Missing data for required field.'


def test_clone(session, auth_client, add_task, add_analysis, add_users):
    (id1, id2), _ = add_users
    analysis = Analysis.query.filter_by(id=add_analysis).first()

    # Try cloning  DRAFT
    resp = auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))
    assert resp.status_code == 422

    # Change status try again
    analysis.status = 'PASSED'
    session.commit()

    resp = auth_client.post('/api/analyses/{}/clone'.format(analysis.hash_id))

    clone_json = decode_json(resp)
    assert clone_json['hash_id'] != analysis.hash_id

    # Check that runs and predictors have been copied
    assert len(clone_json['runs']) == len(analysis.runs)
    assert len(clone_json['predictors']) == len(analysis.predictors)


def test_put(auth_client, add_analysis, add_task, session):
    # Get analysis to edit
    analysis = Analysis.query.filter_by(id=add_analysis).first()
    analysis_json = decode_json(
        auth_client.get('/api/analyses/{}'.format(analysis.hash_id)))

    analysis_json['name'] = 'NEW NAME'

    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 200
    new_analysis = decode_json(resp)
    assert new_analysis['name'] == "NEW NAME"

    # Test adding a run_id
    analysis_json['runs'] = [Run.query.first().id]

    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 200
    new_analysis = decode_json(resp)
    assert new_analysis['runs'] == [Run.query.first().id]

    # Test adding an invalid run id
    analysis_json['runs'] = [9999]

    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 422
    assert 'runs' in decode_json(resp)['message']

    # Add and delete analysis
    # Add analysis
    test_analysis = {
        "dataset_id": add_task,
        "name": "some analysis",
        "description": "pretty damn innovative"
        }

    resp = auth_client.post('/api/analyses', data=test_analysis)
    analysis_json = decode_json(resp)

    # Test adding a run_id
    analysis_json['runs'] = [Run.query.first().id]

    resp = auth_client.put('/api/analyses/{}'.format(analysis_json['hash_id']),
                           data=analysis_json)
    assert resp.status_code == 200

    # Lock analysis
    analysis = Analysis.query.filter_by(hash_id=analysis_json['hash_id']).one()
    analysis.locked = True
    session.commit()

    # Try editing locked analysis
    analysis_json['description'] = "new!"

    resp = auth_client.put('/api/analyses/{}'.format(
        analysis_json['hash_id']),
                        data=analysis_json)
    assert resp.status_code == 422

    # Try deleting locked analysis
    delresp = auth_client.delete('/api/analyses/{}'.format(
        analysis_json['hash_id']))
    assert delresp.status_code == 422

    # Unlock and delete
    analysis.locked = False
    session.commit()

    # Try deleting anlaysis
    delresp = auth_client.delete('/api/analyses/{}'.format(
        analysis_json['hash_id']))
    assert delresp.status_code == 200
    assert Analysis.query.filter_by(
        hash_id=analysis_json['hash_id']).count() == 0


def test_autofill(auth_client, add_analysis, add_task, session):
    # Get analysis to edit
    analysis = Analysis.query.filter_by(id=add_analysis).first()
    analysis_json = decode_json(
        auth_client.get('/api/analyses/{}'.format(analysis.hash_id)))

    analysis_json['predictors'] = []
    analysis_json['runs'] = []

    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 200
    assert len(decode_json(resp)['predictors']) == 0
    assert len(decode_json(resp)['runs']) == 0

    resp = auth_client.post('/api/analyses/{}/fill'.format(analysis.hash_id),
                            data=analysis_json)
    assert resp.status_code == 200
    analysis_json = decode_json(resp)

    assert len(analysis_json['predictors']) == 2
    assert len(analysis_json['runs']) == 4
    assert analysis_json['model']['Input'] == {
        'Run': [1, 2], 'Subject': ['02', '01'], 'Task': ['bidstest']}

    # Try with names that don't exist
    analysis_json['model']['Steps'][0]["Model"]["X"] = \
        ["Brightness", "nonexistent"]
    analysis_json['predictors'] = []
    analysis_json['runs'] = []
    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 200

    # Partial fill should remove a predictor
    resp = auth_client.post('/api/analyses/{}/fill'.format(analysis.hash_id),
                            data=analysis_json,
                            params=dict(partial=True, dryrun=True))
    assert resp.status_code == 200
    analysis_json = decode_json(resp)

    assert len(analysis_json['predictors']) == 1
    assert len(analysis_json['model']['Steps'][0]["Model"]["X"]) == 1

    assert len(analysis_json['runs']) == 4

    # No partial fill - extra predictor remains in model
    resp = auth_client.post('/api/analyses/{}/fill'.format(analysis.hash_id),
                            data=analysis_json,
                            params=dict(partial=False, dryrun=True))
    assert resp.status_code == 200
    analysis_json = decode_json(resp)

    assert len(analysis_json['predictors']) == 1
    assert len(analysis_json['model']['Steps'][0]["Model"]["X"]) == 2
    assert len(analysis_json['runs']) == 4

    #

    # Try with names that don't exist
    analysis_json['model']['Steps'][0]["Model"]["X"] = \
        ["Brightness", "nonexistent"]
    analysis_json['model']['Steps'][0]["Transformations"].append(
              {
                "Name": "Scale",
                "Input": [
                  "nonexistent"
                ]
              }
        )

    analysis_json['predictors'] = []
    analysis_json['runs'] = []
    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=analysis_json)
    assert resp.status_code == 200
    assert len(decode_json(resp)['model']['Steps'][0]["Transformations"]) == 2

    # Partial fill should remove all transformations
    resp = auth_client.post('/api/analyses/{}/fill'.format(analysis.hash_id),
                            data=analysis_json,
                            params=dict(partial=True, dryrun=True))
    assert len(decode_json(resp)['model']['Steps'][0]["Transformations"]) == 0
    assert len(decode_json(resp)['model']['Steps'][0]["Contrasts"]) == 0


def test_reports(session, auth_client, add_analysis):
    analysis = Analysis.query.filter_by(id=add_analysis).first()

    # Create new Report
    r = Report(
        analysis_id=analysis.hash_id
        )
    session.add(r)
    session.commit()

    # Trigger report
    _ = report.generate_report(app, analysis.hash_id, r.id)

    # Get report
    resp = auth_client.get('/api/analyses/{}/report'.format(analysis.hash_id))
    assert resp.status_code == 200

    if decode_json(resp)['status'] != 'OK':
        print(decode_json(resp)['status'])
        print(decode_json(resp)['traceback'])
        assert 0

    result = decode_json(resp)['result']

    for f in ['design_matrix', 'design_matrix_corrplot', 'design_matrix_plot']:
        assert f in result

    assert len(result['design_matrix']) == 4


def test_compile(auth_client, add_analysis, add_analysis_fail):
    analysis = Analysis.query.filter_by(id=add_analysis).first()
    analysis_bad = Analysis.query.filter_by(id=add_analysis_fail).first()

    with pytest.raises(Exception):
        _ = report.compile(app, analysis_bad.hash_id)

    # Test status
    resp = auth_client.get('/api/analyses/{}/compile'.format(
        analysis_bad.hash_id))

    new_analysis = decode_json(resp)
    if new_analysis['status'] != 'FAILED':
        assert 0

    # Test getting bundle prior to compiling
    resp = auth_client.get('/api/analyses/{}/bundle'.format(analysis.hash_id))
    assert resp.status_code == 404

    # Test compiling
    _ = report.compile(app, analysis.hash_id)

    # Get full
    resp = auth_client.get('/api/analyses/{}'.format(analysis.hash_id))
    assert resp.status_code == 200
    locked_analysis = decode_json(resp)

    # Test editing status
    locked_analysis['private'] = False
    locked_analysis['new_name'] = "Should not change to this"
    resp = auth_client.put('/api/analyses/{}'.format(analysis.hash_id),
                           data=locked_analysis)
    assert resp.status_code == 200
    assert decode_json(resp)['private'] is False
    assert decode_json(resp)['name'] != "Should not change to this"

    # Test status after some time
    resp = auth_client.get('/api/analyses/{}/compile'.format(analysis.hash_id))
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
    analysis = Analysis.query.filter_by(id=add_analysis_user2).first()
    resp = auth_client.delete('/api/analyses/{}'.format(analysis.hash_id))

    assert resp.status_code == 404


def test_bibliography(auth_client, add_analysis, add_task, session):
    # Get analysis to edit
    analysis = Analysis.query.filter_by(id=add_analysis).first()
    bib_json = decode_json(
        auth_client.get('/api/analyses/{}/bibliography'.format(
            analysis.hash_id)))

    assert 'supporting' in bib_json
    assert "https://test.test.com/" in bib_json['data'][0]
    assert "Google Cloud Computing Services" in bib_json['extraction'][0]

    assert len([j['id'] for j in bib_json['csl_json']]) == 4
