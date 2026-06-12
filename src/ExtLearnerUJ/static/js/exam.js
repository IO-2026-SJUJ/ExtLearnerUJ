/* ============================================================
   ExtLearnerUJ — Exam simulation client (FR-06)
   - twardy timer odliczający w dół; po 0:00 blokuje formularz i wysyła wynik
   - autozapis odpowiedzi (NFR-02), zsynchronizowany z czasem serwera
   Serwer i tak egzekwuje deadline — to jest warstwa UX.
   ============================================================ */
(function () {
    'use strict';

    const form = document.getElementById('exam-form');
    if (!form) return;

    const autosaveUrl = form.dataset.autosaveUrl;
    const submitUrl   = form.dataset.submitUrl;
    const csrfToken   = form.dataset.csrfToken;
    const timerEl     = document.getElementById('exam-timer');
    const statusEl    = document.getElementById('exam-status');

    let secondsLeft = parseInt(form.dataset.secondsLeft, 10) || 0;
    let finished    = false;
    let inFlight    = false;
    let dirty       = false;
    let saveTimer   = null;

    function collectAnswers() {
        const answers = {};
        form.querySelectorAll('input[type=radio]:checked').forEach((r) => {
            answers[r.name.replace(/^q_/, '')] = r.value;
        });
        return answers;
    }

    function fmt(sec) {
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    }

    function renderTimer() {
        if (!timerEl) return;
        timerEl.textContent = fmt(Math.max(0, secondsLeft));
        timerEl.classList.toggle('exam-timer--warn', secondsLeft <= 60);
        timerEl.classList.toggle('exam-timer--danger', secondsLeft <= 15);
    }

    function setStatus(text) {
        if (statusEl) statusEl.textContent = text;
    }

    async function save() {
        if (finished || inFlight) { dirty = true; return; }
        inFlight = true; dirty = false;
        try {
            const resp = await fetch(autosaveUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ answers: collectAnswers() }),
            });
            const data = await resp.json();
            if (typeof data.secondsLeft === 'number') {
                secondsLeft = data.secondsLeft;     // sync z serwerem
                renderTimer();
            }
            if (data.expired) { lockAndFinish(true); return; }
            setStatus('Zapisano');
        } catch (err) {
            setStatus('Brak połączenia — odpowiedzi mogą się nie zapisać');
        } finally {
            inFlight = false;
            if (dirty && !finished) save();
        }
    }

    function scheduleSave() {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(save, 300);
    }

    async function lockAndFinish(timedOut) {
        if (finished) return;
        finished = true;
        form.querySelectorAll('input, button').forEach((el) => { el.disabled = true; });
        setStatus(timedOut ? 'Czas minął — wysyłanie wyniku…' : 'Wysyłanie wyniku…');
        try {
            const resp = await fetch(submitUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({}),
            });
            const data = await resp.json();
            window.location.href = data.redirect;
        } catch (err) {
            // Fallback — zwykły submit formularza (serwer i tak zamknie po deadline).
            form.submit();
        }
    }

    form.addEventListener('change', (e) => {
        if (e.target.type === 'radio') scheduleSave();
    });

    // Ręczne zakończenie idzie zwykłym POST-em formularza (działa bez JS też).
    // Tick zegara co sekundę:
    renderTimer();
    const ticker = setInterval(() => {
        if (finished) { clearInterval(ticker); return; }
        secondsLeft -= 1;
        renderTimer();
        if (secondsLeft <= 0) {
            clearInterval(ticker);
            lockAndFinish(true);
        }
    }, 1000);
})();
