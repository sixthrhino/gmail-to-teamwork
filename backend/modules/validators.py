from datetime import datetime


def validate_task_structure(task_data: dict) -> None:
    """
    Validate that task data has required fields and valid formats.

    Raises:
        ValueError if validation fails
    """

    if not task_data.get('title') or not task_data['title'].strip():
        raise ValueError("Task title is required and cannot be empty")

    title = task_data.get('title', '')
    if len(title) > 500:
        raise ValueError("Task title cannot exceed 500 characters")

    description = task_data.get('description') or ''
    if len(description) > 5000:
        raise ValueError("Task description cannot exceed 5000 characters")

    priority = task_data.get('priority', 'medium')
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if priority not in valid_priorities:
        raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")

    status = task_data.get('status', 'to_do')
    valid_statuses = ['to_do', 'in_progress']
    if status not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

    if task_data.get('due_date'):
        try:
            datetime.fromisoformat(task_data['due_date'])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid due_date format: {task_data['due_date']}. Use ISO format (YYYY-MM-DD)")

    if task_data.get('tags'):
        tags = task_data.get('tags') or []
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")
        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
