import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

from modules.claude_parser import ClaudeParser
from modules.teamwork_client import TeamworkClient
from modules.validators import validate_task_structure

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

claude_parser = ClaudeParser(api_key=os.getenv('CLAUDE_API_KEY'))
teamwork_client = TeamworkClient(
    tenant_url=os.getenv('TEAMWORK_TENANT_URL'),
    api_key=os.getenv('TEAMWORK_API_KEY')
)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/analyze-email', methods=['POST'])
def analyze_email():
    try:
        data = request.json
        email_context = data.get('email', {})
        client_name = data.get('client_name')

        if not email_context:
            return jsonify({'success': False, 'error': 'Missing email context'}), 400

        if not client_name:
            return jsonify({'success': False, 'error': 'Missing client name'}), 400

        logger.info(f"Analyzing email for client: {client_name}")

        # Find project by company
        try:
            project = teamwork_client.find_project_by_company(client_name)
            logger.info(f"Found project: {project['name']} (Company: {project.get('company')})")
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404

        # Generate summary using Claude
        summary = claude_parser.summarize_issue(email_context)
        logger.info(f"Generated summary: {summary}")

        return jsonify({
            'success': True,
            'summary': summary,
            'project': project
        })

    except Exception as e:
        logger.error(f"Error analyzing email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/create-task', methods=['POST'])
def create_task():
    try:
        data = request.json
        command = data.get('command')
        email_context = data.get('email', {})
        client_name = data.get('client_name')
        project_id = data.get('project_id')  # Can be passed from analyze-email

        if not command:
            return jsonify({'success': False, 'error': 'Missing command'}), 400

        if not client_name and not project_id:
            return jsonify({'success': False, 'error': 'Missing client name or project ID'}), 400

        logger.info(f"Parsing command: {command}")
        logger.info(f"Client name: {client_name}")
        logger.info(f"Email context: {email_context}")

        # Find project by company if not provided
        if not project_id:
            try:
                project = teamwork_client.find_project_by_company(client_name)
                project_id = project['id']
                project_name = project['name']
                logger.info(f"Using project: {project_name} (ID: {project_id})")
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 404
        else:
            project_name = data.get('project_name', 'Unknown')

        task_structure = claude_parser.parse(command, email_context)
        logger.info(f"Parsed task structure: {task_structure}")

        validate_task_structure(task_structure)

        result = teamwork_client.create_task(task_structure, project_id=project_id)
        logger.info(f"Task created: {result['id']}")

        return jsonify({
            'success': True,
            'task_id': result['id'],
            'task_url': result['url'],
            'task_title': result['title'],
            'project_name': project_name,
            'message': f"Task created in {project_name}: {result['title']}"
        })

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return jsonify({'success': False, 'error': f"Failed to create task: {str(e)}"}), 500


@app.route('/parse-command', methods=['POST'])
def parse_command():
    try:
        data = request.json
        command = data.get('command')
        email_context = data.get('email', {})

        if not command:
            return jsonify({'success': False, 'error': 'Missing command'}), 400

        task_structure = claude_parser.parse(command, email_context)
        return jsonify({
            'success': True,
            'task_structure': task_structure
        })

    except Exception as e:
        logger.error(f"Error parsing command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
