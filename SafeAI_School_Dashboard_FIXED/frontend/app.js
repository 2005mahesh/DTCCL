// SafeAI School frontend
// The API URL follows the page hostname, so both localhost and 127.0.0.1 work.
const API = `${window.location.protocol}//${window.location.hostname || '127.0.0.1'}:8000`;

let me = null;
let lessons = [];
let progress = null;
let quizData = [];
let selectedLesson = null;
let quizAnswers = [];
let quizSubmitting = false;

const $ = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
}[c]));

function getToken() {
  return localStorage.getItem('safeai_token') || '';
}

function setToken(token) {
  if (token) localStorage.setItem('safeai_token', token);
  else localStorage.removeItem('safeai_token');
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers,
      credentials: 'omit',
      cache: 'no-store'
    });
  } catch (error) {
    throw new Error(`Cannot connect to SafeAI School API at ${API}. Start the backend with: python -m uvicorn backend.main:app --reload --port 8000`);
  }

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json().catch(() => ({}))
    : { detail: await response.text().catch(() => '') };

  if (!response.ok) {
    if (response.status === 401 && !location.pathname.toLowerCase().endsWith('login.html')) {
      setToken('');
      location.href = 'login.html';
      throw new Error('Your session expired. Please log in again.');
    }
    throw new Error(data.detail || `Request failed (${response.status})`);
  }
  return data;
}

async function boot() {
  if ($('authForm')) {
    setupLogin();
    if (getToken()) {
      try {
        await api('/api/me');
        location.href = 'dashboard.html';
        return;
      } catch {
        setToken('');
      }
    }
    return;
  }

  if ($('app')) {
    try {
      me = await api('/api/me');
      $('loading').hidden = true;
      $('app').hidden = false;
      showApp();
      await refresh();
    } catch (error) {
      setToken('');
      location.href = 'login.html';
    }
  }
}

