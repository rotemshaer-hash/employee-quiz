// מצב בדיקה: הכל נשמר בדפדפן הזה בלבד, ומייל לא נשלח באמת — הוא מוצג במסך הניהול.
// פעיל רק כש-SETTINGS.demo = true. בגרסה האמיתית הקובץ הזה לא עושה כלום.
(function () {
  if (!SETTINGS.demo) return;
  const KEY = 'quiz-demo';
  let mem = { quizzes: {}, mails: [] };
  const read = () => { try { mem = JSON.parse(localStorage.getItem(KEY)) || mem; } catch (e) {} return mem; };
  const write = () => { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) {} };
  const json = (body, status) => new Response(JSON.stringify(body), { status: status || 200, headers: { 'Content-Type': 'application/json' } });
  const realFetch = window.fetch.bind(window);

  window.fetch = async function (url, opts) {
    url = String(url); opts = opts || {};
    const method = (opts.method || 'GET').toUpperCase();
    read();
    if (url.includes('identitytoolkit.googleapis.com')) return json({ idToken: 'demo' });
    if (url.includes('formsubmit.co')) {
      mem.mails.unshift(Object.assign({ _at: Date.now() }, JSON.parse(opts.body)));
      write(); return json({ success: 'true' });
    }
    if (url.startsWith(SETTINGS.databaseURL)) {
      const id = new URL(url).pathname.replace(/\.json$/, '').split('/').filter(Boolean)[1];
      if (method === 'PUT') { mem.quizzes[id] = JSON.parse(opts.body); write(); return json(mem.quizzes[id]); }
      if (method === 'DELETE') { delete mem.quizzes[id]; write(); return json(null); }
      if (id) return json(mem.quizzes[id] || null);
      return json(Object.keys(mem.quizzes).length ? mem.quizzes : null);
    }
    return realFetch(url, opts);
  };

  // באנר + "תיבת דואר" במסך הניהול
  addEventListener('DOMContentLoaded', () => {
    const banner = document.createElement('div');
    banner.style.cssText = 'background:#fff4d6;color:#6b4e00;padding:10px 16px;text-align:center;font-size:15px;font-weight:600';
    banner.textContent = 'מצב בדיקה — שום דבר לא נשלח באמת';
    document.body.prepend(banner);

    const list = document.getElementById('s-list');
    if (!list) return;
    const box = document.createElement('section');
    box.className = 'card';
    list.after(box);
    const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const draw = () => {
      read();
      box.classList.toggle('hidden', list.classList.contains('hidden'));
      box.innerHTML = '<h2>📬 מיילים שהיו נשלחים אליך</h2>' + (mem.mails.length ? mem.mails.map(m =>
        '<details class="item"><summary>' + esc(m._subject) + '</summary><div style="font-size:15px;margin-top:8px">' +
        Object.keys(m).filter(k => k[0] !== '_').map(k => '<div><b>' + esc(k) + ':</b> ' + esc(m[k]) + '</div>').join('') +
        '</div></details>').join('') : '<p class="muted">עוד אין. עשה מבחן כעובד ותחזור לכאן.</p>');
    };
    draw();
    new MutationObserver(draw).observe(list, { attributes: true, attributeFilter: ['class'] });
    addEventListener('focus', draw);
  });
})();
