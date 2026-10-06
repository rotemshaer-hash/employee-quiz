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

  // סרטונים במצב בדיקה נשמרים ב-IndexedDB של הדפדפן
  const idb = () => new Promise((ok, bad) => {
    const r = indexedDB.open('quiz-demo-videos', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('v');
    r.onsuccess = () => ok(r.result); r.onerror = () => bad(r.error);
  });
  const idbDo = async (mode, fn) => {
    const db = await idb();
    return new Promise((ok, bad) => {
      const tx = db.transaction('v', mode), req = fn(tx.objectStore('v'));
      tx.oncomplete = () => ok(req && req.result); tx.onerror = () => bad(tx.error);
    });
  };
  const uploads = {};   // path -> [chunks]
  const pathOf = url => decodeURIComponent(new URL(url).pathname.split('/o/')[1] || '');
  window.resolveVideoSrc = async url => {
    if (!url.includes('firebasestorage') || !url.includes('token=demo')) return url;
    const blob = await idbDo('readonly', st => st.get(pathOf(url)));
    return blob ? URL.createObjectURL(blob) : url;
  };

  window.fetch = async function (url, opts) {
    url = String(url); opts = opts || {};
    const method = (opts.method || 'GET').toUpperCase();
    read();
    if (url.includes('identitytoolkit.googleapis.com')) return json({ idToken: 'demo' });
    if (url.includes('formsubmit.co')) {
      mem.mails.unshift(Object.assign({ _at: Date.now() }, JSON.parse(opts.body)));
      write(); return json({ success: 'true' });
    }
    if (url.includes('firebasestorage.googleapis.com')) {
      const h = opts.headers || {}, cmd = h['X-Goog-Upload-Command'] || '';
      if (cmd === 'start') {
        const path = new URL(url).searchParams.get('name');
        uploads[path] = [];
        return new Response('{}', { headers: { 'X-Goog-Upload-URL': 'https://firebasestorage.googleapis.com/demo-upload?path=' + encodeURIComponent(path) } });
      }
      if (url.includes('/demo-upload')) {
        const path = new URL(url).searchParams.get('path'), parts = uploads[path];
        const received = () => parts.reduce((n, b) => n + b.size, 0);
        if (cmd === 'query') return new Response('', { headers: { 'X-Goog-Upload-Size-Received': String(received()) } });
        parts.push(opts.body);
        if (cmd.includes('finalize')) {
          await idbDo('readwrite', st => st.put(new Blob(parts, { type: 'video/mp4' }), path));
          delete uploads[path];
          return json({ name: path, downloadTokens: 'demo' });
        }
        return new Response('');
      }
      if (method === 'DELETE') { await idbDo('readwrite', st => st.delete(pathOf(url))); return new Response(''); }
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
