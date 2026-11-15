const rotation = document.querySelector('.sx-promo-rotation');
if (rotation) {
  const slides = [...rotation.querySelectorAll('.sx-promo-slide')];
  const controls = rotation.querySelector('.sx-promo-controls');
  const choices = [...controls.querySelectorAll('button:not(.sx-promo-pause)')];
  const pause = controls.querySelector('.sx-promo-pause');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reducedMotion.matches;
  const canHover = matchMedia('(hover: hover)');
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
    if (!paused && !document.hidden && !rotation.querySelector('.sx-promo-slide:focus, button:focus-visible') && !(canHover.matches && rotation.matches(':hover'))) {
      timer = setInterval(() => select((active + 1) % slides.length), 6000);
    }
  }
  function updatePause() {
    pause.textContent = paused ? '▶' : 'Ⅱ';
    pause.setAttribute('aria-label', paused ? 'Запустить смену товаров' : 'Остановить смену товаров');
    schedule();
  }
  choices.forEach((button, index) => button.addEventListener('click', () => {
    select(index);
    schedule();
  }));
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

const brandTile = document.querySelector('.sx-brand-tile');
if (brandTile) {
  const links = [...brandTile.querySelectorAll('.sx-brand-link')];
  const next = brandTile.querySelector('.sx-brand-next');
  let shown = 0;
  function advance() {
    links[shown].hidden = true;
    shown = (shown + 1) % links.length;
    links[shown].hidden = false;
  }
  next.addEventListener('click', advance);
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
    setInterval(() => {
      if (!document.hidden && !brandTile.matches(':focus-within') &&
          !(matchMedia('(hover: hover)').matches && brandTile.matches(':hover'))) advance();
    }, 4500);
  }
}

const picks = document.querySelector('.sx-picks');
const picksControls = document.querySelector('.sx-picks-controls');
if (picks && picksControls) {
  const [previous, next] = picksControls.querySelectorAll('button');
  function move(direction) {
    const behavior = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    picks.scrollBy({left: direction * picks.clientWidth * 0.8, behavior});
  }
  function sync() {
    const overflow = picks.scrollWidth - picks.clientWidth;
    picksControls.hidden = overflow <= 2;
    previous.disabled = picks.scrollLeft <= 2;
    next.disabled = picks.scrollLeft >= overflow - 2;
  }
  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  picks.addEventListener('scroll', sync, {passive: true});
  new ResizeObserver(sync).observe(picks);
  sync();
}
