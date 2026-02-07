# Deploying Flight Academy API to PythonAnywhere

## Your Configuration
- **Username**: `flightacademy`
- **Project folder**: `flight-academy_backend`
- **API URL**: `https://flightacademy.pythonanywhere.com`

---

## ✅ Step 1: Clone Repository (COMPLETED)
```bash
cd ~
git clone https://github.com/MintesnoteBanksira/flight-academy_backend.git
cd ~/flight-academy_backend
```

## ✅ Step 2: Create Virtual Environment (COMPLETED)
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Install Additional Dependencies
```bash
cd ~/flight-academy_backend
source venv/bin/activate
pip install aiofiles greenlet
```

---

## Step 4: Configure PostgreSQL Database

### 4.1 Create PostgreSQL Database
1. Go to **Databases** tab on PythonAnywhere
2. Set a PostgreSQL password (remember this!)
3. Click **"Initialize PostgreSQL"**
4. Wait for database to be created
5. Note the connection details shown:
   - **Host**: `flightacademy-1234.postgres.pythonanywhere-services.com`
   - **Database**: `flightacademy$default` (or create a new one)

### 4.2 Create a New Database (Optional but Recommended)
In the Databases tab, under "Create a database", enter:
- Database name: `flightacademy`
- Click "Create"

Your database will be: `flightacademy$flightacademy`

---

## Step 5: Create .env File
In PythonAnywhere Bash console:

```bash
cd ~/flight-academy_backend
cp env.example.txt .env
nano .env
```

Update with these values (replace YOUR_POSTGRES_PASSWORD):
```
APP_NAME=Flight Academy API
APP_VERSION=1.0.0
DEBUG=False

SECRET_KEY=your-super-secret-key-generate-random-string-here

# PostgreSQL Database (RECOMMENDED)
DATABASE_URL=postgresql+asyncpg://flightacademy:YOUR_POSTGRES_PASSWORD@flightacademy-1234.postgres.pythonanywhere-services.com/flightacademy$flightacademy

# Alternative: SQLite (simpler but less robust)
# DATABASE_URL=sqlite+aiosqlite:////home/flightacademy/flight-academy_backend/flight_academy.db

UPLOAD_DIR=/home/flightacademy/flight-academy_backend/uploads
```

**To generate a random secret key**, run:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 6: Create Uploads Directory
```bash
mkdir -p ~/flight-academy_backend/uploads/videos
mkdir -p ~/flight-academy_backend/uploads/thumbnails
chmod -R 755 ~/flight-academy_backend/uploads
```

---

## Step 7: Initialize Database
```bash
cd ~/flight-academy_backend
source venv/bin/activate
python seed_data.py
```

This creates test accounts:
- **Instructor**: captain@flightacademy.com / password123
- **Student**: student@flightacademy.com / password123
- **Admin**: admin@flightacademy.com / admin123

---

## Step 8: Configure Web App

### 8.1 Create Web App
1. Go to **Web** tab on PythonAnywhere
2. Click **"Add a new web app"**
3. Click "Next" (use flightacademy.pythonanywhere.com)
4. Choose **"Manual configuration"**
5. Select **Python 3.10**

### 8.2 Configure Virtualenv
In Web tab, under "Virtualenv":
- Enter: `/home/flightacademy/flight-academy_backend/venv`
- Click the checkmark

### 8.3 Configure WSGI File
Click on the WSGI configuration file link:
`/var/www/flightacademy_pythonanywhere_com_wsgi.py`

**Delete all contents** and replace with:

```python
import sys
import os

# Add project directory to path
project_home = '/home/flightacademy/flight-academy_backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import the FastAPI app
from app.main import app

# ASGI to WSGI adapter for PythonAnywhere
from asgiref.wsgi import WsgiToAsgi

# This is what PythonAnywhere looks for
application = WsgiToAsgi(app)
```

### 8.4 Install asgiref
In Bash console:
```bash
cd ~/flight-academy_backend
source venv/bin/activate
pip install asgiref
```

---

## Step 9: Configure Static Files
In Web tab, under "Static files":
- URL: `/uploads`
- Directory: `/home/flightacademy/flight-academy_backend/uploads`

Click the checkmark to save.

---

## Step 10: Reload Web App
Click the big green **"Reload flightacademy.pythonanywhere.com"** button.

---

## Step 11: Test Your API

Your API is now live at:
- **Main URL**: https://flightacademy.pythonanywhere.com/
- **API Docs**: https://flightacademy.pythonanywhere.com/docs
- **Health Check**: https://flightacademy.pythonanywhere.com/health

### Test with curl:
```bash
# Health check
curl https://flightacademy.pythonanywhere.com/health

# Get categories
curl https://flightacademy.pythonanywhere.com/api/v1/categories

# Get videos
curl https://flightacademy.pythonanywhere.com/api/v1/videos
```

---

## Troubleshooting

### Check Error Logs
In Web tab, click on **"Error log"** to see any issues.

### Common Issues

#### 1. "No module named 'app'"
Make sure the project path is correct in WSGI file:
```python
project_home = '/home/flightacademy/flight-academy_backend'
```

#### 2. Database Connection Failed
- Check your PostgreSQL password in .env
- Make sure the database host matches what's shown in Databases tab
- For SQLite, use absolute path: `sqlite+aiosqlite:////home/flightacademy/...` (4 slashes!)

#### 3. "greenlet" or "aiofiles" not found
```bash
cd ~/flight-academy_backend
source venv/bin/activate
pip install greenlet aiofiles
```
Then reload the web app.

#### 4. Permission Issues
```bash
chmod -R 755 ~/flight-academy_backend/uploads
```

---

## Updating Code
```bash
cd ~/flight-academy_backend
git pull
source venv/bin/activate
pip install -r requirements.txt
# Then reload web app from Web tab
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
