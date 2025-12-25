from src.utils.nfcore_utils import *

def test_get_pipelines_json():
    nfcore_obj = NfcoreUtils()
    pipeline_list = {}
    max_try = 3
    while max_try > 0:
        pipeline_list = nfcore_obj.get_pipelines_json()
        if len(pipeline_list) == 1:
            break
        max_try -= 1
        print("Failed to fetch, retrying nfcore utils")

    assert len(pipeline_list) == 1, "Nf-core endpoint failed"
    assert pipeline_list.get("remote_workflows", None)
    for i in pipeline_list.get("remote_workflows", None):
        assert i.get("name", None)

def test_get_pipelines():
    nfcore_obj = NfcoreUtils()
    max_try = 3
    while max_try > 0:
        pipeline_list = nfcore_obj.get_pipelines()
        if len(pipeline_list) >0:
            break
        max_try -= 1
        print("Failed to fetch, retrying nfcore utils")

    assert len(pipeline_list) >  0, "Nf-core endpoint failed"
    for i in pipeline_list:
        assert i.name

