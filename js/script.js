(() => {
  'use strict';

  // --- Utility Helpers ---
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const saveData = navigator.connection?.saveData === true;

  // --- Navigation & Header ---
  const initNavigation = () => {
    const header = $('[data-header]');
    const menuButton = $('.menu-toggle');
    const mobileMenu = $('#mobile-menu');

    const updateHeader = () => header?.classList.toggle('scrolled', window.scrollY > 18);
    updateHeader();
    window.addEventListener('scroll', updateHeader, { passive: true });

    if (!menuButton || !mobileMenu) return;

    const setMenuOpen = (open) => {
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      mobileMenu.hidden = !open;
    };

    menuButton.addEventListener('click', () => {
      const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
      setMenuOpen(!isOpen);
    });

    $$('a', mobileMenu).forEach(link => {
      link.addEventListener('click', () => setMenuOpen(false));
    });
  };

  // --- Scroll Reveal Animations ---
  const initScrollReveal = () => {
    const revealElements = $$('.reveal');
    if (!revealElements.length) return;

    if ('IntersectionObserver' in window && !reducedMotion) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px' });

      revealElements.forEach(el => observer.observe(el));
    } else {
      revealElements.forEach(el => el.classList.add('is-visible'));
    }
  };

  // --- Cursor Glow & Card Tilt ---
  const initInteractiveFX = () => {
    if (reducedMotion || saveData || !finePointer) return;

    const glow = $('.cursor-glow');
    let mx = 0, my = 0, rafId = 0;

    if (glow) {
      document.addEventListener('pointermove', (event) => {
        mx = event.clientX;
        my = event.clientY;
        if (rafId) return;

        rafId = requestAnimationFrame(() => {
          glow.style.transform = `translate(${mx - 150}px, ${my - 150}px)`;
          rafId = 0;
        });
      }, { passive: true });
    }

    $$('[data-tilt]').forEach(card => {
      card.addEventListener('pointermove', (event) => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = `perspective(900px) rotateX(${-y * 4}deg) rotateY(${x * 5}deg) translateY(-2px)`;
      }, { passive: true });

      card.addEventListener('pointerleave', () => {
        card.style.transform = '';
      });
    });
  };

  // --- Contact Form Handling ---
  const initContactForm = () => {
    const form = $('#contact-form');
    const status = $('[data-form-status]');
    if (!form) return;

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;

      const data = new FormData(form);
      const name = data.get('name') || '';
      const email = data.get('email') || '';
      const message = data.get('message') || '';

      const subject = encodeURIComponent(`Portfolio enquiry from ${name}`);
      const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\n${message}`);

      if (status) status.textContent = 'Opening your email app…';
      window.location.href = `mailto:faisalhasan494@gmail.com?subject=${subject}&body=${body}`;
    });
  };

  // --- Laptop Boot Sequence ---
  const initLaptopSequence = () => {
    const lid = $('#laptop-lid');
    const display = $('#laptop-display');
    const termBody = $('#term-body');

    if (!lid || !display || !termBody) return;

    const logs = [
      { text: '> ESTABLISHING HANDSHAKE...', delay: 400 },
      { text: '> KERNEL INTEGRITY: SECURE', delay: 850 },
      { text: '> ACCESS GRANTED [ID: GUEST]', delay: 1300 },
      { text: '> WELCOME, TRAVELER.', delay: 1850, highlight: true }
    ];

    // Open laptop lid
    setTimeout(() => lid.classList.add('open'), 400);

    // Power screen display
    setTimeout(() => display.classList.add('powered'), 1200);

    // Print terminal lines sequentially
    logs.forEach((log) => {
      setTimeout(() => {
        const line = document.createElement('div');
        line.className = `boot-line${log.highlight ? ' highlight-welcome' : ''}`;
        line.textContent = log.text;
        termBody.appendChild(line);
      }, 1400 + log.delay);
    });

    // Append blinking cursor
    setTimeout(() => {
      const cursorLine = document.createElement('div');
      cursorLine.className = 'boot-line';
      cursorLine.textContent = '> ';

      const cursor = document.createElement('span');
      cursor.className = 'terminal-cursor';
      cursorLine.appendChild(cursor);

      termBody.appendChild(cursorLine);
    }, 3600);
  };

  // --- Footer Year ---
  const initDynamicYear = () => {
    const yearElem = $('[data-year]');
    if (yearElem) {
      yearElem.textContent = new Date().getFullYear();
    }
  };

  // --- Bootstrap ---
  initNavigation();
  initScrollReveal();
  initInteractiveFX();
  initContactForm();
  initDynamicYear();
  initLaptopSequence();
})();