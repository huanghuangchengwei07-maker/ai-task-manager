# AI Task Manager

## Role Track
**AI/LLM Developer**

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: SQLite + ChromaDB (Vector Database)
- **AI/LLM**: OpenAI API (gpt-4o-mini, text-embedding-3-small) + Google AI (Gemini Pro)
- **Other**: Pydantic, SQLAlchemy

## Features Implemented

### Core Features
- [x] Task CRUD Operations (Create, Read, Update, Delete)
- [x] Task Properties (id, title, description, status, priority, tags, timestamps)
- [x] Data Persistence (SQLite)
- [x] Input Validation (Pydantic)
- [x] Error Handling

### AI Features
- [x] **Natural Language Task Creation** - Parse task information from natural language
- [x] **Automatic Tag Suggestion** - Intelligently suggest tags based on content
- [x] **Task Breakdown** - Break down complex tasks into subtasks
- [x] **Semantic Search** - Semantic search based on vector similarity
- [x] **Priority Recommendation** - Intelligently recommend task priority
- [x] **Multi-Provider Support** - Support for both OpenAI and Google AI with automatic fallback

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd task-ai-manager
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On Linux/Mac:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file and add your API keys:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   GOOGLE_AI_API_KEY=your-google-ai-api-key-here
   AI_PROVIDER=auto
   DATABASE_URL=sqlite:///./tasks.db
   CHROMA_PERSIST_DIR=./chroma_data
   ```
   
   **Note**: 
   - `AI_PROVIDER` can be `auto` (default, uses OpenAI first, falls back to Google AI), `openai`, or `google`
   - At least one API key is required. If both are provided, the system will automatically fallback if one fails.

### Running the Application

**Option 1: Using Python module (Recommended)**
```bash
python -m src.main
```

**Option 2: Using uvicorn directly**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
If you need to experiment with more AI features, considering that API key quotas are limited, you may need to configure your own API key.
The server will start on `http://localhost:8000`

### Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Documentation

### Task CRUD
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/tasks | Create a task |
| GET | /api/tasks | Get task list |
| GET | /api/tasks/{id} | Get a single task |
| PUT | /api/tasks/{id} | Update a task |
| DELETE | /api/tasks/{id} | Delete a task |

### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/ai/parse | Parse natural language |
| POST | /api/ai/parse-and-create | Parse and create task |
| POST | /api/ai/suggest-tags | Suggest tags |
| POST | /api/ai/breakdown | Break down task |
| POST | /api/ai/search | Semantic search |
| POST | /api/ai/recommend-priority | Recommend priority |

### Example: Natural Language Task Creation
```bash
curl -X POST "http://localhost:8000/api/ai/parse" \
  -H "Content-Type: application/json" \
  -d '{"text": "Remind me to have a meeting tomorrow at 3pm, it'\''s important"}'
```

Response:
```json
{
  "title": "Have a meeting",
  "description": null,
  "priority": "high",
  "due_date": "2026-02-01T15:00:00",
  "tags": ["work", "meeting"]
}
```

## Design Decisions

1. **FastAPI**: Modern async framework with built-in OpenAPI documentation and type hints
2. **SQLite + ChromaDB**: SQLite for reliable persistence, ChromaDB for vector search
3. **Multi-Provider AI**: Support for both OpenAI and Google AI with automatic fallback
4. **Service Layer Architecture**: Separation of AI services and business logic for easier testing and maintenance
5. **Graceful Degradation**: Fallback to keyword-based rules when AI providers fail

## Challenges & Solutions

1. **Natural Language Date Parsing**: Use LLM with current date context to handle relative dates (tomorrow, next week, etc.)
2. **Tag Consistency**: Limit tag scope and format through prompt engineering
3. **Vector Search Synchronization**: Synchronize vector database updates in CRUD operations
4. **API Quota Management**: Implemented fallback mechanism - when OpenAI API quota is exhausted, use keyword-based simple rules as backup
5. **Multi-Provider Support**: Automatic fallback from OpenAI to Google AI ensures service availability

## Future Improvements

- [ ] User authentication and multi-user support
- [ ] Task dependencies
- [ ] Similar task detection (avoid duplicates)
- [ ] Daily/weekly task summaries
- [ ] Local embedding models (reduce costs)
- [ ] Enhanced frontend interface
- [ ] Task templates
- [ ] Recurring tasks

## Time Spent
Approximately 3-4 hours

## License
MIT
