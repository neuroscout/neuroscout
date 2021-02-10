from ..request_utils import decode_json


def test_extractor_desc(auth_client, add_local_task_json):
    # List of datasets
    resp = auth_client.get('/api/extractors')
    assert resp.status_code == 200
    ext_list = decode_json(resp)
    assert type(ext_list) == list

    # Get first dataset
    assert 'description' in ext_list[0]
    assert 'name' in ext_list[0]

    assert len(ext_list) > 2

    ext = [ext for ext in ext_list if ext['name'] == 'BrightnessExtractor'][0]

    assert 'average luminosity of the pixels' in ext['description']