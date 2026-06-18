/* ═══════════════════════════════════════════
   IMED PREDICTOR — auth.js
   Firebase Auth — Demo Login Controller
   ════════════════════════════════════════════ */

(function () {
  'use strict';

  // ─── Credenciales demo (visibles en pantalla para el evaluador) ───
  const DEMO_EMAIL    = 'demo@imedpredictor.com';
  const DEMO_PASSWORD = 'ImedDemo2026!';

  // ─── Esperar a que Firebase esté listo ───
  function waitForFirebase(cb, retries = 20) {
    if (typeof firebase !== 'undefined' && firebase.apps && firebase.apps.length > 0) {
      cb();
    } else if (retries > 0) {
      setTimeout(() => waitForFirebase(cb, retries - 1), 200);
    } else {
      console.error('IMED Auth: Firebase no disponible.');
    }
  }

  waitForFirebase(function () {
    const auth       = firebase.auth();
    const loginScreen = document.getElementById('login-screen');
    const appShell   = document.getElementById('app-shell');

    // ─── Estado de autenticación ───
    auth.onAuthStateChanged(function (user) {
      if (user) {
        // Usuario autenticado → ocultar login, mostrar app
        if (loginScreen) loginScreen.classList.add('hidden');
        if (appShell)    appShell.style.display = '';
      } else {
        // Sin sesión → mostrar login, ocultar app
        if (loginScreen) loginScreen.classList.remove('hidden');
        if (appShell)    appShell.style.display = 'none';
      }
    });

    // ─── Autocompletar credenciales demo ───
    window.fillDemoCredentials = function () {
      const emailInput = document.getElementById('login-email');
      const passInput  = document.getElementById('login-password');
      if (emailInput) emailInput.value = DEMO_EMAIL;
      if (passInput)  passInput.value  = DEMO_PASSWORD;
      // Pequeño efecto visual de confirmación
      const btn = document.getElementById('demo-fill-btn');
      if (btn) {
        btn.textContent = '✓ Listo — presiona Ingresar';
        btn.style.background = 'rgba(50, 215, 75, 0.15)';
        btn.style.borderColor = 'rgba(50, 215, 75, 0.3)';
        btn.style.color = '#32D74B';
        setTimeout(() => {
          btn.textContent = '↓ Usar credenciales demo';
          btn.style.background = '';
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 2500);
      }
    };

    // ─── Submit del formulario ───
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email    = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const btn      = document.getElementById('login-submit-btn');
        const errorEl  = document.getElementById('login-error');

        // Limpiar error previo
        errorEl.classList.remove('visible');
        errorEl.textContent = '';

        // Estado de carga
        btn.disabled     = true;
        btn.innerHTML    = '<span class="login-btn-spinner"></span> Autenticando…';

        try {
          await auth.signInWithEmailAndPassword(email, password);
          // onAuthStateChanged se encargará de la transición
        } catch (err) {
          btn.disabled  = false;
          btn.innerHTML = '⚡ Ingresar al Sistema';

          let msg = 'Error de autenticación. Verifica las credenciales.';
          if (err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') {
            msg = 'Credenciales incorrectas. Usa las credenciales demo indicadas arriba.';
          } else if (err.code === 'auth/too-many-requests') {
            msg = 'Demasiados intentos fallidos. Espera unos minutos e intenta nuevamente.';
          } else if (err.code === 'auth/network-request-failed') {
            msg = 'Sin conexión a internet. Verifica tu red e intenta nuevamente.';
          }

          errorEl.textContent = msg;
          errorEl.classList.add('visible');
        }
      });
    }

    // ─── Logout ───
    window.imedLogout = function () {
      auth.signOut().then(() => {
        window.location.reload();
      });
    };
  });

})();
