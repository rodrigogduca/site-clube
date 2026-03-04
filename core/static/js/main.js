/* ============================================
   Clube de Programação - Home Page Scripts
   ============================================ */

/* ---- NAVBAR SCROLL ---- */
const navbar = document.getElementById('navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
  const currentScroll = window.scrollY;
  if (currentScroll > 40) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
  lastScroll = currentScroll;
}, { passive: true });

/* ---- MOBILE MENU ---- */
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

function resetHamburger(spans) {
  spans[0].style.transform = 'none';
  spans[1].style.opacity = '1';
  spans[2].style.transform = 'none';
  document.body.style.overflow = '';
}

function closeMenu() {
  mobileMenu.classList.remove('open');
  const spans = hamburger.querySelectorAll('span');
  resetHamburger(spans);
}

hamburger.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  const spans = hamburger.querySelectorAll('span');
  if (isOpen) {
    spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
    spans[1].style.opacity = '0';
    spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    document.body.style.overflow = 'hidden';
  } else {
    resetHamburger(spans);
  }
});

// Attach closeMenu to mobile menu links
document.querySelectorAll('#mobileMenu a').forEach(link => {
  link.addEventListener('click', closeMenu);
});

/* ---- INTERSECTION OBSERVER (scroll reveal) ---- */
const observerOptions = {
  threshold: 0.08,
  rootMargin: '0px 0px -60px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right').forEach(el => {
  observer.observe(el);
});

/* ---- CURSOR GLOW (desktop only) ---- */
if (window.matchMedia('(pointer: fine)').matches) {
  const glow = document.getElementById('cursorGlow');
  let mouseX = 0, mouseY = 0;
  let glowX = 0, glowY = 0;
  let animating = false;

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    if (!animating) {
      animating = true;
      animateGlow();
    }
  }, { passive: true });

  function animateGlow() {
    glowX += (mouseX - glowX) * 0.08;
    glowY += (mouseY - glowY) * 0.08;
    glow.style.transform = `translate(${glowX - 200}px, ${glowY - 200}px)`;
    if (Math.abs(mouseX - glowX) > 0.5 || Math.abs(mouseY - glowY) > 0.5) {
      requestAnimationFrame(animateGlow);
    } else {
      animating = false;
    }
  }
} else {
  const glowEl = document.getElementById('cursorGlow');
  if (glowEl) glowEl.style.display = 'none';
}

/* ---- SMOOTH ANCHOR SCROLL ---- */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const offset = 80;
      const position = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top: position, behavior: 'smooth' });
    }
  });
});

/* ---- TYPING ANIMATION (hero subtitle) ---- */
const typingEl = document.querySelector('.hero-typing');
if (typingEl) {
  const text = typingEl.dataset.text;
  typingEl.textContent = '';
  let i = 0;
  function typeChar() {
    if (i < text.length) {
      typingEl.textContent += text[i];
      i++;
      setTimeout(typeChar, 25);
    } else {
      typingEl.classList.add('done');
    }
  }
  const typingObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      typeChar();
      typingObserver.disconnect();
    }
  }, { threshold: 0.5 });
  typingObserver.observe(typingEl);
}

/* ---- COUNTER ANIMATION ---- */
function animateCounters() {
  document.querySelectorAll('.stat-number').forEach(el => {
    const text = el.textContent;
    const match = text.match(/(\d+)/);
    if (!match) return;
    const target = parseInt(match[1]);
    const suffix = text.replace(match[1], '');
    let current = 0;
    const duration = 1500;
    const step = target / (duration / 16);

    function update() {
      current += step;
      if (current >= target) {
        current = target;
        el.innerHTML = target + '<span>' + suffix.trim() + '</span>';
        return;
      }
      el.innerHTML = Math.floor(current) + '<span>' + suffix.trim() + '</span>';
      requestAnimationFrame(update);
    }

    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          update();
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    counterObserver.observe(el);
  });
}

animateCounters();

/* ---- MODAL CONTATO ---- */
const btnContato = document.getElementById('btnContato');
const modalContato = document.getElementById('modalContato');
const modalClose = document.getElementById('modalClose');

btnContato.addEventListener('click', () => {
  modalContato.classList.add('open');
  document.body.style.overflow = 'hidden';
});

modalClose.addEventListener('click', () => {
  modalContato.classList.remove('open');
  document.body.style.overflow = '';
});

modalContato.addEventListener('click', (e) => {
  if (e.target === modalContato) {
    modalContato.classList.remove('open');
    document.body.style.overflow = '';
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modalContato.classList.contains('open')) {
    modalContato.classList.remove('open');
    document.body.style.overflow = '';
  }
});

/* ---- USER AVATAR DROPDOWN ---- */
(function() {
  const avatar = document.querySelector('.user-avatar');
  if (!avatar) return;
  const dropdown = avatar.nextElementSibling;
  if (!dropdown) return;

  avatar.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', function(e) {
    if (!dropdown.contains(e.target) && e.target !== avatar) {
      dropdown.classList.remove('open');
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      dropdown.classList.remove('open');
    }
  });
})();

/* ---- MODAL PROSEL ---- */
const btnProsel = document.getElementById('btnProsel');
const modalProsel = document.getElementById('modalProsel');
const modalProselClose = document.getElementById('modalProselClose');

if (btnProsel) {
  btnProsel.addEventListener('click', () => {
    window.open('https://tally.so/r/J926Po', '_blank');
  });
}

if (modalProsel && modalProselClose) {
  modalProselClose.addEventListener('click', () => {
    modalProsel.classList.remove('open');
    document.body.style.overflow = '';
    // Remove query param from URL
    const url = new URL(window.location);
    url.searchParams.delete('prosel');
    window.history.replaceState({}, '', url);
  });

  modalProsel.addEventListener('click', (e) => {
    if (e.target === modalProsel) {
      modalProsel.classList.remove('open');
      document.body.style.overflow = '';
      const url = new URL(window.location);
      url.searchParams.delete('prosel');
      window.history.replaceState({}, '', url);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalProsel.classList.contains('open')) {
      modalProsel.classList.remove('open');
      document.body.style.overflow = '';
      const url = new URL(window.location);
      url.searchParams.delete('prosel');
      window.history.replaceState({}, '', url);
    }
  });

  // Show thank-you popup if returning from Tally with ?prosel=obrigado
  if (new URLSearchParams(window.location.search).get('prosel') === 'obrigado') {
    modalProsel.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}
