# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CV Maker is a full-stack job application tracking system with:
- **Backend**: FastAPI (Python) API server with SQLAlchemy ORM
- **Database**: PostgreSQL with `cv_maker_db` database
- **Frontend**: React with TypeScript + Vite + TailwindCSS
- **AI Features**: URL parsing with web scraping + Claude AI integration

Both backend and frontend are fully functional and integrated. The application provides a complete job application tracking interface with AI-powered job URL parsing.

## Development Environment

### Python Environment
- **Package Manager**: `uv` (modern Python package manager)
- **Python Version**: 3.13.5
- **Virtual Environment**: `.venv/` (managed by uv)
- **Key Dependencies**:
  - FastAPI 0.121.1, uvicorn
  - SQLAlchemy 2.0.44, psycopg2-binary
  - beautifulsoup4, requests (web scraping)
  - anthropic (Claude AI SDK)
  - python-dotenv (environment variables)

### Database
- **Type**: PostgreSQL
- **Database Name**: `cv_maker_db`
- **Connection String**: `postgresql://filipe@localhost/cv_maker_db` (configured in `backend/database.py`)
- **Schema**: `jobs` table (15 columns) with `application_status` enum
- **Enum Values**: `yet_to_apply`, `applied_waiting`, `job_offered`, `job_accepted`, `application_rejected`, `job_rejected`
- **Connection**: PostgreSQL server runs locally (check with `ps aux | grep postgres`)

### Frontend Environment
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 7.2.2
- **Styling**: TailwindCSS 3.x
- **HTTP Client**: Axios
- **Dev Server**: http://localhost:5173
- **Key Dependencies**: react, react-dom, typescript, vite, tailwindcss, axios

## Common Commands

### Backend Development

**Activate virtual environment:**
```bash
source .venv/bin/activate
```

**Run the FastAPI development server:**
```bash
cd backend
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`
Interactive API docs at `http://127.0.0.1:8000/docs`

**Install new dependencies (using uv):**
```bash
uv add <package-name>
```

**Run Python scripts in the environment:**
```bash
uv run python backend/main.py
```

### Frontend Development

**Install dependencies:**
```bash
cd frontend
npm install
```

**Run the Vite development server:**
```bash
cd frontend
npm run dev
```
The app will be available at `http://localhost:5173`
Hot module replacement (HMR) is enabled for fast development

**Build for production:**
```bash
cd frontend
npm run build
```

**Preview production build:**
```bash
cd frontend
npm run preview
```

**Install new dependencies:**
```bash
cd frontend
npm install <package-name>
```

### Database

**Connect to PostgreSQL:**
```bash
psql -d cv_maker_db
```

**Run migrations (once configured):**
```bash
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "description"
```

## Code Architecture

### Backend Structure

The backend follows a layered architecture pattern:

**`backend/main.py`** - FastAPI application entry point
- Defines all API routes and endpoints
- Handles HTTP request/response logic
- Uses dependency injection for database sessions
- API documentation available at `/docs` (Swagger UI)

**`backend/database.py`** - Database configuration
- SQLAlchemy engine setup
- Connection string: `postgresql://filipe@localhost/cv_maker_db`
- `SessionLocal`: Database session factory
- `get_db()`: Dependency function for route handlers
- `Base`: Declarative base for ORM models

**`backend/models.py`** - SQLAlchemy ORM models
- `ApplicationStatus`: Enum matching PostgreSQL enum type
- `Job`: ORM model for the `jobs` table with all 15 columns

**`backend/schemas.py`** - Pydantic schemas for validation
- `JobBase`: Base schema with all job fields
- `JobCreate`: Schema for creating jobs
- `JobUpdate`: Schema for updating jobs (partial updates supported)
- `JobResponse`: Schema for API responses (includes `id`)

**`backend/crud.py`** - Database operations
- `create_job()`: Insert new job application
- `get_job()`: Retrieve single job by ID
- `get_jobs()`: Retrieve all jobs with pagination
- `get_jobs_by_status()`: Filter jobs by status
- `get_jobs_by_company()`: Filter jobs by company (case-insensitive partial match)
- `update_job()`: Update existing job (partial updates)
- `delete_job()`: Delete job by ID

**`backend/job_parser.py`** - AI-powered job URL parsing
- `JobParser` class for extracting job details from URLs
- `fetch_page_content()`: Web scraping with BeautifulSoup
- `parse_basic_info()`: Extract job details using regex/heuristics
- `parse_with_llm()`: Use Claude AI to extract missing information
- `parse_job_url()`: Main method that combines scraping + AI
- Returns parsed data and list of missing fields

### API Endpoints

All endpoints follow RESTful conventions:

**Jobs Resource** (`/jobs`)
- `POST /jobs` - Create new job application (201 Created)
- `GET /jobs` - List all jobs with optional filters:
  - `?skip=N` - Pagination offset (default: 0)
  - `?limit=N` - Page size (default: 100, max: 1000)
  - `?status=STATUS` - Filter by application status
  - `?company=NAME` - Filter by company (partial match)
