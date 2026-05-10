# Gmail to Teamwork Task Automation

Create Teamwork tasks directly from Gmail using natural language commands powered by Claude AI.

## Quick Start

### 1. Create Python Virtual Environment

```bash
cd backend

# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

### 2. Backend Setup

```bash
# Copy env template
cp .env.example .env

# Edit .env with your values
nano .env
```

Required environment variables:
- `CLAUDE_API_KEY`: Your Anthropic API key (get from https://console.anthropic.com)
- `TEAMWORK_TENANT_URL`: Your Teamwork tenant (e.g., https://sixthrhino.teamwork.com)
- `TEAMWORK_PROJECT_ID`: Teamwork project ID
- `TEAMWORK_LIST_ID`: Teamwork task list ID

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Backend Locally

```bash
python app.py
```

Backend starts at `http://localhost:5000`

### 5. Deploy Gmail Add-on

1. Go to [Google Apps Script](https://script.google.com)
2. Create new project: `New project`
3. Copy files from `addon/` folder:
   - `appsscript.json` → Project settings
   - `sidebar.html` → New file named `sidebar.html`
   - `code.gs` → Main code editor
4. Deploy → Deploy as add-on
5. Select Gmail add-on type
6. Install for yourself

### 6. Test

1. Open Gmail
2. Open an email
3. Look for "📋 Create Teamwork Task" in the sidebar
4. Type: `"Create urgent task: review contract, due Friday"`
5. Click "Create Task"
6. Task appears in Teamwork!

## Usage Examples

**Simple task:**
```
review invoice
```

**With priority:**
```
urgent: follow up on proposal
```

**With due date:**
```
important: schedule meeting with client, due Friday
```

**With context:**
```
high priority task: respond to contractor about timeline
```

## Docker Deployment

Build:
```bash
docker build -t gmail-to-teamwork .
```

Run:
```bash
docker run -p 5000:5000 \
  -e CLAUDE_API_KEY=sk-... \
  -e TEAMWORK_TENANT_URL=https://sixthrhino.teamwork.com \
  -e TEAMWORK_PROJECT_ID=... \
  -e TEAMWORK_LIST_ID=... \
  gmail-to-teamwork
```

## Virtual Environment

When done working, deactivate the virtual environment:
```bash
deactivate
```

To activate again later:
```bash
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

## API Endpoints

### POST /create-task
Create a task from natural language command.

Request:
```json
{
  "command": "Create urgent task: review contract, due Friday",
  "email": {
    "subject": "Contract Review",
    "sender": "john@example.com",
    "body": "Please review the attached contract",
    "date": "2026-05-09T10:00:00Z"
  }
}
```

Response:
```json
{
  "success": true,
  "task_id": "123456",
  "task_url": "https://sixthrhino.teamwork.com/tasks/123456",
  "task_title": "Review contract",
  "message": "Task created: Review contract"
}
```

### GET /health
Check backend health.

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-05-09T10:00:00.000000"
}
```

## Troubleshooting

**"Connection failed" in Gmail:**
- Ensure backend is running: `python app.py`
- Check CORS settings (should allow localhost:5000)
- Verify `BACKEND_URL` in sidebar.html matches your setup

**Claude API errors:**
- Check `CLAUDE_API_KEY` is valid
- Verify API key has sufficient quota

**Teamwork API errors:**
- Verify `TEAMWORK_PROJECT_ID` and `TEAMWORK_LIST_ID` are correct
- Check if API user has permission to create tasks
- Ensure task list exists in project

**Gmail Add-on not showing:**
- Refresh Gmail (Ctrl+R or Cmd+R)
- Check that add-on was deployed successfully
- Try in Incognito mode (cache issues)

## Architecture

```
Gmail UI (sidebar.html)
    ↓ (natural language command)
Flask Backend (app.py)
    ├→ Claude Parser (claude_parser.py)
    │   └→ Claude API (parse intent)
    └→ Teamwork Client (teamwork_client.py)
        └→ Teamwork API (create task)
```

## Development

**Run tests:**
```bash
pytest
```

**Debug mode:**
```bash
FLASK_DEBUG=1 python app.py
```

**Check backend health:**
```bash
curl http://localhost:5000/health
```

**Test command parsing (dry-run):**
```bash
curl -X POST http://localhost:5000/parse-command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Create urgent task: review",
    "email": {"subject": "test", "sender": "test@example.com"}
  }'
```
