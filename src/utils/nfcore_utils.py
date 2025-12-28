import requests
from datetime import datetime

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


class RemoteWorkflowList:
    """A information container for a remote workflow.

    Args:
        data (dict): workflow information as they are retrieved from the GitHub repository REST API request
            (https://developer.github.com/v3/repos/#get).
    """

    def __init__(self, data):
        # Vars from the initial data payload
        self.name = data.get("name")
        self.full_name = data.get("full_name")
        self.description = data.get("description")
        self.topics = data.get("topics", [])
        self.archived = data.get("archived")
        self.stargazers_count = data.get("stargazers_count")
        self.watchers_count = data.get("watchers_count")
        self.forks_count = data.get("forks_count")

        # Placeholder vars for releases info (ignore pre-releases)
        self.releases = [r for r in data.get("releases", []) if r.get("published_at") is not None]

        # Placeholder vars for local comparison
        self.local_wf = None
        self.local_is_latest = None

        # Beautify date
        for release in self.releases:

            release["published_at_timestamp"] = int(
                datetime.strptime(release.get("published_at"), "%Y-%m-%dT%H:%M:%SZ").strftime("%s")
            )


class NfcoreUtils:

    def __init__(self):
        self.wf_list = []
        self.max_retry = 3

    def get_pipelines_json(self):
        """Retrieves remote workflows from `nf-co.re <https://nf-co.re>`_.

        Remote workflows are stored in :attr:`self.remote_workflows` list.
        """
        # List all repositories at nf-core
        retry = self.max_retry
        response = {}
        while retry > 0:
            try: 
                nfcore_url = "https://nf-co.re/pipelines.json"
                response = requests.get(nfcore_url, timeout=100)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error retrieving nf-core pipelines: HTTP {response.status_code}")
                    logger.info(f"Retrying for fetching data {retry}")
                    retry -= 1
                return response
            except requests.RequestException as e:
                logger.error(f"Error retrieving nf-core pipelines: {e}")
                retry -= 1
        return response


    def get_pipelines(self):
        """Retrieves remote workflows from `nf-co.re <https://nf-co.re>`_.

        Remote workflows are stored in :attr:`self.remote_workflows` list.
        """
        # List all repositories at nf-core
        retry = self.max_retry
        response = {}
        while retry > 0:
            try: 
                nfcore_url = "https://nf-co.re/pipelines.json"
                response = requests.get(nfcore_url, timeout=100)
                if response.status_code == 200:
                    repos = response.json()["remote_workflows"]
                    for repo in repos:
                        self.wf_list.append(RemoteWorkflowList(repo))
                    return self.wf_list
                retry -= 1
                return self.wf_list
            except requests.RequestException as e:
                logger.error(f"Error retrieving nf-core pipelines: {e}")
                retry -= 1
        return response