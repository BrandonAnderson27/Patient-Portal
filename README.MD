# Patient Portal System

## Requirements

Make sure you have the correct Python version installed.

Check your Python version:

```bash
python --version
```

Required:

- Python 3.12+

---

## Setup Virtual Environment

Create a virtual environment inside the project directory.

### Windows

Create environment:

```bash
python -m venv venv
```

Activate environment:

### Windows (Command Prompt)

```bash
venv\Scripts\activate
```

### Windows (PowerShell)

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
