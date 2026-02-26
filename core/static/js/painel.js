/* ========================================
   PAINEL JS - Clube de Programacao
   ======================================== */

// ---- Cargo/Setor toggle (adicionar_membro, editar_membro) ----
(function() {
  var cargoSelect = document.getElementById('id_cargo');
  var setorField = document.getElementById('id_setor');
  if (!cargoSelect || !setorField) return;
  var setorGroup = setorField.closest('.form-group');
  function toggleSetor() {
    var cargo = cargoSelect.value;
    if (cargo === 'presidente' || cargo === 'vice_presidente') {
      setorGroup.style.display = 'none';
      setorField.value = '';
    } else {
      setorGroup.style.display = '';
    }
  }
  cargoSelect.addEventListener('change', toggleSetor);
  toggleSetor();
})();

// ---- Password wrapper (adicionar_membro, editar_membro) ----
(function() {
  var inputs = document.querySelectorAll('input[type="password"]');
  if (!inputs.length) return;
  inputs.forEach(function(input) {
    var wrapper = document.createElement('div');
    wrapper.className = 'password-wrapper';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'password-toggle';
    btn.setAttribute('aria-label', 'Mostrar senha');
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    btn.addEventListener('click', function() {
      var isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.innerHTML = isPassword
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    });
    wrapper.appendChild(btn);
  });
})();

// ---- Tab switching (painel_admin) ----
(function () {
  function initTabs() {
    var tabsBar = document.querySelector('.tabs-bar');
    if (!tabsBar) return;

    var panels = document.querySelectorAll('.tab-panel');

    function activateTab(targetId) {
      var buttons = tabsBar.querySelectorAll('.tab-btn');
      buttons.forEach(function (btn) {
        var isActive = btn.getAttribute('data-tab') === targetId;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      });
      panels.forEach(function (panel) {
        panel.classList.toggle('active', panel.id === targetId);
      });
    }

    // Event delegation on the tabs bar
    tabsBar.addEventListener('click', function (e) {
      var btn = e.target.closest('.tab-btn');
      if (!btn) return;
      activateTab(btn.getAttribute('data-tab'));
    });

    var activeSetor = tabsBar.dataset.activeSetor;
    if (activeSetor) {
      activateTab('tab-setor-' + activeSetor);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabs);
  } else {
    initTabs();
  }
})();

// ---- Cargo accordion (painel_admin - Todos os Membros) ----
(function() {
  function initAccordion() {
    var toggles = document.querySelectorAll('.cargo-toggle');
    if (!toggles.length) return;

    toggles.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var targetId = btn.getAttribute('data-target');
        var target = document.getElementById(targetId);
        if (!target) return;
        var isCollapsed = target.classList.contains('collapsed');
        if (isCollapsed) {
          target.classList.remove('collapsed');
          btn.classList.remove('collapsed');
        } else {
          target.classList.add('collapsed');
          btn.classList.add('collapsed');
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccordion);
  } else {
    initAccordion();
  }
})();

// ---- Setor filter for kanban (painel_admin - Todos tab) ----
(function() {
  function initFilter() {
    var filtro = document.getElementById('filtro-setor');
    if (!filtro) return;

    filtro.addEventListener('change', function() {
      var valor = filtro.value;
      var board = filtro.closest('.painel-section').querySelector('.kanban-board');
      if (!board) return;

      var cards = board.querySelectorAll('.kanban-card');
      cards.forEach(function(card) {
        if (valor === 'todos') {
          card.style.display = '';
        } else {
          var setorId = card.getAttribute('data-setor-id');
          card.style.display = (setorId === valor) ? '' : 'none';
        }
      });

      // Update counts in each column header
      var columns = board.querySelectorAll('.kanban-column');
      columns.forEach(function(col) {
        var visibleCards = col.querySelectorAll('.kanban-card:not([style*="display: none"])');
        var countEl = col.querySelector('.kanban-count');
        if (countEl) {
          countEl.textContent = visibleCards.length;
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFilter);
  } else {
    initFilter();
  }
})();

// ---- Rename modal (chat_lista) ----
(function() {
  var modal = document.getElementById('renameModal');
  if (!modal) return;

  window.openRenameModal = function(conversaId, currentName) {
    document.getElementById('renameForm').action = '/painel/chat/' + conversaId + '/renomear/';
    document.getElementById('renameInput').value = currentName;
    modal.classList.add('open');
  };

  window.closeRenameModal = function() {
    modal.classList.remove('open');
  };

  modal.addEventListener('click', function(e) {
    if (e.target === modal) window.closeRenameModal();
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') window.closeRenameModal();
  });
})();

// ---- User avatar dropdown ----
(function() {
  var avatar = document.querySelector('.user-avatar');
  if (!avatar) return;
  var dropdown = avatar.parentElement.querySelector('.user-dropdown');
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
