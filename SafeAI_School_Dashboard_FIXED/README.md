# SafeAI School Dashboard — Fixed Version

This version fixes the local login/create-account flow, quiz submission, quiz score/history, dashboard refresh, lesson completion, teacher view, and SafeAI Tutor connection.

## 1. Install dependencies

From the project root:

```powershell
python -m pip install -r requirements.txt
```

## 2. Start the backend

Open PowerShell in the project root:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Keep this terminal running.

## 3. Start the frontend

Open a **second** PowerShell:

```powershell
cd frontend
python -m http.server 5500
```

Keep this terminal running too.

## 4. Open the website

Open:

`http://127.0.0.1:5500/login.html`

## Demo teacher

Email: `teacher@safeai.local`

Password: `Teacher123!`

## Student account

Click **Create account**, enter a name, email and password of at least 8 characters, then click **Create account**.

## Important fixes in this version

- Uses a bearer token stored in the browser instead of fragile cross-port cookies.
- Login and registration both immediately create a persistent database session.
- Login works with either `localhost` or `127.0.0.1` on the frontend.
- Quiz answers are sent to the backend; the backend calculates the score and saves the attempt.
- Quiz history and best score are loaded from SQLite and displayed on the Dashboard.
- Duplicate quiz attempts are allowed and each attempt appears in Quiz History.
- The backend validates the number and range of quiz answers.
- Password hashing uses Python's built-in PBKDF2, avoiding passlib/bcrypt compatibility problems on Python 3.14.
- The API has `/api/health` for a quick backend health check.
- Lesson completion and teacher overview continue to use the same SQLite database.

## If you already have an old `safeai.db`

The new version creates/updates its own tables automatically. If an old local database contains accounts created by a previous version, create a new student account in this fixed version if an old password does not work. Do not delete the database unless you want to reset all existing progress.

## Project structure

```text
SafeAI_School_Dashboard_Complete/
├── backend/
│   └── main.py
├── frontend/
│   ├── app.js
│   ├── dashboard.html
│   ├── login.html
│   └── styles.css
├── .env.example
├── README.md
└── requirements.txt
```
