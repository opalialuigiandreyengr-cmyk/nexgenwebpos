/* =============================================================================
   core/preloader.js — Food & Beverage Startup Splash Preloader Logic
   ========================================================================== */
export function initFoodBeverageSplash() {
  const splash = document.getElementById('app-splash-loader');
  if (!splash) return;

  // Preloader only shows 1 time when first accessing the application in a browser session
  let alreadyShown = false;
  try {
    alreadyShown = sessionStorage.getItem('splash_shown') === '1';
  } catch (e) {}

  if (alreadyShown) {
    try { splash.remove(); } catch (e) {}
    return;
  }

  // Mark as shown for the current session
  try {
    sessionStorage.setItem('splash_shown', '1');
  } catch (e) {}

  const bar = document.getElementById('fb-progress-fill');
  const pctEl = document.getElementById('fb-progress-pct');
  const timerEl = document.getElementById('fb-timer-sec');
  const captionEl = document.getElementById('fb-status-caption');
  const foodIconEl = document.getElementById('fb-food-icon');

  const DURATION_MS = 10000; /* 10s splash sequence */
  const startTime = Date.now();
  let dismissed = false;

  const STAGES = [
    { pct: 0, text: 'Initializing POS terminal & peripheral stations...', icon: '🍔' },
    { pct: 25, text: 'Synchronizing menu catalog, modifiers & recipes...', icon: '🥞' },
    { pct: 50, text: 'Calibrating inventory tables & kitchen routes...', icon: '🍳' },
    { pct: 75, text: 'Connecting Supabase cloud database & logs...', icon: '☕' },
    { pct: 95, text: 'System primed. Opening NEXGEN POS workspace...', icon: '🍕' }
  ];

  function dismiss() {
    if (dismissed) return;
    dismissed = true;
    splash.classList.add('splash-hide');
    setTimeout(() => {
      try { splash.remove(); } catch (e) {}
    }, 450);
  }

  const timer = setInterval(() => {
    if (dismissed) {
      clearInterval(timer);
      return;
    }

    const elapsed = Date.now() - startTime;
    const progress = Math.min(100, (elapsed / DURATION_MS) * 100);
    const remainingSec = Math.max(0, Math.ceil((DURATION_MS - elapsed) / 1000));

    if (bar) bar.style.width = `${progress.toFixed(1)}%`;
    if (pctEl) pctEl.textContent = `${Math.floor(progress)}%`;
    if (timerEl) timerEl.textContent = remainingSec > 0 ? `${remainingSec}s remaining` : 'Ready';

    if (captionEl) {
      for (let i = STAGES.length - 1; i >= 0; i--) {
        if (progress >= STAGES[i].pct) {
          if (captionEl.textContent !== STAGES[i].text) {
            captionEl.textContent = STAGES[i].text;
          }
          if (foodIconEl && foodIconEl.textContent !== STAGES[i].icon) {
            foodIconEl.textContent = STAGES[i].icon;
          }
          break;
        }
      }
    }

    if (elapsed >= DURATION_MS) {
      clearInterval(timer);
      dismiss();
    }
  }, 40);
}
