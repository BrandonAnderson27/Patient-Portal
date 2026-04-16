# Patient Portal System

## Requirements

Make sure you have the correct Python version installed.

Check your Python version:

```bash
python --version
```

Required:

- Python 3.12+
- PostgreSQL installed and running locally

---

## Installation

Clone the repository:

```
git clone https://github.com/your-username/patient-portal.git
cd patient-portal
```

---

## Environment Configuration

This project uses environment variables (via python-decouple) for sensitive settings like the secret key and database credentials.

Create a .env file in the root of hte project directory that contains this: 

```
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_NAME=postgres
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

To generate a secure Django secret key, run this command: 

```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Paste that key into .env

To create a new database in PostgreSQL:

```bash
psql -U postgres
CREATE DATABASE patient_portal;
\q
```

Paste the name of the database into .env

---

## Setup Virtual Environment

Create a virtual environment inside the project directory.

### Windows

Create environment:

```bash
python -m venv venv
```

Activate environment:

#### Windows (Command Prompt)

```bash
venv\Scripts\activate
```

#### Windows (PowerShell)

```powershell
venv\Scripts\Activate.ps1
```

---

### macOS / Linux

Create environment:

```bash
python3 -m venv venv
```

Activate environment:

```bash
source venv/bin/activate
```

---

After activation, you should see:

```
(venv)
```

---

## Install Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

---

## Verify Installed Versions

Check installed dependencies:

```bash
pip list
```

---

## Apply Database Migrations

Create required database tables:

```bash
python manage.py migrate
```

---

## Seed Test Data

Populate the database with test accounts:

```bash
python manage.py seed
```

Test accounts created:

| Role         | Username         | Password     |
|--------------|------------------|--------------|
| Patient      | testpatient      | testpass123  |
| Provider     | testprovider     | testpass123  |
| Receptionist | testreceptionist | testpass123  |
| Lab Staff    | testlabstaff     | testpass123  |
| Admin        | testadmin        | testpass123  |

---

## Run Development Server

Start the Django server:

```bash
python manage.py runserver
```

Open your browser:
```
http://127.0.0.1:8000/
```

---

## Project Structure

```
Patient-Portal/
├── accounts/          # User auth, roles, dashboards, messaging
├── labs/              # Lab requests and results
├── manage.py
└── requirements.txt
```

---

## Notes

- The admin account can approve patient registrations from the admin dashboard
- All role-based dashboards are protected — users are redirected if they access the wrong dashboard
- The seed command can be re-run at any time to reset test data; it cleans up existing test accounts before re-creating them