from src.utils.nfcore_utils import *

def test_get_pipelines_json():
    nfcore_obj = NfcoreUtils()
    pipeline_list = {}
    pipeline_list = nfcore_obj.get_pipelines_json()
    assert len(pipeline_list) == 1, "Nf-core endpoint failed"
    assert pipeline_list.get("remote_workflows", None)
    for i in pipeline_list.get("remote_workflows", None):
        assert i.get("name", None)

def test_get_pipelines():
    nfcore_obj = NfcoreUtils()
    pipeline_list = nfcore_obj.get_pipelines()
    assert len(pipeline_list) >  0, "Nf-core endpoint failed"
    for i in pipeline_list:
        assert i.name

