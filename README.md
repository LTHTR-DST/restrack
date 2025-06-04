# ResTrack

Python application for results tracking

## Scope of MVP/PoC

### Logic

1. Identify user (admin)
2. Users create or subsrcibe to worklists
3. Worklists can contain 0 or more orders
4. Orders can belong to 0 or more worklists
5. Search using patient ID to find all orders - then pick the orders to add to the tracking worklist
6. Remove orders from worklist

### UI

1. Display list of orders and status - filter by worklist and other criteria

## Setup

_ToDo: Improve this section with better instructions on using [uv](https://docs.astral.sh/uv/) for managing all project dependencies._

1. Clone this repository
2. Create a new python environment e.g. `uv venv --python 3.12`
3. Activate the environment with `.venv/Scripts/activate`
4. Install project dependencies with `uv sync` (and use `uv add <package>` to add any dependencies)
5. Install pre-commit using `pre-commit install`
6. Copy the `sample.env` file to a new file called `.env` and setup the environment variables here.

__IMPORTANT:__ DO NOT SAVE ANY SENSITIVE INFORMATION TO VERSION CONTROL

## Development

The application is split into two main components:

- The _backend_ is implemented using [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/). Backend code resides in `restrack/api/`.
- The _frontend_ is a modern web application using [HTMX](https://htmx.org/), [Bootstrap 5](https://getbootstrap.com/), [Jinja2](https://jinja.palletsprojects.com/), and vanilla JavaScript. Frontend code is in `restrack/web/`.

This architecture provides a clear separation of concerns, maintainability, and a modern, responsive user experience.

### Application Database

ResTrack uses SQLite for ease of development but can be replaced with any SQLAlchemy-supported database. Sample data for populating the database is provided in `tests/synthetic_data`. A new SQLite database called `restrack.db` is created at first run.

### Development server

During development, start the web application server. This will create the database if it does not exist. _(ToDo: Automate populating the database with sample data)_.

This is configured as a [VS Code Task](https://code.visualstudio.com/docs/editor/tasks) in `.vscode/tasks.json`. If using a different IDE, run the command in a terminal session.

```json
{
    // See https://go.microsoft.com/fwlink/?LinkId=733558
    // for the documentation about the tasks.json format
    "version": "2.0.0",
    "tasks": [
        {
            "label": "HTMX Web Development Server",
            "type": "shell",
            "command": "python run_web.py",
            "problemMatcher": [
                "$python"
            ]
        }
    ]
}
```

## Key Technologies

- **FastAPI**: Backend API and HTML routes
- **SQLModel**: Database ORM
- **HTMX**: Dynamic HTML updates without full page reloads
- **Bootstrap 5**: Responsive UI framework
- **Jinja2**: HTML templating
- **Vanilla JavaScript**: Client-side logic

## Project Structure

```
restrack/
├── api/         # FastAPI backend (REST API)
├── models/      # SQLModel database models
├── web/         # HTMX frontend (routes, templates, static)
│   ├── app.py
│   ├── templates/
│   └── static/
├── config.py    # Configuration management
└── ...
```

## Features

- User authentication (JWT, secure cookies)
- Worklist management (create, subscribe, copy, delete)
- Order management (view, filter, update status, add notes)
- Patient search
- Admin functions (user management)
- Responsive, real-time UI with htmx
- Modal dialogs, alerts, and interactive tables

## Security

- JWT authentication for all routes (except login)
- HTTP-only cookies for token storage
- Input validation and SQL injection protection
- Admin-only routes protected

## Troubleshooting

- Use FastAPI docs at `/docs` and `/redoc` for API testing
- Check browser dev tools for htmx requests
- Use `print()` in Python for debugging
- Inspect database with SQLite browser
- Check `.env` for configuration issues

## Database Migrations (Alembic)

This project uses [Alembic](https://alembic.sqlalchemy.org/) for managing database schema migrations. Migration scripts are located in the `alembic/` directory. To create or apply migrations, use the Alembic CLI:

- Create a new migration after model changes:
  ```pwsh
  alembic revision --autogenerate -m "Describe your change"
  ```
- Apply migrations to the database:
  ```pwsh
  alembic upgrade head
  ```

See the `alembic/README.md` for more details.
