import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "safeai.db"

app = FastAPI(title="SafeAI School API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Password hashing: built-in PBKDF2, so the project does not depend on the
# Python 3.14/passlib/bcrypt compatibility combination.
# -----------------------------------------------------------------------------
PBKDF2_ITERATIONS = 310_000

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


LESSONS = [
    {
        "id": "privacy", "title": "Protecting Privacy",
        "summary": "Keep passwords, OTPs, addresses, live locations, school IDs and private photos out of AI chats.",
        "details": {
            "intro": "Privacy means controlling who can access information about you. AI tools can be useful, but anything you type or upload should be treated carefully.",
            "key_points": ["Never share passwords, OTPs or authentication codes.", "Avoid sharing your home address, live location or school ID.", "Do not upload private photos or documents unless you understand how the service handles them.", "Use fictional or non-identifying examples when learning with AI."],
            "examples": ["Instead of entering your real address, write: 'I live in a large city.'", "Instead of pasting a real OTP, ask: 'What is an OTP and why should it stay private?'"],
            "safety_tips": ["Pause before uploading anything personal.", "Ask a trusted adult or teacher if you are unsure.", "Use strong passwords and multi-factor authentication."],
            "remember": "AI can help you learn without needing your private information."
        }
    },
    {
        "id": "phishing", "title": "Spotting Phishing",
        "summary": "Learn how fake messages and websites try to trick people into revealing information.",
        "details": {
            "intro": "Phishing is a deceptive attempt to make you reveal information, click a harmful link or take an unsafe action.",
            "key_points": ["Check the sender and website address carefully.", "Urgent messages are a reason to slow down, not panic.", "Never share passwords or OTPs through messages.", "Verify unusual requests through a trusted channel."],
            "examples": ["A message says your account will be closed in 10 minutes unless you click a link.", "Someone pretending to be a teacher asks for your password."],
            "safety_tips": ["Do not click suspicious links.", "Open the official app or website yourself.", "Tell a trusted adult about suspicious messages."],
            "remember": "Slow down, verify, and never give secrets to an unexpected sender."
        }
    },
    {
        "id": "deepfakes", "title": "Understanding Deepfakes",
        "summary": "Learn how AI can create or manipulate realistic-looking images, audio and video.",
        "details": {
            "intro": "A deepfake is AI-generated or AI-manipulated media designed to look or sound real.",
            "key_points": ["Realistic media is not automatically authentic.", "Look for the original source and context.", "Check important claims against reliable sources.", "Do not forward embarrassing or harmful manipulated media."],
            "examples": ["A video appears to show a person saying something they never said.", "An image is edited so a person appears in a place they were never in."],
            "safety_tips": ["Avoid sharing uncertain media.", "Check multiple reliable sources.", "Report harmful impersonation when appropriate."],
            "remember": "Seeing is not always proof; verify important media before believing or sharing it."
        }
    },
    {
        "id": "misinformation", "title": "Misinformation",
        "summary": "Learn how to check surprising AI-generated claims before sharing them.",
        "details": {
            "intro": "Misinformation is incorrect or misleading information. AI can produce convincing text that still contains errors.",
            "key_points": ["AI can make mistakes or invent details.", "Check dates, names, numbers and sources.", "Prefer primary or trusted sources for important claims.", "Separate facts from opinions and guesses."],
            "examples": ["An AI answer gives a statistic without a source.", "A viral post makes a surprising claim but provides no evidence."],
            "safety_tips": ["Search for independent confirmation.", "Check the original source and publication date.", "Do not share a claim simply because it sounds confident."],
            "remember": "Confidence is not evidence; verify important information."
        }
    },
    {
        "id": "responsible-ai", "title": "Responsible AI Use",
        "summary": "Use AI as a learning helper while keeping your own thinking and checking your work.",
        "details": {
            "intro": "Responsible AI use means using AI in ways that support learning, honesty, safety and respect.",
            "key_points": ["Use AI to explain concepts and generate practice.", "Check AI answers before relying on them.", "Follow your school's rules for AI-assisted work.", "Do your own thinking instead of copying blindly."],
            "examples": ["Ask AI to explain a difficult concept, then solve a similar problem yourself.", "Use AI feedback to improve a draft while keeping your own ideas."],
            "safety_tips": ["Do not submit copied work when your school requires original work.", "Ask your teacher when AI use is unclear.", "Keep private information out of prompts."],
            "remember": "AI should support your learning, not replace your responsibility."
        }
    },
    {
        "id": "digital-footprint", "title": "Digital Footprint",
        "summary": "Understand the information your online activity can leave behind.",
        "details": {
            "intro": "A digital footprint is information connected with your online activity, such as posts, comments, profiles and interactions.",
            "key_points": ["Posts and comments can be copied or reshared.", "Privacy settings reduce exposure but are not a guarantee.", "Think about future audiences before posting.", "Remove unnecessary personal information from public profiles."],
            "examples": ["A public post can be screenshotted even after you delete it.", "A profile may reveal your school, routine or interests."],
            "safety_tips": ["Review privacy settings regularly.", "Avoid posting live location information.", "Use respectful language online."],
            "remember": "Think before you post because online information can travel beyond its original audience."
        }
    },
    {
        "id": "strong-accounts", "title": "Strong Account Security",
        "summary": "Build safer account habits with unique passwords and multi-factor authentication.",
        "details": {
            "intro": "Account security reduces the chance that someone else can access your accounts.",
            "key_points": ["Use a different strong password for important accounts.", "Enable multi-factor authentication where available.", "Never share authentication codes.", "Use a reputable password manager if appropriate."],
            "examples": ["Your email password should not be the same as your gaming password.", "An MFA code should be entered only into the service you are signing into."],
            "safety_tips": ["Do not save passwords in public chats.", "Change a password if you think it has been exposed.", "Keep recovery information secure."],
            "remember": "Unique passwords plus MFA provide stronger protection than password reuse."
        }
    },
    {
        "id": "safe-chat", "title": "Safe AI Chats",
        "summary": "Learn how to ask useful questions to AI without exposing sensitive information.",
        "details": {
            "intro": "AI chat can be a powerful learning tool. Good prompts can be specific while still protecting personal information.",
            "key_points": ["Use fictional names and sample data.", "Remove passwords, IDs, addresses and private records.", "Ask for explanations, examples and practice questions.", "Check important answers independently."],
            "examples": ["Ask: 'Explain photosynthesis for a 10th-grade student.'", "Use a fictional student name when asking for help with a writing exercise."],
            "safety_tips": ["Review your prompt before pressing Send.", "Do not paste confidential school or family records.", "Close or report conversations that make you uncomfortable."],
            "remember": "A useful AI prompt does not need your private data."
        }
    },
    {
        "id": "online-respect", "title": "Online Respect & Safety",
        "summary": "Communicate respectfully and know what to do when online content feels unsafe.",
        "details": {
            "intro": "Digital safety includes respectful communication, boundaries and knowing when to ask for help.",
            "key_points": ["Do not participate in harassment or bullying.", "Do not share another person's private information.", "Block or report harmful behavior when appropriate.", "Tell a trusted adult when something online feels unsafe."],
            "examples": ["A group chat repeatedly targets a student with insulting messages.", "Someone asks you to keep a suspicious online conversation secret."],
            "safety_tips": ["Save evidence if reporting is needed.", "Use platform block and report tools.", "Talk to a trusted adult, teacher or school counselor."],
            "remember": "You do not have to handle unsafe online situations alone."
        }
    },
    {
        "id": "ai-facts", "title": "Checking AI Answers",
        "summary": "Learn why AI answers should be checked before you use important information.",
        "details": {
            "intro": "AI can produce useful explanations, but it can also make mistakes. Critical thinking and verification remain important.",
            "key_points": ["Check important facts against reliable sources.", "Look for missing context or outdated information.", "Ask follow-up questions when an answer is unclear.", "For schoolwork, understand the answer rather than copying it."],
            "examples": ["Compare an AI-generated science fact with your textbook or a trusted educational source.", "Ask AI to explain a calculation and then verify the result yourself."],
            "safety_tips": ["Do not treat confidence as proof.", "Use more than one reliable source for important claims.", "Ask a teacher when you are unsure."],
            "remember": "Use AI as a helper, but keep your own judgment and verification."
        }
    },
]

QUIZ_QUESTIONS = [
    {"id": 1, "question": "What should you do with an OTP?", "options": ["Never share it with anyone", "Post it privately", "Give it to a chatbot", "Use it as a username"], "answer": 0},
    {"id": 2, "question": "Why should AI answers be checked?", "options": ["AI can make mistakes", "AI always knows everything", "Checking deletes errors", "AI cannot write facts"], "answer": 0},
    {"id": 3, "question": "What is a deepfake?", "options": ["AI-generated or manipulated media", "A password manager", "A Wi-Fi setting", "A search engine"], "answer": 0},
    {"id": 4, "question": "What is phishing?", "options": ["A trick to steal information through deceptive messages or sites", "A school subject", "A type of AI model", "A safe backup"], "answer": 0},
    {"id": 5, "question": "Which is safest to put into an AI chat?", "options": ["A fictional example", "Your password", "Your OTP", "Your home address"], "answer": 0},
    {"id": 6, "question": "What is a digital footprint?", "options": ["Information you leave through online activity", "A paper footprint", "A computer cable", "A Wi-Fi password"], "answer": 0},
    {"id": 7, "question": "What should you do if online content feels unsafe?", "options": ["Stop and tell a trusted adult", "Send more information", "Meet the sender", "Keep it secret"], "answer": 0},
    {"id": 8, "question": "What is responsible homework AI use?", "options": ["Learn with AI and verify your work", "Copy everything", "Submit private records", "Ask AI to impersonate a teacher"], "answer": 0},
    {"id": 9, "question": "Before sharing a surprising AI claim, you should…", "options": ["Check reliable sources and context", "Share immediately", "Hide the source", "Assume it is true"], "answer": 0},
    {"id": 10, "question": "Which is a strong account habit?", "options": ["Use unique passwords and MFA", "Reuse one password everywhere", "Share OTPs", "Save passwords in public chats"], "answer": 0},
]


class AuthData(BaseModel):
    name: str = ""
    email: EmailStr
    password: str


class QuizSubmission(BaseModel):
    answers: list[int]


class LessonComplete(BaseModel):
    lesson_id: str


class ChatData(BaseModel):
    message: str


def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'student')")
    con.execute("CREATE TABLE IF NOT EXISTS completions(user_id INTEGER,lesson_id TEXT,completed_at TEXT,PRIMARY KEY(user_id,lesson_id))")
    con.execute("CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,score INTEGER,total INTEGER,taken_at TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER NOT NULL,created_at TEXT NOT NULL)")
    teacher = con.execute("SELECT id FROM users WHERE email=?", ("teacher@safeai.local",)).fetchone()
    if not teacher:
        con.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            ("Demo Teacher", "teacher@safeai.local", hash_password("Teacher123!"), "teacher"),
        )
    con.commit()
    con.close()


