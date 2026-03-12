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

/* ---- CUSTOM NUMBER INPUT BUTTONS ---- */
(function() {
  document.querySelectorAll('.tool-number-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var input = this.closest('.tool-number-wrap').querySelector('input[type="number"]');
      if (!input) return;
      var step = parseFloat(input.step) || 1;
      var min = parseFloat(input.min);
      var max = parseFloat(input.max);
      var current = parseFloat(input.value) || 0;
      var dir = this.dataset.dir;

      if (dir === 'up') {
        current = Math.round((current + step) * 10) / 10;
        if (!isNaN(max)) current = Math.min(current, max);
      } else {
        current = Math.round((current - step) * 10) / 10;
        if (!isNaN(min)) current = Math.max(current, min);
      }

      input.value = current;
      input.dispatchEvent(new Event('input'));
    });
  });
})();

/* ---- PASSEI SENAI? CALCULATOR ---- */
(function() {
  var btnCalcular = document.getElementById('btnCalcularMedia');
  var resultado = document.getElementById('resultadoMedia');

  if (!btnCalcular) return;

  btnCalcular.addEventListener('click', function() {
    var av1Input = document.getElementById('notaAV1');
    var av2Input = document.getElementById('notaAV2');
    var av3Input = document.getElementById('notaAV3');
    var edagInput = document.getElementById('notaEDAG');

    var av1 = parseFloat(av1Input.value);
    var av2 = parseFloat(av2Input.value);
    var av3 = parseFloat(av3Input.value);
    var edag = parseFloat(edagInput.value);

    if (isNaN(av1) || isNaN(av2) || isNaN(av3) || isNaN(edag)) {
      resultado.style.display = 'block';
      resultado.innerHTML = '<div class="result-title">Erro</div><div class="result-detail">Preencha todas as notas antes de calcular.</div>';
      return;
    }

    av1 = Math.max(0, Math.min(10, av1));
    av2 = Math.max(0, Math.min(10, av2));
    av3 = Math.max(0, Math.min(10, av3));
    edag = Math.max(0, Math.min(10, edag));

    // AG = somatório(nota × peso) / 100
    var ag = (av1 * 25 + av2 * 25 + av3 * 30 + edag * 20) / 100;
    var agArredondado = Math.round(ag * 10) / 10;

    // Tabela de notas e pesos
    var tabela =
      '<table class="result-table">' +
        '<thead><tr><th>Avaliação</th><th>Nota</th><th>Peso (%)</th></tr></thead>' +
        '<tbody>' +
          '<tr><td>AV1</td><td>' + av1.toFixed(1) + '</td><td>25%</td></tr>' +
          '<tr><td>AV2</td><td>' + av2.toFixed(1) + '</td><td>25%</td></tr>' +
          '<tr><td>AV3</td><td>' + av3.toFixed(1) + '</td><td>30%</td></tr>' +
          '<tr><td>EDAG</td><td>' + edag.toFixed(1) + '</td><td>20%</td></tr>' +
        '</tbody>' +
      '</table>';

    var explicacao = '<div class="result-detail">A média do semestre é calculada considerando os pesos de cada avaliação: somatório das notas multiplicadas pelos pesos, dividido por 100.</div>';

    resultado.style.display = 'block';

    if (ag >= 7) {
      resultado.innerHTML =
        '<div class="result-section">' +
          '<div class="result-value aprovado">' + agArredondado.toFixed(1) + '</div>' +
          '<div class="result-title">Média do Semestre</div>' +
          '<div class="result-status aprovado-bg">Aprovado!</div>' +
          explicacao + tabela +
        '</div>' +
        '<div class="result-bar"><div class="result-bar-fill green" style="width:' + (ag * 10) + '%"></div></div>';
    } else if (ag >= 3) {
      // Pontuação necessária na Final = (50 - 6 × AG) / 4 (usando AG arredondado)
      var notaFinal = (50 - 6 * agArredondado) / 4;
      notaFinal = Math.round(notaFinal * 10) / 10;
      resultado.innerHTML =
        '<div class="result-section">' +
          '<div class="result-value final">' + agArredondado.toFixed(1) + '</div>' +
          '<div class="result-title">Média do Semestre</div>' +
          '<div class="result-status final-bg">Você irá para a FINAL</div>' +
          explicacao + tabela +
        '</div>' +
        '<div class="result-divider"></div>' +
        '<div class="result-section">' +
          '<div class="result-value final-nota">' + notaFinal.toFixed(1) + '</div>' +
          '<div class="result-title">Pontuação para Aprovação</div>' +
          '<div class="result-detail">Este é o quanto você precisa na Final.</div>' +
          '<div class="result-detail">O estudante que não obtiver AG igual ou superior a 7,0 poderá fazer Avaliação Final (AF), em caráter de recuperação.</div>' +
          '<div class="result-formula">Pontuação necessária = (50 - 6 × AG) / 4</div>' +
        '</div>' +
        '<div class="result-bar"><div class="result-bar-fill orange" style="width:' + (ag * 10) + '%"></div></div>';
    } else {
      resultado.innerHTML =
        '<div class="result-section">' +
          '<div class="result-value reprovado">' + agArredondado.toFixed(1) + '</div>' +
          '<div class="result-title">Média do Semestre</div>' +
          '<div class="result-status reprovado-bg">Reprovado</div>' +
          '<div class="result-detail">A média ficou abaixo de 3,0, sem direito à Avaliação Final.</div>' +
          tabela +
        '</div>' +
        '<div class="result-bar"><div class="result-bar-fill red" style="width:' + (ag * 10) + '%"></div></div>';
    }
  });
})();