- `GET /jobs/{id}` - Get specific job by ID (404 if not found)
- `PUT /jobs/{id}` - Update job (partial updates supported, 404 if not found)
- `DELETE /jobs/{id}` - Delete job (204 No Content, 404 if not found)

**AI Features** (`/parse-job-url`)
- `POST /parse-job-url` - Parse job posting from URL
  - Request body: `{ "url": "https://...", "use_llm": true/false }`
  - Response includes parsed job data and missing_fields list
  - Uses web scraping + Claude AI (if API key provided)

**Utility Endpoints**
- `GET /` - API welcome message
- `GET /db-test` - Database connection health check

### Frontend Structure

The frontend follows a component-based architecture:

**`frontend/src/App.tsx`** - Main application component
- Manages global state (form visibility, editing state)
- Handles navigation between list and form views
- Coordinates data flow between components

**`frontend/src/components/JobList.tsx`** - Job listing component
- Displays all job applications in card format
- Implements filtering by status and company
- Handles job deletion with confirmation
- Triggers edit mode for selected jobs
- Shows loading and error states

**`frontend/src/components/JobForm.tsx`** - Job create/edit form
- Handles both create and update operations
- Form validation and error handling
- All 15 job fields supported
- Automatic form population when editing
- Status dropdown with all enum values

**`frontend/src/services/api.ts`** - API client service
- Axios-based HTTP client
- Configured for backend at `http://127.0.0.1:8000`
- Type-safe API methods:
  - `getJobs()` - List with filters
  - `getJob(id)` - Get single job
  - `createJob(data)` - Create new
  - `updateJob(id, data)` - Update existing
  - `deleteJob(id)` - Delete job
  - `testConnection()` - Health check

**`frontend/src/types/job.ts`** - TypeScript type definitions
- `ApplicationStatus` enum matching backend
- `Job` interface (complete job record)
- `JobCreate` interface (for new jobs)
- `JobUpdate` interface (for updates)

**Styling**
- TailwindCSS for all styling
- Responsive design (mobile-friendly)
- Status badges with color coding
- Form validation indicators

### Database Schema

**Table: `jobs`**
- `id` (integer, primary key, auto-increment)
- `role` (varchar 255)
- `company` (varchar 255)
- `department` (varchar 255)
- `opening_date` (date)
- `closing_date` (date)
- `application_date` (date)
- `last_update` (date)
- `status` (application_status enum)
- `url` (text)
- `cv` (text)
- `cover_letter` (text)
- `other_questions` (text)
- `location` (varchar 255)
- `salary` (varchar 255)
- `notes` (text)

## Current State & Next Steps

**Completed:**
- ✅ PostgreSQL database configured with `jobs` table and `application_status` enum
- ✅ FastAPI backend with complete CRUD API
- ✅ SQLAlchemy ORM integrated with PostgreSQL
- ✅ API documentation available at `/docs`
- ✅ React + TypeScript frontend with Vite
- ✅ TailwindCSS styling implemented
- ✅ Full CRUD UI (create, read, update, delete)
- ✅ Job filtering by status and company
- ✅ CORS configured for frontend-backend communication
- ✅ **AI-powered job URL parsing** (web scraping + Claude AI)
- ✅ Auto-fill form fields from job posting URLs
- ✅ Visual indicators for parsed/missing fields
- ✅ Both servers tested and working

**How to Run the Full Application:**
1. Start PostgreSQL (should already be running)
2. Start backend: `cd backend && uvicorn main:app --reload`
3. Start frontend: `cd frontend && npm run dev`
4. Access the application at http://localhost:5173

**Optional Future Enhancements:**
1. Add user authentication/authorization
2. Set up Alembic for database migrations
3. Add data export functionality (CSV, PDF)
4. Implement job application analytics/dashboard
5. Add email reminders for follow-ups
6. Deploy to production (Vercel/Railway/Heroku)

## Important Notes

**Backend:**
- The project uses `uv` instead of `pip`/`poetry`, so always use `uv add` for dependencies
- PostgreSQL must be running locally for database operations
- The `.venv` directory is managed by uv and should not be modified manually
- API auto-reloads on code changes when using `--reload` flag with uvicorn
- CORS is configured for `http://localhost:5173` and `http://localhost:5174` (Vite dev server)
- **AI Features Setup**: Create `backend/.env` file with `ANTHROPIC_API_KEY=your_key` to enable LLM-powered URL parsing
  - Without API key: Basic web scraping still works
  - With API key: Enhanced parsing using Claude AI for better accuracy

**Frontend:**
- Vite dev server runs on port 5173 by default
- Hot Module Replacement (HMR) enabled for instant updates
- TypeScript strict mode is enabled
- All API calls go through the centralized `api.ts` service
- TailwindCSS configuration is in `tailwind.config.js`

**Development Workflow:**
- Backend changes auto-reload with uvicorn's `--reload` flag
- Frontend changes auto-reload with Vite's HMR
- Database schema changes should be made directly in PostgreSQL (Alembic not yet configured)
- Both servers must be running for full functionality
