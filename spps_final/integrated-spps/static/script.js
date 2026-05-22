/**
 * script.js — Student Performance Prediction System
 * ORIGINAL JS kept. NEW admin helpers added at the bottom.
 */

// ── Spinner ──────────────────────────────────────────────────
function showSpinner() {
  const o = document.getElementById('spinnerOverlay');
  if (o) o.classList.add('active');
}
function hideSpinner() {
  const o = document.getElementById('spinnerOverlay');
  if (o) o.classList.remove('active');
}

// ── Form Validation & Submit ─────────────────────────────────
function setupPredictForm() {
  const form = document.getElementById('predictForm');
  if (!form) return;

  const rules = {
    study_hours:    { min:0, max:16,  label:'Study Hours' },
    attendance:     { min:0, max:100, label:'Attendance (%)' },
    prev_sem_marks: { min:0, max:100, label:'Previous Sem Marks' },
    internal_marks: { min:0, max:25,  label:'Internal Marks' },
    assignment_pct: { min:0, max:100, label:'Assignment Completion (%)' },
    sleep_hours:    { min:0, max:16,  label:'Sleep Hours' },
    internet_hours: { min:0, max:16,  label:'Internet Hours' },
  };

  form.addEventListener('submit', function(e) {
    let valid = true;
    clearErrors();
    for (const [name, rule] of Object.entries(rules)) {
      const input = form.querySelector(`[name="${name}"]`);
      if (!input) continue;
      const val = parseFloat(input.value);
      if (isNaN(val)) { showError(input, `${rule.label} is required.`); valid = false; }
      else if (val < rule.min || val > rule.max) { showError(input, `${rule.label} must be ${rule.min}–${rule.max}.`); valid = false; }
    }
    const part = form.querySelector('[name="participation"]');
    if (part && part.value === '') { showError(part, 'Please select Participation.'); valid = false; }
    if (!valid) { e.preventDefault(); const first = form.querySelector('.error'); if (first) first.scrollIntoView({ behavior:'smooth', block:'center' }); return; }
    showSpinner();
  });

  form.querySelectorAll('.form-input').forEach(input => {
    input.addEventListener('blur', () => {
      clearError(input);
      const rule = rules[input.name];
      if (!rule) return;
      const val = parseFloat(input.value);
      if (!isNaN(val) && (val < rule.min || val > rule.max)) showError(input, `Must be ${rule.min}–${rule.max}.`);
    });
    input.addEventListener('input', () => clearError(input));
  });
}

function showError(el, msg) {
  el.classList.add('error');
  el.style.borderColor = '#ef4444';
  let err = el.parentNode.querySelector('.field-error');
  if (!err) { err = document.createElement('div'); err.className = 'input-hint field-error'; err.style.color = '#f87171'; el.parentNode.appendChild(err); }
  err.textContent = msg;
}
function clearError(el) {
  el.classList.remove('error');
  el.style.borderColor = '';
  const err = el.parentNode.querySelector('.field-error');
  if (err) err.remove();
}
function clearErrors() {
  document.querySelectorAll('.error').forEach(el => { el.classList.remove('error'); el.style.borderColor = ''; });
  document.querySelectorAll('.field-error').forEach(el => el.remove());
}
function resetForm() {
  const form = document.getElementById('predictForm');
  if (form) { form.reset(); clearErrors(); }
}

// ── Animate probability bars ─────────────────────────────────
function animateProbBars() {
  document.querySelectorAll('.prob-fill').forEach(bar => {
    const target = bar.dataset.width || '0';
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = target + '%'; }, 200);
  });
}

// ── Animate counters ─────────────────────────────────────────
function animateCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;
    let start = 0;
    const step = target / (1200 / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { start = target; clearInterval(timer); }
      el.textContent = start.toFixed(decimals) + suffix;
    }, 16);
  });
}

// ── Scroll animations ─────────────────────────────────────────
function setupScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('animate-fade-up'); entry.target.style.opacity='1'; observer.unobserve(entry.target); }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.card, .stat-tile').forEach(el => { el.style.opacity='0'; observer.observe(el); });
}

// ── Active nav ────────────────────────────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href');
    if ((path==='/' && href==='/') || (href!=='/' && path.startsWith(href))) link.classList.add('active');
  });
}

// ── Contact form (frontend only) ──────────────────────────────
function setupContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const name = form.querySelector('#cName').value.trim();
    const email = form.querySelector('#cEmail').value.trim();
    const msg = form.querySelector('#cMessage').value.trim();
    if (!name||!email||!msg) { alert('Please fill in all fields.'); return; }
    form.innerHTML = `<div style="text-align:center;padding:2rem"><div style="font-size:3rem;margin-bottom:1rem">✅</div><h3 style="color:#10b981">Message Sent!</h3><p style="color:rgba(255,255,255,0.6)">Thank you, ${name}.</p></div>`;
  });
}

// ── NEW: Auto-hide flash messages ─────────────────────────────
function autoHideFlash() {
  setTimeout(() => {
    document.querySelectorAll('.flash-msg').forEach(f => {
      f.style.transition = 'opacity .5s';
      f.style.opacity = '0';
      setTimeout(() => f.remove(), 500);
    });
  }, 4500);
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setActiveNav();
  setupPredictForm();
  setupScrollAnimations();
  setupContactForm();
  animateProbBars();
  animateCounters();
  autoHideFlash();
});
