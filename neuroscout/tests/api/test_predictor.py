from tests.request_utils import decode_json
def test_get_predictor(auth_client, extract_features):
    # List of predictors
    resp = auth_client.get('/api/predictors')
    assert resp.status_code == 200
    pred_list = decode_json(resp)
    assert type(pred_list) == list

    # Get RT predictors
    pred_id = [p for p in pred_list if p['name'] == 'rt'][0]['id']
    assert 'name' in pred_list[0]

    # Check that derivative event is in there
    assert len([p for p in pred_list if p['name'] == 'rating']) > 0

    rv = auth_client.get('/api/predictors/{}'.format(pred_id))
    assert rv.status_code == 200
    pred = decode_json(rv)
    assert pred_id == pred['id']
    assert pred['run_statistics'][0]['mean'] == 167.25

    # Try getting nonexistent predictor
    resp = auth_client.get('/api/predictors/{}'.format('123'))
    assert resp.status_code == 404

    # Test parameters
    ds = decode_json(
        auth_client.get('/api/datasets'))
    dataset_id = ds[0]['id']
    run_id = str(ds[0]['runs'][0]['id'])

    resp = auth_client.get('/api/predictors', params={'run_id' : run_id})
    assert resp.status_code == 200
    pred_select = decode_json(resp)
    assert type(pred_select) == list

    resp = auth_client.get('/api/predictors', params={'run_id' : '123123'})
    assert resp.status_code == 200
    assert len(decode_json(resp)) == 0

    # Test filtering by dataset
    resp = auth_client.get('/api/predictors', params={'dataset_id' : dataset_id})
    assert resp.status_code == 200
    pred_select = decode_json(resp)
    assert type(pred_select) == list
    assert len(pred_select) == 4

    # Test filtering by multiple parameters
    resp = auth_client.get('/api/predictors', params={'name': 'rt',
        'run_id': run_id})
    assert resp.status_code == 200
    pred_p = decode_json(resp)
    assert len(pred_p) == 1
    assert 'extracted_feature' not in pred_p[0]
    assert pred_p[0]['source'] == 'event'

    # Test extracted_feature
    resp = auth_client.get('/api/predictors', params={'name': 'Brightness',
        'run_id': run_id})
    assert resp.status_code == 200
    pred_p = decode_json(resp)
    assert 'extracted_feature' in pred_p[0]
    assert pred_p[0]['extracted_feature']['description'] == 'Brightness of an image.'
    assert pred_p[0]['source'] == 'extracted'
    assert pred_p[0]['modality'] == 'image'


def test_get_rextracted(auth_client, reextract):
    run_id = decode_json(
        auth_client.get('/api/runs', params={'number' : '1', 'subject': '01'}))[0]['id']
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
    resp = auth_client.get('/api/predictor-events',
                           params={'predictor_id' : pe['predictor_id'],
                                 'run_id' : pe['run_id']})

    assert resp.status_code == 200
    pe_list_filt = decode_json(resp)
    assert len(pe_list_filt) == 4
