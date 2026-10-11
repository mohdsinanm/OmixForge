import requests
import time
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
        """Initialize RemoteWorkflowList with GitHub API workflow data.
        
        Parameters
        ----------
        data : dict
            Workflow information from GitHub repository REST API.
        """
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
        """Initialize NfcoreUtils with empty workflow list and retry settings."""
        self.wf_list = []
        self.max_retry = 3

    def get_pipelines_json(self):
        """Retrieves remote workflows from `nf-co.re <https://nf-co.re>`_.

        Remote workflows are stored in :attr:`self.remote_workflows` list.
        """
        # List all repositories at nf-core
        nfcore_url = "https://nf-co.re/pipelines.json"
        last_error = None
        for attempt in range(1, self.max_retry + 1):
            try: 
                response = requests.get(nfcore_url, timeout=20)
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as exc:
                        last_error = f"The nf-core API returned invalid JSON: {exc}"
                else:
                    last_error = f"nf-core API returned HTTP {response.status_code}"
                    if response.status_code != 429 and response.status_code < 500:
                        raise RuntimeError(last_error)
            except requests.RequestException as e:
                last_error = str(e)

            logger.warning(
                f"Error retrieving nf-core pipelines (attempt {attempt}/{self.max_retry}): {last_error}"
            )
            if attempt < self.max_retry:
                time.sleep(min(2 ** (attempt - 1), 4))

        raise RuntimeError(
            f"Could not load workflows from nf-core after {self.max_retry} attempts: {last_error}. "
            "Check your network connection and try refreshing again."
        )


    def get_pipelines(self):
        """Retrieves remote workflows from `nf-co.re <https://nf-co.re>`_.

        Remote workflows are stored in :attr:`self.remote_workflows` list.
        """
        payload = self.get_pipelines_json()
        repos = payload.get("remote_workflows") if isinstance(payload, dict) else None
        if not isinstance(repos, list):
            raise RuntimeError("The nf-core API response did not include a workflow list.")

        self.wf_list = [RemoteWorkflowList(repo) for repo in repos]
        return self.wf_list