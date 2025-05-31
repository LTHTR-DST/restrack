# ResTrack - AI Agent Instructions

## Project Overview
ResTrack is a clinical results tracking portal that helps clinicians manage and track the status of medical investigations using worklists. The project has been migrated from Panel to a modern htmx-based frontend with FastAPI backend.

## Architecture

### Backend
- **FastAPI** (`restrack/api/api.py`) - REST API endpoints
- **SQLModel** - Database ORM for PostgreSQL/SQLite
- **Two databases**:
  - Local SQLite (`restrack.db`) - Application data (worklists, users, etc.)
  - Remote OMOP CDM database - Clinical order data

### Frontend
- **htmx** - Dynamic HTML updates without full page reloads
- **Bootstrap 5** - Responsive UI framework
- **Jinja2** - HTML templating
- **Vanilla JavaScript** - Client-side interactions

## Key Components

### Web Application (`restrack/web/`)
- `app.py` - Main FastAPI web app with HTML routes
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JavaScript, and assets
- `components/` - Reusable template components

### API (`restrack/api/`)
- `api.py` - REST API endpoints for data operations
- Mounted at `/api/v1` in the web app

### Models (`restrack/models/`)
- `worklist.py` - User, WorkList, OrderWorkList models
- `cdm.py` - OMOP CDM ORDER model for clinical data

## Development Setup

### Prerequisites
- Python 3.12+
- uv package manager
- SQLite (for local development)
- Access to OMOP CDM database (for production)

### Installation
```bash
# Install dependencies
uv sync

# Set up environment variables
cp sample.env .env
# Edit .env with your database connections
```

### Running the Application
```bash
# Start the API server (development)
uv run fastapi dev ./restrack/api/api.py

# Start the web frontend (development)
uv run fastapi dev --port 8001 ./restrack/web/app.py

# Alternative: Use the startup script
python run_web.py

# Or use VS Code task: "HTMX Web Development Server"
```

### Environment Configuration
Copy `sample.env` to `.env` and configure:
- `APP_DB_URL` - Local SQLite database path
- `REMOTE_DB_URL` - OMOP CDM database connection
- Other environment variables as needed

## Key Features Implemented

### Core Functionality
- **User Authentication** - Basic auth with JSON user store
- **Worklist Management** - Create, subscribe, copy, delete worklists
- **Order Management** - View, filter, and manage clinical orders
- **Status Tracking** - Update order status and add notes
- **Patient Search** - Find all orders for a specific patient
- **Admin Functions** - User management and worklist deletion

### UI Components
- **Responsive Design** - Works on desktop, tablet, mobile
- **Real-time Updates** - htmx for dynamic content loading
- **Interactive Tables** - Checkbox selection, sorting
- **Modal Dialogs** - For forms and confirmations
- **Alert System** - User feedback and error handling

## Development Guidelines

### Current Status
The project has been successfully migrated from Panel to htmx. Both UIs coexist:
- **htmx frontend** - Modern web application at port 8001 (primary)
- **Panel UI** - Legacy interface preserved in `restrack/ui/` (backup)

### Adding New Features
1. **API First** - Add REST endpoints in `restrack/api/api.py`
2. **Web Routes** - Add HTML routes in `restrack/web/app.py`
3. **Templates** - Create/update Jinja2 templates
4. **JavaScript** - Add client-side logic in `static/js/app.js`

### File Structure Patterns
```
restrack/
├── api/                   # FastAPI backend
│   └── api.py            # REST API endpoints
├── models/               # SQLModel database models
│   ├── worklist.py       # Application models
│   └── cdm.py           # OMOP CDM models
├── web/                  # htmx frontend
│   ├── app.py           # Main web application
│   ├── templates/
│   │   ├── base.html    # Base template with common layout
│   │   ├── dashboard.html # Main dashboard page
│   │   └── components/  # Reusable template components
│   └── static/
│       ├── css/style.css # Custom styles
│       └── js/app.js    # JavaScript functionality
├── ui/                   # Original Panel UI (preserved)
└── config.py            # Configuration management
```

### Key Conventions
- **htmx attributes** - Use `hx-get`, `hx-post`, etc. for dynamic updates
- **Component targets** - Use `hx-target` to specify update areas
- **Error handling** - Return alert HTML for user feedback
- **State management** - Use JavaScript globals for client state
- **Authentication** - All routes require basic auth (except logout)

## Database Schema

### Local Database (restrack.db)
- `user` - User accounts
- `worklist` - Clinical worklists
- `userworklist` - User subscriptions to worklists
- `orderworklist` - Orders assigned to worklists with status/notes

### Remote Database (OMOP CDM)
- `measurement` table - Clinical order data
- Read-only access for order retrieval

## Common Tasks

### Adding a New API Endpoint
1. Add route function in `restrack/api/api.py`
2. Define request/response models if needed
3. Add database operations using SQLModel
4. Test with FastAPI docs at `/docs`

### Adding a New Web Page
1. Create route in `restrack/web/app.py`
2. Create template in `templates/`
3. Add navigation links if needed
4. Test user authentication and authorization

### Adding htmx Interactions
1. Add `hx-*` attributes to HTML elements
2. Create corresponding web routes that return HTML fragments
3. Use `hx-target` to specify where content should be inserted
4. Add loading indicators and error handling

### Debugging Tips
- Use FastAPI docs at `/docs` and `/redoc` for API testing
- Check browser dev tools for htmx requests
- Use `print()` statements in Python for debugging
- Check database with SQLite browser for data issues

## Security Considerations
- Basic authentication for all routes
- SQL injection protection via SQLModel
- Input validation on all forms
- Admin-only routes protected by username check

## Performance Notes
- Database sessions properly closed
- htmx requests minimize data transfer
- Static files served efficiently
- Responsive design for mobile users

## Future Enhancements
- JWT token authentication
- Real-time notifications with WebSockets
- Advanced filtering and search
- Audit logging for clinical actions
- Integration with external clinical systems
- Role-based access control

## Troubleshooting

### Common Issues
1. **Database connection errors** - Check .env configuration
2. **Import errors** - Ensure uv dependencies are installed
3. **Template not found** - Check template paths and names
4. **htmx not working** - Verify JavaScript console for errors
5. **Authentication issues** - Check `data/users.json` file

### Development Tools
- **VS Code Tasks** - Configured for running servers
- **FastAPI Docs** - Auto-generated API documentation
- **Browser DevTools** - For frontend debugging
- **SQLite Browser** - For database inspection

## Contact & Support
This is a clinical application - ensure proper testing and validation before production use. Follow institutional guidelines for clinical software development and deployment.
