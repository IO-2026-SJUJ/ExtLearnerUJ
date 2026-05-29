/* ============================================================
   ExtLearnerUJ — Error Marker (FR-10)

   Moderator zaznacza fragment tekstu myszą, klika kolor,
   zaznaczenie jest zapisywane przez AJAX.
   ============================================================ */
(function () {
    'use strict';

    const editor = document.getElementById('editor-text');
    if (!editor) return;

    const markList = document.getElementById('mark-list');
    const addUrl = editor.dataset.addUrl;
    let activeType = 'GRAMMAR';

    function getCsrf() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    // ---- Wybór koloru ----
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeType = btn.dataset.type;
        });
    });

    // ---- Zaznaczanie tekstu ----
    editor.addEventListener('mouseup', async () => {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed) return;

        const snippet = selection.toString().trim();
        if (snippet.length < 2) return;

        // Sprawdź czy zaznaczenie jest w edytorze
        const range = selection.getRangeAt(0);
        if (!editor.contains(range.commonAncestorContainer)) return;

        // Zapytaj o komentarz (opcjonalnie)
        const comment = prompt(
            `Komentarz do zaznaczenia "${snippet.substring(0, 40)}"` +
            (snippet.length > 40 ? '…' : '') +
            ' (opcjonalny, ENTER aby pominąć):',
            ''
        );
        if (comment === null) {
            // Kliknęła Cancel — nie zapisujemy
            selection.removeAllRanges();
            return;
        }

        try {
            const resp = await fetch(addUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrf(),
                },
                body: JSON.stringify({
                    snippet: snippet,
                    type: activeType,
                    position: '',  // pozycja znakowa — do rozbudowy w Sprincie 3
                    comment: comment || '',
                }),
            });

            if (!resp.ok) {
                alert('Nie udało się zapisać zaznaczenia.');
                return;
            }

            const data = await resp.json();

            // Wizualnie zaznacz fragment w tekście
            try {
                const span = document.createElement('span');
                span.className = 'mark mark--' + activeType.toLowerCase();
                span.title = comment || activeType;
                span.dataset.markId = data.id;
                range.surroundContents(span);
                selection.removeAllRanges();
            } catch (e) {
                // Jeśli zaznaczenie przekracza granice node'ów, surroundContents rzuci
                // błąd — pominiemy wizualne zaznaczenie, ale mark jest zapisany.
                console.warn('Nie udało się otoczyć tagiem:', e);
            }

            // Dodaj do listy w panelu
            addToMarkList(data);
        } catch (err) {
            console.error('Add mark failed:', err);
            alert('Błąd sieci — spróbuj ponownie.');
        }
    });

    function addToMarkList(mark) {
        if (!markList) return;
        const item = document.createElement('div');
        item.className = 'mark-item mark-item--' + mark.type.toLowerCase();
        item.dataset.id = mark.id;

        const del = document.createElement('button');
        del.className = 'mark-item__delete';
        del.innerHTML = '×';
        del.title = 'Usuń';
        del.dataset.deleteUrl = `/moderator/marks/${mark.id}/delete/`;
        del.addEventListener('click', () => deleteMark(mark.id, item));

        const snippet = document.createElement('div');
        snippet.className = 'mark-item__snippet';
        snippet.textContent = '„' + (mark.snippet.length > 60
            ? mark.snippet.substring(0, 60) + '…'
            : mark.snippet) + '"';

        item.appendChild(del);
        item.appendChild(snippet);

        if (mark.comment) {
            const c = document.createElement('div');
            c.className = 'mark-item__comment';
            c.textContent = mark.comment;
            item.appendChild(c);
        }
        markList.prepend(item);
    }

    // ---- Usuwanie istniejących (także statycznych z serwera) ----
    markList?.querySelectorAll('.mark-item__delete').forEach(btn => {
        btn.addEventListener('click', async () => {
            const url = btn.dataset.deleteUrl;
            const item = btn.closest('.mark-item');
            const id = item.dataset.id;
            await deleteMark(id, item, url);
        });
    });

    async function deleteMark(id, itemEl, url = null) {
        const deleteUrl = url || `/moderator/marks/${id}/delete/`;
        if (!confirm('Usunąć to zaznaczenie?')) return;

        try {
            const resp = await fetch(deleteUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() },
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);

            // Usuń z listy
            itemEl?.remove();

            // Usuń ze zmienionego tekstu — rozpakuj span.mark
            const marked = editor.querySelector(`[data-mark-id="${id}"]`);
            if (marked) {
                const parent = marked.parentNode;
                while (marked.firstChild) {
                    parent.insertBefore(marked.firstChild, marked);
                }
                parent.removeChild(marked);
                parent.normalize();
            }
        } catch (err) {
            console.error('Delete mark failed:', err);
            alert('Nie udało się usunąć.');
        }
    }
})();