function setupLogin() {
  let registerMode = false;
  const form = $('authForm');

  const setMode = (isRegister) => {
    registerMode = isRegister;
    $('loginTab').classList.toggle('active', !isRegister);
    $('registerTab').classList.toggle('active', isRegister);
    $('name').hidden = !isRegister;
    $('name').required = isRegister;
    $('password').autocomplete = isRegister ? 'new-password' : 'current-password';
    $('authTitle').textContent = isRegister ? 'Create your account' : 'Welcome back';
    $('authSubtitle').textContent = isRegister
      ? 'Create a student account to start learning.'
      : 'Login to continue your safe AI learning journey.';
    $('authMsg').textContent = '';
    $('authMsg').className = 'message';
    $('authSubmit').textContent = isRegister ? 'Create account' : 'Continue';
  };

  $('loginTab').onclick = () => setMode(false);
  $('registerTab').onclick = () => setMode(true);

  form.onsubmit = async (event) => {
    event.preventDefault();
    const submit = $('authSubmit');
    const message = $('authMsg');
    message.textContent = '';
    message.className = 'message';
    submit.disabled = true;
    submit.textContent = registerMode ? 'Creating account…' : 'Logging in…';

    const payload = {
      name: $('name').value.trim(),
      email: $('email').value.trim(),
      password: $('password').value
    };

    try {
      const result = await api(registerMode ? '/api/register' : '/api/login', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setToken(result.token);
      location.href = 'dashboard.html';
    } catch (error) {
      message.textContent = error.message;
      message.className = 'message error';
      submit.disabled = false;
      submit.textContent = registerMode ? 'Create account' : 'Continue';
    }
  };

  $('apiStatus').textContent = `API: ${API}`;
  setMode(false);
}

function showApp() {
  $('who').textContent = me.name;
  $('studentName').textContent = me.name;
  $('teacherNav').hidden = me.role !== 'teacher';
}

async function refresh() {
  const [lessonData, progressData] = await Promise.all([
    api('/api/lessons'),
    api('/api/progress')
  ]);
  lessons = lessonData;
  progress = progressData;
  renderLessons();
  renderDashboard();
  if (me.role === 'teacher') await loadTeacher();
}

function show(id) {
  document.querySelectorAll('.view').forEach((view) => { view.hidden = true; });
  const target = $(id);
  if (!target) return;
  target.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (id === 'quiz') loadQuiz();
  if (id === 'teacher' && me?.role === 'teacher') loadTeacher();
}

function renderDashboard() {
  if (!progress) return;
  const percent = progress.lessons_total
    ? Math.round((progress.lessons_done / progress.lessons_total) * 100)
    : 0;

  $('percent').textContent = `${percent}%`;
  $('done').textContent = `${progress.lessons_done}/${progress.lessons_total}`;
  $('best').textContent = progress.best_score == null
    ? '—'
    : `${progress.best_score}/${progress.best_total}`;
  $('points').textContent = progress.points;
  $('badgeCount').textContent = progress.badges.length;

  $('badges').innerHTML = progress.badges.length
    ? progress.badges.map((badge) => `
      <div class="badge-item">
        <b>🏅 ${escapeHTML(badge.title)}</b>
        <span>${escapeHTML(badge.description)}</span>
      </div>`).join('')
    : '<p class="muted">Complete lessons and quizzes to earn badges.</p>';

  $('history').innerHTML = progress.attempts.length
    ? progress.attempts.map((attempt) => {
      const percentScore = Math.round((attempt.score / attempt.total) * 100);
      return `
        <div class="history-item">
          <div><b>${attempt.score}/${attempt.total}</b> <span class="score-pill">${percentScore}%</span></div>
          <span class="muted">${new Date(attempt.taken_at).toLocaleString()}</span>
        </div>`;
    }).join('')
    : '<div class="empty-state">No quiz attempts yet. Take the quiz to see your score here.</div>';
}

function renderLessons() {
  $('lessonGrid').innerHTML = lessons.map((lesson) => `
    <article class="card lesson-card">
      <div class="badge">LESSON</div>
      <h3>${escapeHTML(lesson.title)}</h3>
      <p>${escapeHTML(lesson.summary)}</p>
      <button class="study-btn" data-study="${escapeHTML(lesson.id)}">📖 Study Lesson</button>
      <button class="${lesson.completed_at ? 'done' : ''} complete-btn" data-complete="${escapeHTML(lesson.id)}">
        ${lesson.completed_at ? '✓ Completed' : 'Mark complete'}
      </button>
    </article>`).join('');

  $('lessonGrid').onclick = async (event) => {
    const study = event.target.closest('[data-study]');
    if (study) {
      try { await openLessonDetails(study.dataset.study); }
      catch (error) { alert(error.message); }
      return;
    }
    const completeButton = event.target.closest('[data-complete]');
    if (completeButton) {
      try { await complete(completeButton.dataset.complete); }
      catch (error) { alert(error.message); }
    }
  };
}

async function openLessonDetails(id) {
  const lesson = await api(`/api/lessons/${encodeURIComponent(id)}`);
  selectedLesson = lesson;
  $('modalTitle').textContent = lesson.title;
  $('modalIntro').textContent = lesson.details.intro;
  $('modalKeyPoints').innerHTML = lesson.details.key_points.map((item) => `<li>${escapeHTML(item)}</li>`).join('');
  $('modalExamples').innerHTML = lesson.details.examples.map((item) => `<li>${escapeHTML(item)}</li>`).join('');
  $('modalSafetyTips').innerHTML = lesson.details.safety_tips.map((item) => `<li>${escapeHTML(item)}</li>`).join('');
  $('modalRemember').textContent = lesson.details.remember;
  const localLesson = lessons.find((item) => item.id === id);
  $('modalComplete').textContent = localLesson?.completed_at ? '✓ Completed' : '✅ Mark Complete';
  $('lessonModal').hidden = false;
  document.body.classList.add('modal-open');
}

async function complete(id) {
  await api('/api/lessons/complete', {
    method: 'POST',
    body: JSON.stringify({ lesson_id: id })
  });
  await refresh();
  if (selectedLesson?.id === id) $('modalComplete').textContent = '✓ Completed';
}

function closeLessonModal() {
  $('lessonModal').hidden = true;
  document.body.classList.remove('modal-open');
  selectedLesson = null;
}

async function loadQuiz() {
  if (!$('quizBox')) return;
  $('quizBox').innerHTML = '<div class="loading-box">Loading quiz…</div>';
  try {
    quizData = await api('/api/quiz/questions');
    quizAnswers = new Array(quizData.length).fill(null);
    quizSubmitting = false;
    renderQuiz();
  } catch (error) {
    $('quizBox').innerHTML = `<div class="empty-state error-box">${escapeHTML(error.message)}</div>`;
  }
}

function renderQuiz() {
  $('quizBox').innerHTML = `
    ${quizData.map((question, index) => `
      <div class="quiz-card">
        <h3>${index + 1}. ${escapeHTML(question.question)}</h3>
        <div class="options" data-question="${index}">
          ${question.options.map((option, optionIndex) => `
            <button type="button" class="option ${quizAnswers[index] === optionIndex ? 'selected' : ''}"
              data-q="${index}" data-a="${optionIndex}">
              <span class="option-letter">${String.fromCharCode(65 + optionIndex)}</span>
              <span>${escapeHTML(option)}</span>
            </button>`).join('')}
        </div>
      </div>`).join('')}
    <div class="quiz-actions">
      <button id="quizSubmit" class="primary quiz-submit" type="button">Submit quiz</button>
      <span id="quizProgress" class="muted">0/${quizData.length} answered</span>
    </div>
    <div id="quizResult" aria-live="polite"></div>`;

  $('quizBox').onclick = (event) => {
    const option = event.target.closest('.option');
    if (!option || quizSubmitting) return;
    const q = Number(option.dataset.q);
    const answer = Number(option.dataset.a);
    quizAnswers[q] = answer;
    document.querySelectorAll(`.option[data-q="${q}"]`).forEach((button) => button.classList.remove('selected'));
    option.classList.add('selected');
    updateQuizProgress();
  };

  $('quizSubmit').onclick = submitQuiz;
  updateQuizProgress();
}

function updateQuizProgress() {
  const answered = quizAnswers.filter((answer) => answer !== null).length;
  if ($('quizProgress')) $('quizProgress').textContent = `${answered}/${quizData.length} answered`;
}

async function submitQuiz() {
  if (quizSubmitting) return;
  const unanswered = quizAnswers.filter((answer) => answer === null).length;
  const result = $('quizResult');
  if (unanswered) {
    result.innerHTML = `<div class="result warning">Please answer all ${quizData.length} questions before submitting.</div>`;
    return;
  }

  quizSubmitting = true;
  const button = $('quizSubmit');
  button.disabled = true;
  button.textContent = 'Submitting…';
  result.innerHTML = '';

  try {
    const saved = await api('/api/quiz', {
      method: 'POST',
      body: JSON.stringify({ answers: quizAnswers })
    });

    const percentage = Math.round((saved.score / saved.total) * 100);
    result.innerHTML = `
      <div class="result success">
        <h3>🎉 Quiz submitted successfully!</h3>
        <p>Your score: <strong>${saved.score}/${saved.total}</strong> (${percentage}%)</p>
        <p>Your result has been saved to <b>Quiz History</b> on the Dashboard.</p>
        <button class="secondary" type="button" onclick="show('dashboard')">View dashboard</button>
      </div>`;

    await refresh();
  } catch (error) {
    result.innerHTML = `<div class="result error-box">${escapeHTML(error.message)}</div>`;
    button.disabled = false;
    button.textContent = 'Submit quiz';
  } finally {
    quizSubmitting = false;
  }
}

async function loadTeacher() {
  if (!$('teacherRows')) return;
  try {
    const rows = await api('/api/teacher/overview');
    $('teacherRows').innerHTML = rows.length
      ? rows.map((row) => `<tr>
          <td>${escapeHTML(row.name)}</td>
          <td>${escapeHTML(row.email)}</td>
          <td>${row.lessons_done}/${lessons.length}</td>
          <td>${row.best_score == null ? '—' : row.best_score}</td>
          <td>${row.quiz_attempts}</td>
        </tr>`).join('')
      : '<tr><td colspan="5">No students yet.</td></tr>';
  } catch (error) {
    $('teacherRows').innerHTML = `<tr><td colspan="5" class="error-box">${escapeHTML(error.message)}</td></tr>`;
  }
}

async function logout() {
  try { await api('/api/logout', { method: 'POST' }); }
  catch (_) { /* local logout still happens */ }
  setToken('');
  location.href = 'login.html';
}

function toggleChat() {
  $('chat').classList.toggle('open');
  if ($('chat').classList.contains('open')) $('chatInput').focus();
}

async function sendChat(event) {
  event.preventDefault();
  const text = $('chatInput').value.trim();
  if (!text) return;
  addMsg(text, 'user');
  $('chatInput').value = '';
  addMsg('Thinking…', 'bot');
  const thinking = $('messages').lastElementChild;
  try {
    const data = await api('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: text })
    });
    thinking.remove();
    addMsg(data.answer, 'bot');
  } catch (error) {
    thinking.textContent = error.message;
  }
}

function addMsg(text, type) {
  const div = document.createElement('div');
  div.className = `msg ${type}`;
  div.textContent = text;
  $('messages').appendChild(div);
  $('messages').scrollTop = $('messages').scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
  if ($('fab')) $('fab').onclick = toggleChat;
  if ($('chatForm')) $('chatForm').onsubmit = sendChat;
  if ($('closeLesson')) $('closeLesson').onclick = closeLessonModal;
  if ($('backLesson')) $('backLesson').onclick = closeLessonModal;
  if ($('modalComplete')) $('modalComplete').onclick = async () => {
    if (selectedLesson) {
      try { await complete(selectedLesson.id); }
      catch (error) { alert(error.message); }
    }
  };
  if ($('lessonModal')) $('lessonModal').addEventListener('click', (event) => {
    if (event.target.id === 'lessonModal') closeLessonModal();
  });
  boot();
});
