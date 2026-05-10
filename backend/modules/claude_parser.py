import json
import re
import logging
from datetime import datetime, timedelta
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class ClaudeParser:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"

    def summarize_issue(self, email_context: dict) -> str:
        """Generate a concise summary of the issue from email context."""

        email_preview = f"""
Email Context:
- From: {email_context.get('sender', 'unknown')}
- Subject: {email_context.get('subject', '(no subject)')}
- Date: {email_context.get('date', 'unknown')}
- Body: {email_context.get('body', '')[:500]}
"""

        prompt = f"""Analyze this email and provide a concise 2-3 sentence summary of the website issue being reported.

{email_preview}

Focus on:
- What is broken or not working
- Where on the website (if mentioned)
- Any error messages or symptoms

Return ONLY the summary text, no JSON or formatting."""

        try:
            logger.info("Calling Claude API to summarize issue...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Claude API call successful")

            summary = response.content[0].text.strip()
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize issue: {type(e).__name__}: {e}")
            # Fallback to basic summary
            return f"Issue reported in email: {email_context.get('subject', 'No subject')}"

    def parse(self, command: str, email_context: dict) -> dict:
        """
        Parse natural language command into task structure using Claude.

        Args:
            command: Natural language command (e.g., "Create urgent task: review by Friday")
            email_context: Email data {sender, subject, body, date, to, cc}

        Returns:
            dict with keys: title, description, priority, due_date, tags, status
        """

        email_preview = f"""
Email Context:
- From: {email_context.get('sender', 'unknown')}
- To: {email_context.get('to', 'unknown')}
- Subject: {email_context.get('subject', '(no subject)')}
- Date: {email_context.get('date', 'unknown')}
- Body Preview: {email_context.get('body', '')[:300]}
"""

        system_prompt = """You are a task parsing assistant for website issue tracking. Your job is to parse natural language commands and email context into structured Teamwork task data.

Parse the user's command and email context and return valid JSON (no markdown, just pure JSON) with these fields:
{
  "title": "concise task title (required)",
  "description": "clear description of the website issue with email context (REQUIRED)",
  "priority": "low, medium, high, or urgent (default: medium)",
  "due_date": "ISO format date like 2026-05-15, or null if not specified",
  "tags": ["list", "of", "tags"],
  "status": "to_do or in_progress (default: to_do)"
}

Rules:
- Title should be concise and action-oriented (e.g., "Fix broken contact form on homepage")
- Description is REQUIRED and must include:
  1. Clear summary of the issue reported
  2. Email context (From, Subject, Date)
  3. Relevant details from email body
- Format the description as:
  "Issue: [clear summary of what's broken/wrong]

  Details from client:
  [relevant details from email body]

  Email Context:
  From: [sender]
  Subject: [subject]
  Date: [date]"
- Infer priority from language: "urgent", "broken", "critical", "not working" -> high; "minor", "suggestion" -> low
- Tags: IMPORTANT - Automatically detect and add these keywords as tags if found in email subject or body:
  * "bug" - for bugs, defects, errors, issues
  * "defect" - for defects or broken features
  * "update" - for update requests or changes
  * "feature" - for feature requests
  * "enhancement" - for improvements
  * "performance" - for speed/performance issues
  * "security" - for security concerns
  * Also add any other relevant tags from the email (e.g., "payment", "form", "login", etc.)
- Parse relative dates: "Friday" -> next Friday, "ASAP" -> today, "tomorrow" -> tomorrow

Return ONLY valid JSON, no other text."""

        user_message = f"""Command: "{command}"

{email_preview}

Parse this command and return the task JSON structure."""

        try:
            logger.info("Calling Claude API...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                system=system_prompt
            )
            logger.info("Claude API call successful")
        except Exception as e:
            logger.error(f"Claude API call failed: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            raise Exception(f"Failed to call Claude API: {str(e)}")

        response_text = response.content[0].text.strip()

        try:
            task_data = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                task_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse Claude response: {response_text}")

        task_data = self._normalize_dates(task_data)
        task_data = self._set_defaults(task_data)

        return task_data

    def _normalize_dates(self, task_data: dict) -> dict:
        """Convert relative dates to ISO format."""
        due_date = task_data.get('due_date')

        if not due_date:
            return task_data

        if due_date.lower() == 'today':
            task_data['due_date'] = datetime.now().date().isoformat()
        elif due_date.lower() == 'tomorrow':
            task_data['due_date'] = (datetime.now() + timedelta(days=1)).date().isoformat()
        elif due_date.lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            task_data['due_date'] = self._next_weekday(due_date).isoformat()

        return task_data

    def _next_weekday(self, day_name: str) -> datetime.date:
        """Get the next occurrence of a weekday."""
        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        target_day = days[day_name.lower()]
        today = datetime.now()
        current_day = today.weekday()
        days_ahead = target_day - current_day

        if days_ahead <= 0:
            days_ahead += 7

        return (today + timedelta(days=days_ahead)).date()

    def _set_defaults(self, task_data: dict) -> dict:
        """Set default values for missing fields."""
        defaults = {
            'priority': 'medium',
            'status': 'to_do',
            'tags': []
        }

        for key, default_value in defaults.items():
            if key not in task_data or task_data[key] is None:
                task_data[key] = default_value

        return task_data
