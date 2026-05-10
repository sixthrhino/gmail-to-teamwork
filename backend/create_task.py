#!/usr/bin/env python3
"""
Simple CLI tool to create Teamwork tasks from natural language commands.

Usage:
    python create_task.py "Create urgent task: review contract, due Friday"
    python create_task.py "important: follow up with client by tomorrow"
"""

import sys
import os
from dotenv import load_dotenv

from modules.claude_parser import ClaudeParser
from modules.teamwork_client import TeamworkClient
from modules.validators import validate_task_structure

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_task.py \"<natural language command>\"")
        print("\nExamples:")
        print('  python create_task.py "Create urgent task: review contract"')
        print('  python create_task.py "important: follow up by Friday"')
        print('  python create_task.py "add to backlog: refactor auth"')
        sys.exit(1)

    command = " ".join(sys.argv[1:])

    print(f"📝 Command: {command}\n")

    # Validate environment
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key or not claude_api_key.startswith('sk-'):
        print("❌ Error: CLAUDE_API_KEY not set in .env")
        sys.exit(1)

    teamwork_api_key = os.getenv('TEAMWORK_API_KEY')
    if not teamwork_api_key:
        print("❌ Error: TEAMWORK_API_KEY not set in .env")
        sys.exit(1)

    project_id = os.getenv('TEAMWORK_PROJECT_ID')
    list_id = os.getenv('TEAMWORK_LIST_ID')
    if not project_id or not list_id:
        print("❌ Error: TEAMWORK_PROJECT_ID or TEAMWORK_LIST_ID not set in .env")
        sys.exit(1)

    try:
        # Parse command with Claude
        print("🤖 Parsing command with Claude...")
        parser = ClaudeParser(api_key=claude_api_key)
        task_data = parser.parse(command, email_context={})

        print(f"   Title: {task_data.get('title')}")
        print(f"   Priority: {task_data.get('priority')}")
        print(f"   Due date: {task_data.get('due_date', 'Not set')}")
        print()

        # Validate
        print("✓ Validating task structure...")
        validate_task_structure(task_data)
        print("✓ Validation passed")
        print()

        # Create in Teamwork
        print("🌐 Creating task in Teamwork...")
        teamwork = TeamworkClient(
            tenant_url=os.getenv('TEAMWORK_TENANT_URL'),
            project_id=project_id,
            list_id=list_id,
            api_key=teamwork_api_key
        )

        result = teamwork.create_task(task_data)

        print(f"✅ Task created successfully!")
        print(f"\n📋 Task ID: {result['id']}")
        print(f"📝 Title: {result['title']}")
        print(f"🔗 URL: {result['url']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
