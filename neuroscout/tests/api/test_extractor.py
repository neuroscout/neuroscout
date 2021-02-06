from ..request_utils import decode_json


def test_get_dataset(auth_client, add_local_task_json):
    # List of datasets
    resp = auth_client.get('/api/extractors')
    assert resp.status_code == 200
    dataset_list = decode_json(resp)
    assert type(dataset_list) == list

    # Get first dataset
    assert 'description' in dataset_list[0]
    assert 'name' in dataset_list[0]

    assert len(dataset_list) > 20

    ext = [ext for ext in dataset_list if ext['name'] == 'RMSExtractor'][0]

    assert 'Extracts root mean square (RMS) from audio' in ext['description']