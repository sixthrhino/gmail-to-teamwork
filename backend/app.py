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
    project_id=os.getenv('TEAMWORK_PROJECT_ID'),
    list_id=os.getenv('TEAMWORK_LIST_ID'),
    api_key=os.getenv('TEAMWORK_API_KEY')
)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/create-task', methods=['POST'])
def create_task():
    try:
        data = request.json
        command = data.get('command')
        email_context = data.get('email', {})

        if not command:
            return jsonify({'success': False, 'error': 'Missing command'}), 400

        logger.info(f"Parsing command: {command}")
        logger.info(f"Email context: {email_context}")

        task_structure = claude_parser.parse(command, email_context)
        logger.info(f"Parsed task structure: {task_structure}")

        validate_task_structure(task_structure)

        result = teamwork_client.create_task(task_structure)
        logger.info(f"Task created: {result['id']}")

        return jsonify({
            'success': True,
            'task_id': result['id'],
            'task_url': result['url'],
            'task_title': result['title'],
            'message': f"Task created: {result['title']}"
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
