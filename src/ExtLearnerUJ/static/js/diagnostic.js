/* ============================================================
   ExtLearnerUJ — Diagnostic test client
   Implementuje NFR-02: autozapis po każdej zmianie odpowiedzi.
   Używa fetch() + cookie CSRF (Django standard).
   ============================================================ */
(function () {
    'use strict';

    const form = document.getElementById('diagnostic-form');
    if (!form) return;

    const autosaveUrl = form.dataset.autosaveUrl;
    const csrfToken   = form.dataset.csrfToken;
    const statusEl    = document.getElementById('progress-status');
    const fillEl      = document.getElementById('progress-fill');
    const totalCount  = parseInt(form.dataset.totalCount, 10) || 0;

    let saveTimer   = null;
    let inFlight    = false;
    let dirty       = false;

    function collectAnswers() {
        const answers = {};
        const radios = form.querySelectorAll('input[type=radio]:checked');
        radios.forEach((r) => {
            // name="q_<id>"
            const qid = r.name.replace(/^q_/, '');
            answers[qid] = r.value;
        });
        return answers;
    }

    function updateProgress(answered) {
        if (!fillEl || !totalCount) return;
        const pct = Math.round(100 * answered / totalCount);
        fillEl.style.width = pct + '%';
    }

    function setStatus(text, saved) {
        if (!statusEl) return;
        statusEl.textContent = text;
        statusEl.classList.toggle('test-progress__status--saved', !!saved);
    }

    async function save() {
        if (inFlight) { dirty = true; return; }
        inFlight = true;
        dirty = false;
        const answers = collectAnswers();
        updateProgress(Object.keys(answers).length);
        setStatus('Zapisywanie…', false);

        try {
            const resp = await fetch(autosaveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ answers }),
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const now = new Date();
            const hh = String(now.getHours()).padStart(2, '0');
            const mm = String(now.getMinutes()).padStart(2, '0');
            const ss = String(now.getSeconds()).padStart(2, '0');
            setStatus(`Zapisano · ${hh}:${mm}:${ss}`, true);
        } catch (err) {
            console.error('Autosave failed:', err);
            setStatus('Nie udało się zapisać — sprawdź połączenie', false);
        } finally {
            inFlight = false;
            if (dirty) save();  // jeśli użytkownik zdążył zaznaczyć kolejną odpowiedź
        }
    }

    function scheduleSave() {
        if (saveTimer) clearTimeout(saveTimer);
        // Mały debounce żeby nie spamować przy szybkich kliknięciach
        saveTimer = setTimeout(save, 300);
    }

    form.addEventListener('change', (e) => {
        if (e.target.type === 'radio') {
            scheduleSave();
        }
    });

    // Przy submit: bez autozapisu (i tak zapisze właściwa ocena)
    form.addEventListener('submit', () => {
        if (saveTimer) clearTimeout(saveTimer);
    });

    // Początkowy stan
    updateProgress(0);
    setStatus('Zmiany zapisują się automatycznie', false);
})();
