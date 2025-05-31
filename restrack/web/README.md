# ResTrack Web Frontend (HTMX)

This directory contains the new htmx-based web frontend for ResTrack, replacing the Panel-based UI.

## Architecture

- **FastAPI**: Backend web server and API endpoints
- **HTMX**: Dynamic frontend interactions without complex JavaScript
- **Bootstrap 5**: Modern, responsive UI framework
- **Jinja2**: Server-side templating

## Key Features

- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: HTMX provides seamless UI updates
- **Modular Components**: Reusable template components
- **Progressive Enhancement**: Works with JavaScript disabled

## File Structure

```
web/
├── app.py                 # Main FastAPI application
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # JavaScript functionality
└── templates/
    ├── base.html         # Base template
    ├── dashboard.html    # Main dashboard
    └── components/       # Reusable components
        ├── worklist_selector.html
        ├── orders_table.html
        ├── subscription_manager.html
        ├── copy_manager.html
        └── delete_manager.html
```

## Running the Web Frontend

### Development Server

Use the VS Code task "HTMX Web Development Server" or run manually:

```bash
python -m fastapi dev --port 8001 ./restrack/web/app.py
```

### Production

```bash
python run_web.py
```

## Key Differences from Panel UI

1. **Technology Stack**:
   - Panel + Bokeh → FastAPI + HTMX + Bootstrap

2. **State Management**:
   - Panel reactive parameters → JavaScript state + HTMX attributes

3. **Interactivity**:
   - Python callbacks → HTMX requests + JavaScript event handlers

4. **Styling**:
   - Panel components → Bootstrap components + custom CSS

## Authentication

Uses the same basic authentication as the original Panel app:
- Credentials stored in `data/users.json`
- Same username/password pairs

## API Integration

The web frontend uses the existing FastAPI backend at `/api/v1/` endpoints, ensuring compatibility with the existing data layer and business logic.

## Browser Support

- Modern browsers with JavaScript enabled
- Graceful degradation for older browsers
- Mobile-responsive design
