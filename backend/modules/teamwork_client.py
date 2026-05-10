import requests
import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)


class TeamworkClient:
    def __init__(self, tenant_url: str, project_id: str, list_id: str, api_key: str = None):
        self.tenant_url = tenant_url.rstrip('/')
        self.project_id = project_id
        self.list_id = list_id
        self.api_key = api_key
        self.api_base = f"{self.tenant_url}/projects/api/v3"

        # Setup auth header - Teamwork uses Basic auth
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            # Teamwork API: Basic auth with apikey: (empty password)
            auth_string = base64.b64encode(f"{api_key}:".encode()).decode()
            self.headers['Authorization'] = f'Basic {auth_string}'

    def create_task(self, task_data: dict) -> dict:
        """
        Create a task in Teamwork.

        Args:
            task_data: {
                'title': str (required),
                'description': str (optional),
                'priority': 'low', 'medium', 'high', 'urgent' (optional),
                'due_date': ISO date string (optional),
                'tags': [str] (optional),
                'status': 'to_do', 'in_progress' (optional)
            }

        Returns:
            {'id': task_id, 'url': task_url, 'title': task_title}
        """

        title = task_data.get('title')
        if not title:
            raise ValueError("Task title is required")

        priority_map = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'urgent': 4
        }

        priority = task_data.get('priority', 'medium')
        # Priority should be a string enum, not numeric
        priority_value = priority  # Keep as string: low, medium, high, urgent

        payload = {
            'name': title,
            'description': task_data.get('description', ''),
        }

        if priority_value:
            payload['priority'] = priority_value

        if task_data.get('due_date'):
            payload['dueDate'] = task_data['due_date']

        if task_data.get('tags'):
            payload['tags'] = task_data['tags']

        logger.info(f"Creating task in Teamwork: {payload}")

        try:
            # Correct endpoint: /tasklists/{id}/tasks.json
            url = f"{self.api_base}/tasklists/{self.list_id}/tasks.json"
            logger.info(f"Posting to URL: {url}")
            logger.info(f"Payload: {payload}")

            response = requests.post(
                url,
                json={'task': payload},
                headers=self.headers,
                timeout=30
            )
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            task_id = result.get('id')
            task_url = f"{self.tenant_url}/tasks/{task_id}"

            logger.info(f"Task created successfully: {task_id}")

            return {
                'id': task_id,
                'url': task_url,
                'title': title
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create task in Teamwork: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            raise Exception(f"Teamwork API error: {str(e)}")

    def get_projects(self) -> list:
        """Get list of available projects."""
        try:
            url = f"{self.api_base}/projects"
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get('projects', [])
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise

    def get_lists(self, project_id: Optional[str] = None) -> list:
        """Get task lists for a project."""
        project = project_id or self.project_id
        try:
            url = f"{self.api_base}/projects/{project}/tasklists"
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get('tasklists', [])
        except Exception as e:
            logger.error(f"Failed to fetch task lists: {e}")
            raise
