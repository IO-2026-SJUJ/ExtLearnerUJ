/* ============================================================
   ExtLearnerUJ — Material voting (FR-09)
   Vanilla JS, używa fetch + CSRF token z ukrytego formularza.
   ============================================================ */
(function () {
    'use strict';

    const btn = document.getElementById('vote-btn');
    if (!btn) return;

    const materialId = btn.dataset.materialId;
    const priorityEl = document.getElementById('priority-value');
    const voteCountEl = document.getElementById('vote-count');

    function getCsrf() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    btn.addEventListener('click', async () => {
        if (btn.disabled) return;
        btn.disabled = true;
        btn.textContent = 'Głosowanie…';

        try {
            const resp = await fetch(`/materials/${materialId}/vote/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (resp.status === 403) {
                btn.textContent = 'Tylko studenci mogą głosować';
                return;
            }
            if (!resp.ok) throw new Error('HTTP ' + resp.status);

            const data = await resp.json();
            if (priorityEl) priorityEl.textContent = data.priority;
            if (voteCountEl) voteCountEl.textContent = data.voteCount;

            btn.classList.remove('btn--accent');
            btn.classList.add('btn--ghost');
            btn.textContent = '👍 Już głosowałeś';
        } catch (err) {
            console.error('Vote failed:', err);
            btn.disabled = false;
            btn.textContent = '👍 Spróbuj ponownie';
        }
    });
})();
