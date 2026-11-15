const rotation = document.querySelector('.sx-promo-rotation');
if (rotation) {
  const slides = [...rotation.querySelectorAll('.sx-promo-slide')];
  const controls = rotation.querySelector('.sx-promo-controls');
  const choices = [...controls.querySelectorAll('button:not(.sx-promo-pause)')];
  const pause = controls.querySelector('.sx-promo-pause');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reducedMotion.matches;
  let active = 0;
  let timer;
  function select(index) {
    slides[active].hidden = true;
    choices[active].removeAttribute('aria-current');
    active = index;
    slides[active].hidden = false;
    choices[active].setAttribute('aria-current', 'true');
  }
  function schedule() {
    clearInterval(timer);
    if (!paused && !document.hidden && !rotation.matches(':hover, :focus-within')) {
      timer = setInterval(() => select((active + 1) % slides.length), 6000);
    }
  }
  function updatePause() {
    pause.textContent = paused ? '▶' : 'Ⅱ';
    pause.setAttribute('aria-label', paused ? 'Запустить смену товаров' : 'Остановить смену товаров');
    schedule();
  }
  choices.forEach((button, index) => button.addEventListener('click', () => select(index)));
  pause.addEventListener('click', () => { paused = !paused; updatePause(); });
  reducedMotion.addEventListener('change', () => { paused = reducedMotion.matches; updatePause(); });
  for (const event of ['mouseenter', 'mouseleave', 'focusin', 'focusout']) {
    rotation.addEventListener(event, () => requestAnimationFrame(schedule));
  }
  document.addEventListener('visibilitychange', schedule);
  controls.hidden = false;
  updatePause();
}

const mobileNav = document.querySelector('.sx-mobile-nav');
if (mobileNav) {
  let previousScroll = Math.max(0, window.scrollY);
  let pending = false;
  window.addEventListener('scroll', () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      const position = Math.max(0, window.scrollY);
      const delta = position - previousScroll;
      if (position < 48 || delta < -5) mobileNav.classList.remove('is-compact');
      else if (position > 85 && delta > 5) mobileNav.classList.add('is-compact');
      if (Math.abs(delta) > 5 || position < 48) previousScroll = position;
      pending = false;
    });
  }, { passive: true });
}
