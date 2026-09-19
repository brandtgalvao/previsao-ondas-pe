// Cadastro do sistema-piloto de alertas de ondas (Grande/Extrema).
// Independente do app.js: fala diretamente com o Supabase via REST usando
// a anon key publica (config em alerts-config.js), protegida por RLS.
(function () {
  function isConfigured() {
    return !!(window.ALERTS_CONFIG && window.ALERTS_CONFIG.supabaseUrl && window.ALERTS_CONFIG.supabaseAnonKey);
  }

  async function populatePlaces(select) {
    try {
      const res = await fetch("data/forecast.json", { cache: "no-store" });
      const data = await res.json();
      select.innerHTML = "";
      for (const [id, place] of Object.entries(data.places)) {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = place.label;
        select.appendChild(opt);
      }
    } catch (e) {
      select.innerHTML = '<option value="">(não foi possível carregar as praias)</option>';
    }
  }

  function wireConditionalFields(form) {
    const emailCk = form.querySelector('[name="canal_email"]');
    const emailInput = form.querySelector('[name="email"]');
    const smsCk = form.querySelector('[name="canal_sms"]');
    const telInput = form.querySelector('[name="telefone"]');
    function sync() {
      emailInput.disabled = !emailCk.checked;
      telInput.disabled = !smsCk.checked;
    }
    emailCk.addEventListener("change", sync);
    smsCk.addEventListener("change", sync);
    sync();
  }

  function showMsg(el, text, isError) {
    el.hidden = false;
    el.textContent = text;
    el.className = "alerts-msg" + (isError ? " alerts-msg-error" : " alerts-msg-ok");
  }

  async function submitForm(form, msgEl) {
    const fd = new FormData(form);
    const canalEmail = fd.get("canal_email") === "on";
    const canalSms = fd.get("canal_sms") === "on";
    if (!canalEmail && !canalSms) {
      showMsg(msgEl, "Selecione pelo menos um canal (e-mail ou SMS).", true);
      return;
    }
    if (canalEmail && !fd.get("email")) {
      showMsg(msgEl, "Informe um e-mail ou desmarque o canal E-mail.", true);
      return;
    }
    if (canalSms && !fd.get("telefone")) {
      showMsg(msgEl, "Informe um telefone ou desmarque o canal SMS.", true);
      return;
    }
    if (!fd.get("consentimento")) {
      showMsg(msgEl, "É necessário concordar com o uso dos dados para se cadastrar.", true);
      return;
    }
    if (!isConfigured()) {
      showMsg(msgEl, "Cadastro ainda não disponível: o sistema de alertas está em configuração.", true);
      return;
    }

    const payload = {
      nome: fd.get("nome"),
      email: canalEmail ? fd.get("email") : null,
      telefone: canalSms ? fd.get("telefone") : null,
      place_id: fd.get("place_id"),
      nivel: fd.get("nivel"),
      canal_email: canalEmail,
      canal_sms: canalSms,
      consentimento: true,
    };

    const submitBtn = form.querySelector(".alerts-submit-btn");
    submitBtn.disabled = true;
    try {
      const res = await fetch(`${window.ALERTS_CONFIG.supabaseUrl}/rest/v1/subscribers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "apikey": window.ALERTS_CONFIG.supabaseAnonKey,
          "Authorization": `Bearer ${window.ALERTS_CONFIG.supabaseAnonKey}`,
          "Prefer": "return=minimal",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      showMsg(msgEl, "Cadastro realizado! Você vai receber um alerta quando a previsão atingir a classe escolhida.", false);
      form.reset();
      wireConditionalFields(form);
    } catch (err) {
      showMsg(msgEl, `Não foi possível concluir o cadastro (${err.message}). Tente novamente mais tarde.`, true);
    } finally {
      submitBtn.disabled = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("alerts-toggle-btn");
    const panel = document.getElementById("alerts-panel");
    const form = document.getElementById("alerts-form");
    const msgEl = document.getElementById("alerts-msg");
    const placeSelect = document.getElementById("alerts-place-select");
    if (!toggleBtn || !panel || !form) return;

    populatePlaces(placeSelect);
    wireConditionalFields(form);

    toggleBtn.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
      toggleBtn.classList.toggle("active", !panel.hidden);
    });

    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      submitForm(form, msgEl);
    });
  });
})();
