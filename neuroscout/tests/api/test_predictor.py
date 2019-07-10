from ..request_utils import decode_json
import pytest
import os


def test_get_predictor(auth_client, extract_features):
    # List of predictors
    resp = auth_client.get('/api/predictors')
    assert resp.status_code == 200
    pred_list = decode_json(resp)
    assert type(pred_list) == list

    # Get RT predictors
    rt = [p for p in pred_list if p['name'] == 'rt'][0]
    assert 'name' in rt
    assert rt['description'] == "How long it takes to react!"
    pred_id = rt['id']

    # Check that derivative event is in there
    assert len([p for p in pred_list if p['name'] == 'rating']) > 0

    rv = auth_client.get('/api/predictors/{}'.format(pred_id))
    assert rv.status_code == 200
    pred = decode_json(rv)
    assert pred_id == pred['id']

    # Try getting nonexistent predictor
    resp = auth_client.get('/api/predictors/{}'.format('123'))
    assert resp.status_code == 404

    # Test parameters
    ds = decode_json(
        auth_client.get('/api/datasets'))
    dataset_id = ds[0]['id']
    run_id = str(ds[0]['runs'][0])

    resp = auth_client.get('/api/predictors', params={'run_id': run_id})
    assert resp.status_code == 200
    pred_select = decode_json(resp)
    assert type(pred_select) == list

    resp = auth_client.get('/api/predictors', params={'run_id': '123123'})
    assert resp.status_code == 200
    assert len(decode_json(resp)) == 0

    # Test filtering by dataset
    resp = auth_client.get(
        '/api/predictors', params={'dataset_id': dataset_id})
    assert resp.status_code == 200
    pred_select = decode_json(resp)
    assert type(pred_select) == list
    assert len(pred_select) == 4

    # Test filtering by multiple parameters
    resp = auth_client.get(
        '/api/predictors', params={'name': 'rt', 'run_id': run_id})
    assert resp.status_code == 200
    pred_p = decode_json(resp)
    assert len(pred_p) == 1
    assert 'extracted_feature' not in pred_p[0]
    assert pred_p[0]['source'] == 'events'

    # Test extracted_feature
    resp = auth_client.get(
        '/api/predictors', params={'name': 'Brightness', 'run_id': run_id})
    assert resp.status_code == 200
    pred_p = decode_json(resp)
    assert 'extracted_feature' in pred_p[0]
    assert pred_p[0]['extracted_feature']['description'] == \
        'Brightness of an image.'
    assert pred_p[0]['source'] == 'extracted'
    assert pred_p[0]['extracted_feature']['modality'] == 'image'


def test_get_rextracted(auth_client, reextract):
    run_id = decode_json(
        auth_client.get(
            '/api/runs', params={'number': '1', 'subject': '01'}))[0]['id']
    resp = auth_client.get('/api/predictors', params={
        'run_id': run_id, 'newest': 'false'})
    assert len(decode_json(resp)) == 5


def test_get_predictor_data(auth_client, add_task):
    # List of predictors
    resp = auth_client.get('/api/predictor-events')
    assert resp.status_code == 200
    pe_list = decode_json(resp)
    assert len(pe_list) == 36

    pe = pe_list[0]
    # Get PEs only for one run
    resp = auth_client.get(
        '/api/predictor-events',
        params={'predictor_id': pe['predictor_id'], 'run_id': pe['run_id']})

    assert resp.status_code == 200
    pe_list_filt = decode_json(resp)
    assert len(pe_list_filt) == 4


@pytest.mark.skipif('CELERY_BROKER_URL' not in os.environ,
                    reason="requires redis")
def test_predictor_create(auth_client, add_task, get_data_path):
    events = (get_data_path / 'bids_test' / 'sub-01' / 'func').glob('*.tsv')
    events = [e.open('rb') for e in events]

    runs = []
    for i in ['1', '2']:
        resp = decode_json(
            auth_client.get(
                '/api/runs', params={'number': i}))
        r = ','.join([str(r['id']) for r in resp])
        runs.append(r)

    dataset_id = decode_json(
        auth_client.get('/api/datasets'))[0]['id']

    # Test extracted_feature
    resp = auth_client.post(
        '/api/predictors/collection',
        data={
            'collection_name': 'new_one',
            'dataset_id': dataset_id,
            'event_files': [events[0], events[1]],
            'runs': runs
            },
        content_type='multipart/form-data',
        json_dump=False
        )
    assert resp.status_code == 200
    resp = decode_json(resp)
    assert resp['collection_name'] == 'new_one'
    assert resp['status'] == 'PENDING'

    # Can't test for anything more because db is not written by Flask here
    # So Celery can't see the task that is created
