from ..request_utils import decode_json
from ...resources.predictor import prepare_upload
from ...tasks.upload import upload_collection
from ...core import app
from werkzeug.datastructures import FileStorage


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

    run_id = auth_client.get('/api/runs', params={'dataset_id': dataset_id})
    run_id = [r['id'] for r in run_id]

    resp = auth_client.get('/api/predictors', params={'run_id': run_id})
    assert resp.status_code == 200
    pred_select = decode_json(resp)
    assert type(pred_select) == list

    resp = auth_client.get('/api/predictors', params={'run_id': '123123'})
    assert resp.status_code == 200
    assert len(decode_json(resp)) == 0

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


def test_predictor_create(session,
                          auth_client, add_users, add_task, get_data_path):
    # Mock request to /predictors/create
    events = (get_data_path / 'bids_test' / 'sub-01' / 'func').glob('*.tsv')
    events = [FileStorage(stream=e.open('rb')) for e in events]

    (id_1, _), _ = add_users

    runs = []
    for i in ['1', '2']:
        resp = decode_json(
            auth_client.get(
                '/api/runs', params={'number': i}))
        r = [str(r['id']) for r in resp]
        runs.append(r)

    dataset_id = decode_json(
        auth_client.get('/api/datasets'))[0]['id']

    pc, filenames = prepare_upload(
        'new_one', events, runs, dataset_id
    )

    pc.user_id = id_1
    session.commit()

    descriptions = {
        "trial_type": "new_description"
    }

    # Submit to celery task
    results = upload_collection(app, filenames, runs, dataset_id, pc.id,
                                descriptions)
    assert results['status'] == 'OK'

    resp = auth_client.get(f'/api/predictors/collection/{pc.id}')
    assert resp.status_code == 200
    resp = decode_json(resp)

    assert resp['collection_name'] == 'new_one'
    assert len(resp['predictors']) == 3
    assert resp['status'] == 'OK'

    # Get predictor from API
    resp = decode_json(auth_client.get('/api/predictors/{}'.format(
        resp['predictors'][0]['id'])))
    assert resp['source'] == 'Collection: new_one'
    assert resp['name'] == 'trial_type'
    assert resp['description'] == 'new_description'

    # Test user PC route:
    resp = decode_json(auth_client.get('/api/user/predictors'))
    assert len(resp) == 3


def test_get_predictor_data(auth_client, add_task, extract_features):
    # List of predictors (includes both regular and extracted PEs)
    pids = [
        str(p['id']) for p in decode_json(auth_client.get('/api/predictors'))]

    resp = auth_client.get('/api/predictor-events',
                           params={'predictor_id': ",".join(pids)})

    assert resp.status_code == 200
    pe_list = decode_json(resp)
    assert len(pe_list) == 52

    pe = pe_list[0]
    # Get PEs only for one run
    resp = auth_client.get(
        '/api/predictor-events',
        params={'predictor_id': pe['predictor_id'], 'run_id': pe['run_id']})

    assert resp.status_code == 200
    pe_list_filt = decode_json(resp)
    assert len(pe_list_filt) == 4