init_db()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    con = db()
    con.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)", (token, user_id, now_iso()))
    con.commit()
    con.close()
    return token


def current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not token:
        raise HTTPException(401, "Not logged in")
    con = db()
    row = con.execute(
        "SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=?",
        (token,),
    ).fetchone()
    con.close()
    if not row:
        raise HTTPException(401, "Session expired. Please log in again.")
    return dict(row)


@app.get("/")
def root():
    return {"name": "SafeAI School API", "status": "running", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(request: Request):
    return current_user(request)


@app.post("/api/register")
def register(data: AuthData):
    name = data.name.strip()
    email = str(data.email).lower().strip()
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if not name:
        raise HTTPException(400, "Name is required")
    con = db()
    try:
        cur = con.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, hash_password(data.password)),
        )
        con.commit()
        uid = cur.lastrowid
    except sqlite3.IntegrityError:
        con.close()
        raise HTTPException(400, "An account with this email already exists")
    con.close()
    token = create_session(uid)
    return {"message": "Registered successfully", "token": token}


@app.post("/api/login")
def login(data: AuthData):
    email = str(data.email).lower().strip()
    con = db()
    user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    con.close()
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_session(user["id"])
    return {"message": "Login successful", "token": token}


@app.post("/api/logout")
def logout(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if token:
        con = db()
        con.execute("DELETE FROM sessions WHERE token=?", (token,))
        con.commit()
        con.close()
    return {"message": "Logged out"}


@app.get("/api/lessons")
def lessons(request: Request):
    u = current_user(request)
    con = db()
    rows = con.execute("SELECT lesson_id,completed_at FROM completions WHERE user_id=?", (u["id"],)).fetchall()
    con.close()
    done = {r["lesson_id"]: r["completed_at"] for r in rows}
    return [
        {"id": x["id"], "title": x["title"], "summary": x["summary"], "completed_at": done.get(x["id"])}
        for x in LESSONS
    ]


@app.get("/api/lessons/{lesson_id}")
def lesson_detail(lesson_id: str, request: Request):
    current_user(request)
    for x in LESSONS:
        if x["id"] == lesson_id:
            return x
    raise HTTPException(404, "Lesson not found")


@app.post("/api/lessons/complete")
def complete_lesson(data: LessonComplete, request: Request):
    u = current_user(request)
    if not any(x["id"] == data.lesson_id for x in LESSONS):
        raise HTTPException(404, "Lesson not found")
    con = db()
    con.execute(
        "INSERT OR REPLACE INTO completions(user_id,lesson_id,completed_at) VALUES(?,?,?)",
        (u["id"], data.lesson_id, now_iso()),
    )
    con.commit()
    con.close()
    return {"message": "Lesson completed"}


@app.get("/api/quiz/questions")
def quiz_questions(request: Request):
    current_user(request)
    return [{k: q[k] for k in ("id", "question", "options")} for q in QUIZ_QUESTIONS]


@app.post("/api/quiz")
def quiz(data: QuizSubmission, request: Request):
    u = current_user(request)
    if len(data.answers) != len(QUIZ_QUESTIONS):
        raise HTTPException(400, f"Please answer all {len(QUIZ_QUESTIONS)} questions.")
    if any(a not in range(4) for a in data.answers):
        raise HTTPException(400, "Invalid quiz answer.")
    score = sum(1 for q, answer in zip(QUIZ_QUESTIONS, data.answers) if q["answer"] == answer)
    total = len(QUIZ_QUESTIONS)
    taken_at = now_iso()
    con = db()
    con.execute(
        "INSERT INTO attempts(user_id,score,total,taken_at) VALUES(?,?,?,?)",
        (u["id"], score, total, taken_at),
    )
    con.commit()
    con.close()
    return {"message": "Quiz saved", "score": score, "total": total, "taken_at": taken_at}


@app.get("/api/progress")
def progress(request: Request):
    u = current_user(request)
    con = db()
    done = con.execute("SELECT COUNT(*) c FROM completions WHERE user_id=?", (u["id"],)).fetchone()["c"]
    attempts = con.execute(
        "SELECT id,score,total,taken_at FROM attempts WHERE user_id=? ORDER BY id DESC",
        (u["id"],),
    ).fetchall()
    best_row = con.execute(
        "SELECT score,total FROM attempts WHERE user_id=? ORDER BY score DESC,id ASC LIMIT 1",
        (u["id"],),
    ).fetchone()
    badges = []
    if done >= 1:
        badges.append({"title": "First Lesson", "description": "Completed your first lesson."})
    if done >= len(LESSONS):
        badges.append({"title": "Safety Scholar", "description": "Completed every lesson."})
    if attempts:
        badges.append({"title": "Quiz Starter", "description": "Completed a safety quiz."})
    con.close()
    return {
        "lessons_done": done,
        "lessons_total": len(LESSONS),
        "best_score": best_row["score"] if best_row else None,
        "best_total": best_row["total"] if best_row else None,
        "points": done * 10 + sum(r["score"] for r in attempts),
        "badges": badges,
        "attempts": [dict(r) for r in attempts],
    }


@app.get("/api/teacher/overview")
def teacher_overview(request: Request):
    u = current_user(request)
    if u["role"] != "teacher":
        raise HTTPException(403, "Teacher access required")
    con = db()
    users = con.execute("SELECT id,name,email FROM users WHERE role='student' ORDER BY name").fetchall()
    rows = []
    for student in users:
        done = con.execute("SELECT COUNT(*) c FROM completions WHERE user_id=?", (student["id"],)).fetchone()["c"]
        best = con.execute("SELECT MAX(score) m FROM attempts WHERE user_id=?", (student["id"],)).fetchone()["m"]
        attempts = con.execute("SELECT COUNT(*) c FROM attempts WHERE user_id=?", (student["id"],)).fetchone()["c"]
        rows.append({"name": student["name"], "email": student["email"], "lessons_done": done, "best_score": best, "quiz_attempts": attempts})
    con.close()
    return rows


@app.post("/api/chat")
def chat(data: ChatData, request: Request):
    current_user(request)
    text = data.message.strip().lower()
    if not text:
        raise HTTPException(400, "Message is required")
    if any(x in text for x in ["otp", "password", "privacy", "address", "location"]):
        ans = "Protect private information: never share passwords, OTPs, home addresses, live locations, school IDs or private photos in an AI chat."
    elif any(x in text for x in ["phishing", "fake link", "suspicious message"]):
        ans = "For possible phishing, slow down, check the sender and URL, avoid suspicious links, and verify the request through an official channel."
    elif "deepfake" in text:
        ans = "A deepfake is AI-generated or manipulated media that can look or sound realistic. Check the original source and context before sharing it."
    elif any(x in text for x in ["misinformation", "fake news", "verify"]):
        ans = "AI can make mistakes. Check important claims against reliable, independent sources before sharing or relying on them."
    else:
        ans = "I can help with privacy, phishing, deepfakes, misinformation, strong accounts, safe AI chats and responsible AI use. Ask me a specific safety question."
    return {"answer": ans}
