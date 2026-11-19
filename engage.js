/* Seoul Bites Guide — stay-on-site helpers: scroll progress, saved guides list, food quiz. */
(function () {
  'use strict';
  var KEY = 'bites.saved.v2';
  var doc = document;

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {}
  }
  function pathOf(href) {
    var a = doc.createElement('a');
    a.href = href;
    return a.pathname.replace(/\/index\.html$/, '/');
  }

  /* ---------- scroll progress ---------- */
  var bar = doc.createElement('div');
  bar.className = 'progress-bar';
  bar.setAttribute('aria-hidden', 'true');
  doc.body.appendChild(bar);
  function updateBar() {
    var h = doc.documentElement.scrollHeight - window.innerHeight;
    var p = h > 0 ? (window.scrollY / h) * 100 : 0;
    bar.style.width = Math.max(0, Math.min(100, p)) + '%';
  }
  window.addEventListener('scroll', updateBar, { passive: true });
  window.addEventListener('resize', updateBar);
  updateBar();

  /* ---------- saved guides ---------- */
  var saved = read();
  var buttons = [].slice.call(doc.querySelectorAll('.save-btn'));

  function isSaved(href) {
    var p = pathOf(href);
    return saved.some(function (s) { return s.path === p; });
  }

  var dock = doc.createElement('div');
  dock.className = 'saved-dock';
  dock.innerHTML =
    '<div class="saved-panel" id="saved-panel" hidden>' +
    '<div class="saved-head"><strong>My Seoul list</strong>' +
    '<button class="saved-close" type="button" aria-label="Close saved list">✕</button></div>' +
    '<ul class="saved-list"></ul>' +
    '<p class="saved-empty">Nothing saved yet. Tap “Save this guide” on a guide you want to come back to.</p>' +
    '<button class="saved-clear" type="button">Clear list</button></div>' +
    '<button class="saved-toggle" type="button" aria-expanded="false" aria-controls="saved-panel">★ My list (0)</button>';
  doc.body.appendChild(dock);

  var panel = dock.querySelector('.saved-panel');
  var listEl = dock.querySelector('.saved-list');
  var emptyEl = dock.querySelector('.saved-empty');
  var toggle = dock.querySelector('.saved-toggle');
  var clearBtn = dock.querySelector('.saved-clear');

  function render() {
    toggle.textContent = '★ My list (' + saved.length + ')';
    toggle.setAttribute('aria-expanded', String(!panel.hidden));
    listEl.innerHTML = saved.map(function (s) {
      return '<li><a href="' + s.href + '">' + s.title + '</a>' +
        '<button type="button" class="saved-remove" data-path="' + s.path + '" aria-label="Remove ' +
        s.title.replace(/"/g, '&quot;') + ' from my list">Remove</button></li>';
    }).join('');
    emptyEl.hidden = saved.length > 0;
    clearBtn.hidden = saved.length === 0;
    buttons.forEach(function (b) {
      var on = isSaved(b.getAttribute('data-save-href'));
      b.setAttribute('aria-pressed', String(on));
      b.textContent = on ? '★ Saved to my Seoul list' : '☆ Save this guide to my Seoul list';
    });
  }

  listEl.addEventListener('click', function (e) {
    var btn = e.target.closest('.saved-remove');
    if (!btn) return;
    saved = saved.filter(function (s) { return s.path !== btn.getAttribute('data-path'); });
    write(saved);
    render();
  });
  clearBtn.addEventListener('click', function () {
    saved = [];
    write(saved);
    render();
  });
  toggle.addEventListener('click', function () {
    panel.hidden = !panel.hidden;
    toggle.setAttribute('aria-expanded', String(!panel.hidden));
    if (!panel.hidden) panel.querySelector('a, button').focus();
  });
  dock.querySelector('.saved-close').addEventListener('click', function () {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  });
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      var href = b.getAttribute('data-save-href');
      var p = pathOf(href);
      if (isSaved(href)) {
        saved = saved.filter(function (s) { return s.path !== p; });
      } else {
        saved.push({ path: p, href: href, title: b.getAttribute('data-save-title') });
      }
      write(saved);
      render();
    });
  });
  render();

  /* ---------- 1-minute Seoul food quiz ---------- */
  var quiz = doc.getElementById('seoul-quiz');
  if (quiz) {
    var form = quiz.querySelector('form');
    var result = quiz.querySelector('.quiz-result');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var right = 0;
      var missed = [];
      quiz.querySelectorAll('fieldset').forEach(function (fs) {
        var answer = fs.getAttribute('data-answer');
        var chosen = data.get(fs.getAttribute('data-name'));
        var ok = chosen === answer;
        fs.classList.toggle('quiz-ok', ok);
        fs.classList.toggle('quiz-bad', !ok && !!chosen);
        if (ok) right++; else missed.push(fs.getAttribute('data-href'));
        var note = fs.querySelector('.quiz-why');
        if (note) note.hidden = ok;
      });
      var total = quiz.querySelectorAll('fieldset').length;
      var answered = form.querySelectorAll('input[type=radio]:checked').length;
      result.hidden = false;
      var head = '<strong>' + right + ' / ' + total + ' correct.</strong> ';
      var tail;
      if (answered < total) {
        tail = 'You answered ' + answered + ' of ' + total + '. ' +
          (missed[0] ? 'The guide for the first one you missed: <a href="' + missed[0] + '">open it →</a>' : '');
      } else if (right === total) {
        tail = 'You could order for the whole table. Next: <a href="./seoul-must-eat-dishes-index.html">the 15-dish price index</a>.';
      } else {
        tail = 'Close. The guide that covers what you missed: <a href="' + missed[0] + '">open it →</a>';
      }
      result.innerHTML = head + tail;
      result.focus();
    });
    quiz.querySelector('.quiz-reset').addEventListener('click', function () {
      form.reset();
      quiz.querySelectorAll('fieldset').forEach(function (fs) {
        fs.classList.remove('quiz-ok', 'quiz-bad');
      });
      result.hidden = true;
    });
  }
})();
