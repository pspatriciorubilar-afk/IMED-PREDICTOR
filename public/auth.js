/* ═══════════════════════════════════════════
   IMED PREDICTOR — auth.js
   Firebase Auth — Demo Login Controller
   ════════════════════════════════════════════ */

/* ╔══════════════════════════════════════════════════════════════╗
   ║  ⚠️  CUENTA DEMO — NO MODIFICAR ⚠️                           ║
   ║                                                              ║
   ║  Email   : demo@imedpredictor.com                            ║
   ║  Password: ImedDemo2026!                                     ║
   ║  Role    : DEMO                                              ║
   ║                                                              ║
   ║  Esta cuenta es la cuenta OFICIAL para la postulación        ║
   ║  Capital Semilla CORFO. NO cambiar contraseña, email ni      ║
   ║  rol. NO deshabilitar. NO eliminar. Si se necesita           ║
   ║  restablecer, usar scratch/restore_demo.py.                  ║
   ╚══════════════════════════════════════════════════════════════╝ */

(function () {
  'use strict';

  // ─── Credenciales demo ───
  // ⚠️ NO MODIFICAR — cuenta oficial para postulación Capital Semilla
  const DEMO_EMAIL    = 'demo@imedpredictor.com';
  const DEMO_PASSWORD = 'ImedDemo2026!';

  // ─── Inyectar estilos del modal de logout ───
  const style = document.createElement('style');
  style.textContent = `
    #logout-confirm-overlay {
      position: fixed; inset: 0; z-index: 99999;
      background: rgba(0,0,0,0.65);
      backdrop-filter: blur(4px);
      display: flex; align-items: center; justify-content: center;
      animation: fadeInOverlay 0.15s ease;
    }
    @keyframes fadeInOverlay { from { opacity:0; } to { opacity:1; } }
    #logout-confirm-box {
      background: #0d1117;
      border: 1px solid rgba(255,77,77,0.3);
      border-radius: 16px;
      padding: 32px 36px;
      max-width: 340px; width: 90%;
      text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,0.7), 0 0 40px rgba(255,77,77,0.08) inset;
      animation: slideUpBox 0.2s cubic-bezier(0.16,1,0.3,1);
    }
    @keyframes slideUpBox { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
    #logout-confirm-box .lco-icon  { font-size:32px; margin-bottom:12px; }
    #logout-confirm-box .lco-title { font-size:17px; font-weight:700; color:#fff; margin-bottom:8px; }
    #logout-confirm-box .lco-sub   { font-size:13px; color:#636375; margin-bottom:24px; line-height:1.5; }
    #logout-confirm-box .lco-btns  { display:flex; gap:10px; justify-content:center; }
    #logout-confirm-box .lco-cancel {
      flex:1; padding:11px 0; border-radius:10px; border:1px solid rgba(255,255,255,0.1);
      background:rgba(255,255,255,0.05); color:#aaa; font-size:14px; font-weight:600;
      cursor:pointer; transition:all 0.2s; font-family:inherit;
    }
    #logout-confirm-box .lco-cancel:hover { background:rgba(255,255,255,0.1); color:#fff; }
    #logout-confirm-box .lco-ok {
      flex:1; padding:11px 0; border-radius:10px; border:none;
      background:linear-gradient(135deg,#c0392b,#FF4D4D); color:#fff;
      font-size:14px; font-weight:700; cursor:pointer; transition:all 0.2s; font-family:inherit;
    }
    #logout-confirm-box .lco-ok:hover { filter:brightness(1.15); transform:translateY(-1px); }
  `;
  document.head.appendChild(style);

  // ─── Modal de confirmación de logout (reemplaza confirm()) ───
  function showLogoutConfirm(onConfirm) {
    const overlay = document.createElement('div');
    overlay.id = 'logout-confirm-overlay';
    overlay.innerHTML = `
      <div id="logout-confirm-box">
        <div class="lco-icon">⏻</div>
        <div class="lco-title">Cerrar Sesión</div>
        <div class="lco-sub">¿Estás seguro de que deseas salir del sistema?</div>
        <div class="lco-btns">
          <button class="lco-cancel" id="lco-cancel-btn">Cancelar</button>
          <button class="lco-ok" id="lco-ok-btn">Sí, salir</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    document.getElementById('lco-ok-btn').onclick = function () {
      overlay.remove();
      onConfirm();
    };
    document.getElementById('lco-cancel-btn').onclick = function () {
      overlay.remove();
    };
    // Click fuera = cancelar
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) overlay.remove();
    });
    // Escape = cancelar
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', escHandler); }
    });
  }

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
    const auth        = firebase.auth();
    const loginScreen = document.getElementById('login-screen');
    const appShell    = document.getElementById('app-shell');

    // ─── Autocompletar credenciales demo ───
    window.fillDemoCredentials = function () {
      const emailInput = document.getElementById('login-email');
      const passInput  = document.getElementById('login-password');
      if (emailInput) emailInput.value = DEMO_EMAIL;
      if (passInput)  passInput.value  = DEMO_PASSWORD;
      const btn = document.getElementById('demo-fill-btn');
      if (btn) {
        btn.textContent = '✓ Listo — presiona Ingresar';
        btn.style.background  = 'rgba(50, 215, 75, 0.15)';
        btn.style.borderColor = 'rgba(50, 215, 75, 0.3)';
        btn.style.color       = '#32D74B';
        setTimeout(() => {
          btn.textContent = '↓ Usar credenciales demo';
          btn.style.background = btn.style.borderColor = btn.style.color = '';
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

        errorEl.classList.remove('visible');
        errorEl.textContent = '';
        btn.disabled  = true;
        btn.innerHTML = '<span class="login-btn-spinner"></span> Autenticando…';

        try {
          await auth.signInWithEmailAndPassword(email, password);
        } catch (err) {
          btn.disabled  = false;
          btn.innerHTML = '⚡ Ingresar al Sistema';

          let msg = 'Error de autenticación. Verifica las credenciales.';
          if (['auth/user-not-found','auth/wrong-password','auth/invalid-credential'].includes(err.code)) {
            msg = 'Credenciales incorrectas. Verifica tu email y contraseña.';
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
      auth.signOut().then(() => { window.location.reload(); });
    };

    // ─── Inyectar botón logout y detalles del usuario activo ───
    function injectUserHeaderInfo() {
      const topbarRight = document.querySelector('.topbar-right');
      if (!topbarRight) { setTimeout(injectUserHeaderInfo, 100); return; }
      
      const user = auth.currentUser;
      if (!user) return;

      // 1. Inyectar o actualizar info del usuario (correo y rol) al lado del avatar
      let infoEl = document.getElementById('user-header-info');
      if (!infoEl) {
        infoEl = document.createElement('div');
        infoEl.id = 'user-header-info';
        infoEl.style.cssText = 'display:flex; flex-direction:column; text-align:right; margin-right:8px; font-family:var(--font); justify-content:center;';
        
        const avatar = topbarRight.querySelector('.avatar');
        if (avatar) {
          topbarRight.insertBefore(infoEl, avatar);
        } else {
          topbarRight.appendChild(infoEl);
        }
      }

      const isSuperAdmin = user.email === 'ps.patriciorubilar@gmail.com';
      const roleText = isSuperAdmin ? 'Super Admin' : 'Demo CORFO';
      infoEl.innerHTML = `
        <span style="font-size:11px; font-weight:800; color:#fff; letter-spacing:0.5px">${roleText}</span>
        <span style="font-size:9px; color:#636375; font-weight:500">${user.email}</span>
      `;

      // 2. Personalizar iniciales del avatar
      const avatarEl = topbarRight.querySelector('.avatar');
      if (avatarEl) {
        avatarEl.textContent = isSuperAdmin ? 'PS' : 'DM';
      }

      // 3. Inyectar botón logout
      if (!document.getElementById('logout-btn')) {
        const logoutBtn = document.createElement('button');
        logoutBtn.id        = 'logout-btn';
        logoutBtn.className = 'btn-icon';
        logoutBtn.title     = 'Cerrar sesión';
        logoutBtn.innerHTML = '⏻';
        logoutBtn.style.cssText = 'color:#636375; font-size:18px; transition:color 0.2s; cursor:pointer; margin-left:8px;';
        logoutBtn.onmouseover = function() { this.style.color = '#FF4D4D'; };
        logoutBtn.onmouseout  = function() { this.style.color = '#636375'; };
        logoutBtn.onclick = function () {
          showLogoutConfirm(function () { window.imedLogout(); });
        };
        topbarRight.appendChild(logoutBtn);
      }
    }

    // ─── Controladores del Modal de Registro y Contratación SaaS ───
    let selectedRegPlan = 'BASIC';

    window.openRegistrationModal = function (e) {
      if (e) e.preventDefault();
      document.getElementById('registration-modal').classList.remove('hidden');
      goToRegistrationStep1();
    };

    window.closeRegistrationModal = function () {
      document.getElementById('registration-modal').classList.add('hidden');
    };

    window.selectRegPlan = function (plan) {
      selectedRegPlan = plan;
      // Actualizar selección visual
      const pBasic = document.getElementById('reg-plan-basic');
      const pPro = document.getElementById('reg-plan-pro');
      if (plan === 'BASIC') {
        if (pBasic) pBasic.checked = true;
        if (pPro) pPro.checked = false;
      } else {
        if (pBasic) pBasic.checked = false;
        if (pPro) pPro.checked = true;
      }
    };

    window.goToRegistrationStep2 = function () {
      document.getElementById('reg-step-1').classList.add('hidden');
      document.getElementById('reg-step-2').classList.remove('hidden');
    };

    window.goToRegistrationStep1 = function () {
      document.getElementById('reg-step-2').classList.add('hidden');
      document.getElementById('reg-step-1').classList.remove('hidden');
      document.getElementById('reg-error').style.display = 'none';
      document.getElementById('reg-success').style.display = 'none';
    };

    window.submitRegistration = async function (e) {
      e.preventDefault();
      const tenantId = document.getElementById('reg-tenant-id').value.toLowerCase().replace(/[^a-z0-9]/g, '');
      const name = document.getElementById('reg-tenant-name').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value;
      
      const btn = document.getElementById('btn-reg-submit');
      const errEl = document.getElementById('reg-error');
      const sucEl = document.getElementById('reg-success');

      errEl.style.display = 'none';
      sucEl.style.display = 'none';
      
      if (password.length < 6) {
        errEl.textContent = 'La contraseña debe tener al menos 6 caracteres.';
        errEl.style.display = 'block';
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<span class="login-btn-spinner"></span> Procesando registro y pago...';

      try {
        // Conectar con la pasarela Stripe (Simulado con confirmación)
        const stripeConfirm = confirm(`[STRIPE SECURE] ¿Autorizas la domiciliación de pagos para el plan ${selectedRegPlan}?`);
        if (!stripeConfirm) {
          throw new Error('El pago ha sido cancelado por el usuario.');
        }

        // Llamar a la Cloud Function pública para crear inquilino y cuenta
        const registerFn = firebase.functions().httpsCallable('register_new_tenant');
        const res = await registerFn({ tenantId, name, email, password, plan: selectedRegPlan });

        if (res.data.status === 'success') {
          sucEl.innerHTML = `✅ ${res.data.message}<br><br>Redireccionando al dashboard...`;
          sucEl.style.display = 'block';
          
          // Auto-iniciar sesión
          await auth.signInWithEmailAndPassword(email, password);
          setTimeout(() => {
            closeRegistrationModal();
            window.location.reload();
          }, 2000);
        } else {
          throw new Error(res.data.message);
        }
      } catch (err) {
        console.error(err);
        errEl.textContent = `Fallo en el proceso: ${err.message}`;
        errEl.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Autorizar Pago y Crear Cuenta';
      }
    };

    // Ejecutar inyección al cambiar estado de sesión
    auth.onAuthStateChanged(function (user) {
      if (user) {
        if (loginScreen) loginScreen.classList.add('hidden');
        if (appShell)    appShell.style.display = '';
        setTimeout(injectUserHeaderInfo, 100);
      } else {
        if (loginScreen) loginScreen.classList.remove('hidden');
        if (appShell)    appShell.style.display = 'none';
      }
    });
  });

})();