/* ---- CALCULADORA DE FALTAS ---- */
(function() {
  const btnFaltas = document.getElementById('btnCalcularFaltas');
  const cargaInput = document.getElementById('cargaHoraria');
  const faltasInput = document.getElementById('faltasAtuais');
  const resultado = document.getElementById('resultadoFaltas');

  if (!btnFaltas) return;

  btnFaltas.addEventListener('click', function() {
    var cargaHoras = parseFloat(cargaInput.value);
    var faltasDias = parseInt(faltasInput.value) || 0;

    if (!cargaHoras || cargaHoras <= 0) {
      resultado.style.display = 'block';
      resultado.innerHTML = '<div class="result-title">Erro</div><div class="result-detail">Selecione a carga horária da disciplina.</div>';
      return;
    }

    // Each day = 2 classes of 50 min = 100 min
    // Convert course hours to minutes
    const cargaMinutos = cargaHoras * 60;
    const totalDias = cargaMinutos / 100;
    // Max absences = 25% of total days
    const maxFaltasDias = Math.floor(totalDias * 0.25);
    const faltasRestantes = Math.max(0, maxFaltasDias - faltasDias);
    const percentualUsado = totalDias > 0 ? ((faltasDias / totalDias) * 100) : 0;
    const percentualPresenca = 100 - percentualUsado;

    resultado.style.display = 'block';

    let statusClass, statusText;
    if (faltasDias > maxFaltasDias) {
      statusClass = 'reprovado';
      statusText = 'Reprovado por falta! Você ultrapassou o limite.';
    } else if (faltasRestantes <= 2) {
      statusClass = 'final';
      statusText = 'Cuidado! Você está no limite de faltas.';
    } else {
      statusClass = 'aprovado';
      statusText = 'Você ainda pode faltar.';
    }

    const barWidth = Math.min(100, percentualUsado);
    const barClass = faltasDias > maxFaltasDias ? 'red' : (faltasRestantes <= 2 ? 'orange' : 'green');

    resultado.innerHTML =
      '<div class="result-title">' + statusText + '</div>' +
      '<div class="result-value ' + statusClass + '">' + faltasRestantes + ' dia' + (faltasRestantes !== 1 ? 's' : '') + '</div>' +
      '<div class="result-detail">' +
        'Total de dias letivos: <strong>' + Math.floor(totalDias) + '</strong><br>' +
        'Máximo de faltas permitidas: <strong>' + maxFaltasDias + ' dias</strong><br>' +
        'Faltas acumuladas: <strong>' + faltasDias + ' dias</strong><br>' +
        'Presença atual: <strong>' + percentualPresenca.toFixed(1) + '%</strong>' +
      '</div>' +
      '<div class="result-bar"><div class="result-bar-fill ' + barClass + '" style="width:' + (100 - barWidth) + '%"></div></div>';
  });
})();
