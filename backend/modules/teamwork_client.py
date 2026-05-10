import requests
import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)


class TeamworkClient:
    def __init__(self, tenant_url: str, api_key: str):
        self.tenant_url = tenant_url.rstrip('/')
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

    def create_task(self, task_data: dict, project_id: str) -> dict:
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
            project_id: Project ID to create task in (required)

        Returns:
            {'id': task_id, 'url': task_url, 'title': task_title}
        """

        title = task_data.get('title')
        if not title:
            raise ValueError("Task title is required")

        if not project_id:
            raise ValueError("Project ID is required")

        # Get first task list for the project
        list_id = self._get_default_tasklist(project_id)

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

        # Note: Tags will be added separately after task creation
        logger.info(f"Creating task in Teamwork: {payload}")

        try:
            # Correct endpoint: /tasklists/{id}/tasks.json
            url = f"{self.api_base}/tasklists/{list_id}/tasks.json"
            logger.info(f"Posting to URL: {url}")
            logger.info(f"Payload: {payload}")

            response = requests.post(
                url,
                json={'task': payload},
                headers=self.headers,
                timeout=30
            )
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            response.raise_for_status()

            result = response.json()
            logger.info(f"Parsed response: {result}")

            # Try different possible locations for task ID
            task_id = result.get('id') or result.get('task', {}).get('id')
            task_url = f"{self.tenant_url}/tasks/{task_id}"

            logger.info(f"Task created successfully: {task_id}")

            # Add tags if provided
            if task_data.get('tags') and task_id:
                self._add_tags_to_task(task_id, task_data['tags'])

            return {
                'id': task_id,
                'url': task_url,
                'title': title
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create task in Teamwork: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            raise Exception(f"Teamwork API error: {str(e)}")

    def _add_tags_to_task(self, task_id: str, tags: list):
        """Add tags to a task after creation."""
        try:
            # Teamwork API v3 expects PUT with tags array
            url = f"{self.api_base}/tasks/{task_id}/tags.json"

            # Send all tags in one request
            tag_payload = {'tags': [{'name': tag} for tag in tags]}

            response = requests.put(
                url,
                json=tag_payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 201, 204]:
                logger.info(f"Added {len(tags)} tags to task {task_id}")
            else:
                logger.warning(f"Failed to add tags: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error adding tags to task: {e}")
            # Don't fail the whole task creation if tags fail

    def _get_default_tasklist(self, project_id: str) -> str:
        """Get the first task list ID for a project."""
        try:
            url = f"{self.api_base}/projects/{project_id}/tasklists.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            lists = response.json().get('tasklists', [])

            if not lists:
                raise ValueError(f"No task lists found in project {project_id}")

            return lists[0]['id']
        except Exception as e:
            logger.error(f"Failed to fetch task lists: {e}")
            raise

    def get_projects(self) -> list:
        """Get list of available projects."""
        try:
            url = f"{self.api_base}/projects.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            logger.info(f"Get projects response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            return data.get('projects', [])
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise

    def find_project_by_company(self, client_name: str) -> dict:
        """Find project by matching company/client name (case-insensitive)."""
        projects = self.get_projects()
        client_lower = client_name.lower()

        for project in projects:
            # Check company name (fetch if we have company ID)
            company_id = project.get('companyId') or project.get('company', {}).get('id')
            company_name = 'N/A'

            if company_id:
                company_name = self._get_company_name(company_id)

            # Also check project name as fallback
            project_name = project.get('name', '').lower()

            if (company_name and (client_lower in company_name.lower() or company_name.lower() in client_lower) or
                client_lower in project_name or project_name in client_lower):
                logger.info(f"Found matching project: {project.get('name')} (Company: {company_name}, ID: {project.get('id')})")
                return {
                    'id': project.get('id'),
                    'name': project.get('name'),
                    'company': company_name
                }

        raise ValueError(f"No project found for client: {client_name}")

    def _get_company_name(self, company_id: int) -> str:
        """Fetch company name by ID."""
        try:
            url = f"{self.api_base}/companies/{company_id}.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('company', {}).get('name', 'N/A')
        except Exception as e:
            logger.error(f"Failed to fetch company name: {e}")
            return 'N/A'

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
