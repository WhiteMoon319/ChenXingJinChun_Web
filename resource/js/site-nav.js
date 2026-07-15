(() => {
  const main = document.querySelector('main');

  if (main && !document.querySelector('.skip-link')) {
    main.id ||= 'main-content';
    const skipLink = document.createElement('a');
    skipLink.className = 'skip-link';
    skipLink.href = `#${main.id}`;
    skipLink.textContent = '跳至正文';
    document.body.prepend(skipLink);
  }

  document.querySelectorAll('.nav-link.active').forEach((link) => {
    link.setAttribute('aria-current', 'page');
  });

  const nav = document.querySelector('.site-nav');
  const inner = nav?.querySelector('.site-nav-inner');
  const links = inner?.querySelector('.nav-links');

  if (!nav || !inner || !links) return;

  nav.setAttribute('aria-label', '主导航');
  links.id ||= 'site-nav-links';

  const button = document.createElement('button');
  button.className = 'nav-toggle';
  button.type = 'button';
  button.setAttribute('aria-label', '导航菜单');
  button.setAttribute('aria-controls', links.id);
  button.setAttribute('aria-expanded', 'false');
  button.innerHTML = '<span></span><span></span><span></span>';
  inner.append(button);
  nav.classList.add('mobile-nav-ready');

  const desktopQuery = matchMedia('(min-width: 600px)');

  const close = () => {
    nav.classList.remove('menu-open');
    button.setAttribute('aria-expanded', 'false');
  };

  const syncViewport = () => {
    close();
    button.hidden = desktopQuery.matches;
  };

  button.addEventListener('click', () => {
    const open = nav.classList.toggle('menu-open');
    button.setAttribute('aria-expanded', String(open));
  });

  links.addEventListener('click', close);
  document.addEventListener('click', (event) => {
    if (!nav.contains(event.target)) close();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav.classList.contains('menu-open')) {
      close();
      button.focus();
    }
  });

  if (desktopQuery.addEventListener) {
    desktopQuery.addEventListener('change', syncViewport);
  } else {
    desktopQuery.addListener(syncViewport);
  }
  syncViewport();
})();
