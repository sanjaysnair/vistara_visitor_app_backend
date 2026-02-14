# Backend - Apartment Visitor Security System

FastAPI-based backend for managing visitor check-ins with email notifications.

## Setup

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 2. Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit `.env` file with your configuration:

```
DATABASE_URL=sqlite:///./apartment_security.db
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@apartment.com
```

### 4. Run the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - API info
- `POST /api/visitors` - Create new visitor entry
- `GET /api/visitors` - Get all visitors
- `GET /api/visitors/{id}` - Get specific visitor
- `DELETE /api/visitors/{id}` - Delete visitor
- `GET /api/stats` - Get statistics

## Database

Using SQLite for local development. Database file: `apartment_security.db`

## API Documentation

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`
# vistara_visitor_app_backend
