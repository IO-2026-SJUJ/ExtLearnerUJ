/* Animuje słupki wyników obszarów po załadowaniu strony. */
(function () {
    'use strict';

    const bars = document.querySelectorAll('.area-bar__fill');
    if (!bars.length) return;

    // Przy redukcji ruchu od razu ustawiamy docelowy stan
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    bars.forEach((bar, i) => {
        const target = bar.dataset.score || '0';
        if (reduce) {
            bar.style.width = target + '%';
        } else {
            setTimeout(() => { bar.style.width = target + '%'; }, 100 + i * 120);
        }
    });
})();
