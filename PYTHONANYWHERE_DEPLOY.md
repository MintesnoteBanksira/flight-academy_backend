# Deploying Flight Academy API to PythonAnywhere

## Prerequisites
- PythonAnywhere account (free tier works for testing)
- Git repository with this backend code (optional)

## Step 1: Create PythonAnywhere Account
1. Go to https://www.pythonanywhere.com
2. Sign up for a free account (or paid for more features)
3. Note your username - it will be part of your API URL

## Step 2: Upload Code

### Option A: Using Git (Recommended)
1. Push your backend code to GitHub/GitLab
2. Open a Bash console on PythonAnywhere
3. Clone your repository:
   ```bash
   cd ~
   git clone https://github.com/yourusername/flight_academy_backend.git
   ```

### Option B: Manual Upload
1. Go to Files tab on PythonAnywhere
2. Create a new folder: `flight_academy_backend`
3. Upload all files manually

## Step 3: Create Virtual Environment
In PythonAnywhere Bash console:

```bash
cd ~/flight_academy_backend
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Configure Database

### Option A: SQLite (Simple, Good for Testing)
No additional setup needed - database file will be created automatically.

### Option B: PostgreSQL (Recommended for Production)
1. Go to Databases tab on PythonAnywhere
2. Create a new PostgreSQL database
3. Note down the connection details
4. Update your `.env` file:
   ```
   DATABASE_URL=postgresql+asyncpg://username:password@username-1234.postgres.pythonanywhere-services.com/database_name
   ```

## Step 5: Create .env File
In PythonAnywhere Bash console:

```bash
cd ~/flight_academy_backend
cp env.example.txt .env
nano .env
```

Update the values:
```
SECRET_KEY=generate-a-strong-random-key
DEBUG=False
DATABASE_URL=sqlite+aiosqlite:///./flight_academy.db
```

## Step 6: Initialize Database
```bash
cd ~/flight_academy_backend
source venv/bin/activate
python seed_data.py
```

## Step 7: Configure Web App

1. Go to Web tab on PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10

### Configure WSGI File
Click on the WSGI configuration file link and replace contents with:

```python
import sys
import os

# Add your project directory to the path
project_home = '/home/YOUR_USERNAME/flight_academy_backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./flight_academy.db'
os.environ['SECRET_KEY'] = 'your-secret-key-here'

# For FastAPI with ASGI
from app.main import app
```

### IMPORTANT: For FastAPI (ASGI)
PythonAnywhere's free tier only supports WSGI. To use FastAPI:

**Option 1: Use ASGI adapter (recommended)**
Add to WSGI file:
```python
from asgiref.wsgi import WsgiToAsgi

# At the end
application = WsgiToAsgi(app)
```

**Option 2: Upgrade to paid plan**
Paid plans support ASGI natively.

## Step 8: Configure Static Files
In Web tab, add:
- URL: `/uploads`
- Directory: `/home/YOUR_USERNAME/flight_academy_backend/uploads`

## Step 9: Reload Web App
Click the green "Reload" button in the Web tab.

## Step 10: Test Your API
Your API will be available at:
- `https://YOUR_USERNAME.pythonanywhere.com/`
- API Docs: `https://YOUR_USERNAME.pythonanywhere.com/docs`

## Test Endpoints
```bash
# Health check
curl https://YOUR_USERNAME.pythonanywhere.com/health

# API documentation
open https://YOUR_USERNAME.pythonanywhere.com/docs
```

## Troubleshooting

### Check Error Logs
In Web tab, click on "Error log" to see any issues.

### Database Issues
```bash
cd ~/flight_academy_backend
source venv/bin/activate
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"
```

### Permission Issues
```bash
chmod -R 755 ~/flight_academy_backend/uploads
```

## Updating Code
```bash
cd ~/flight_academy_backend
git pull  # if using git
source venv/bin/activate
pip install -r requirements.txt
# Reload web app from Web tab
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/signup | Register new user |
| POST | /api/v1/auth/login | Login (OAuth2) |
| POST | /api/v1/auth/login/json | Login (JSON body) |
| GET | /api/v1/users/me | Get current user |
| PATCH | /api/v1/users/me | Update profile |
| GET | /api/v1/videos | List videos |
| GET | /api/v1/videos/featured | Featured videos |
| GET | /api/v1/videos/{id} | Get video details |
| POST | /api/v1/videos | Upload video (instructor) |
| PATCH | /api/v1/videos/{id} | Update video (instructor) |
| DELETE | /api/v1/videos/{id} | Delete video (instructor) |
| GET | /api/v1/categories | List categories |
| POST | /api/v1/categories | Create category (instructor) |
