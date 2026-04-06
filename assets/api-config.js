(() => {
  const STORAGE_KEY = 'langgraph-realworld-api-config';

  const CASES = {
    '01': {
      label: 'Caso 01 · Soporte Omnicanal',
      envPath: 'cases/01-soporte-cliente-omnicanal/backend/.env',
    },
    '02': {
      label: 'Caso 02 · Mesa de Ayuda TI',
      envPath: 'cases/02-mesa-ayuda-ti-runbooks/backend/.env',
    },
    '09': {
      label: 'Caso 09 · RRHH Screening Agenda',
      envPath: 'cases/09-rrhh-screening-agenda/backend/.env',
    },
    '10': {
      label: 'Caso 10 · Onboarding Empleados',
      envPath: 'cases/10-onboarding-empleados/backend/.env',
    },
    '13': {
      label: 'Caso 13 · BI Analista de Datos',
      envPath: 'cases/13-bi-analista-datos/backend/.env',
    },
  };

  const FIELD_DEFS = [
    {
      key: 'OPENAI_API_KEY',
      label: 'OpenAI API Key',
      placeholder: 'sk-...',
      link: 'https://platform.openai.com/api-keys',
      help: 'Activa el modo LIVE con LLM en los casos 01, 02, 09, 10 y 13.',
      cases: ['01', '02', '09', '10', '13'],
    },
    {
      key: 'OPENAI_MODEL',
      label: 'Modelo OpenAI',
      placeholder: 'gpt-4o-mini',
      link: 'https://platform.openai.com/docs/models',
      help: 'Relacionado al caso 01 para elegir el modelo del enrutador.',
      cases: ['01'],
      defaultValue: 'gpt-4o-mini',
    },
    {
      key: 'MODEL',
      label: 'Modelo LLM',
      placeholder: 'gpt-4.1',
      link: 'https://platform.openai.com/docs/models',
      help: 'Relacionado a los casos 09 y 10 para scoring o checklist personalizado.',
      cases: ['09', '10'],
    },
    {
      key: 'AWS_ACCESS_KEY_ID',
      label: 'AWS Access Key ID',
      placeholder: 'AKIA...',
      link: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html',
      help: 'Permite storage real en caso 09 y permisos IAM reales en caso 10.',
      cases: ['09', '10'],
    },
    {
      key: 'AWS_SECRET_ACCESS_KEY',
      label: 'AWS Secret Access Key',
      placeholder: '...',
      link: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html',
      help: 'Par requerido junto a AWS_ACCESS_KEY_ID para casos 09 y 10.',
      cases: ['09', '10'],
      secret: true,
    },
    {
      key: 'AWS_DEFAULT_REGION',
      label: 'AWS Region',
      placeholder: 'us-east-1',
      link: 'https://docs.aws.amazon.com/general/latest/gr/rande.html',
      help: 'Región usada por storage o IAM real en casos 09 y 10.',
      cases: ['09', '10'],
      defaultValue: 'us-east-1',
    },
    {
      key: 'S3_BUCKET',
      label: 'S3 Bucket',
      placeholder: 'rrhh-cv-bucket',
      link: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html',
      help: 'Bucket para CVs y uploads del caso 09.',
      cases: ['09'],
    },
    {
      key: 'RESUME_STORAGE_DIR',
      label: 'Directorio de CVs',
      placeholder: '/app/uploads',
      link: 'https://docs.docker.com/engine/storage/volumes/',
      help: 'Ruta local alternativa para CVs en caso 09.',
      cases: ['09'],
    },
    {
      key: 'SMTP_HOST',
      label: 'SMTP Host',
      placeholder: 'smtp.gmail.com',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Email real para notificaciones del caso 09.',
      cases: ['09'],
    },
    {
      key: 'SMTP_PORT',
      label: 'SMTP Port',
      placeholder: '587',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Puerto SMTP del caso 09.',
      cases: ['09'],
      defaultValue: '587',
    },
    {
      key: 'SMTP_USER',
      label: 'SMTP User',
      placeholder: 'rrhh@empresa.com',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Usuario SMTP usado por el caso 09.',
      cases: ['09'],
    },
    {
      key: 'SMTP_PASS',
      label: 'SMTP Password',
      placeholder: '...',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Password o app password SMTP del caso 09.',
      cases: ['09'],
      secret: true,
    },
    {
      key: 'SMTP_USE_TLS',
      label: 'SMTP TLS',
      placeholder: 'true',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Define TLS para notificaciones del caso 09.',
      cases: ['09'],
      defaultValue: 'true',
    },
    {
      key: 'SENDGRID_API_KEY',
      label: 'SendGrid API Key',
      placeholder: 'SG....',
      link: 'https://app.sendgrid.com/settings/api_keys',
      help: 'Proveedor alternativo de email para el caso 09.',
      cases: ['09'],
      secret: true,
    },
    {
      key: 'SENDGRID_FROM_EMAIL',
      label: 'Email remitente',
      placeholder: 'rrhh@tu-dominio.cl',
      link: 'https://docs.sendgrid.com/ui/sending-email/sender-verification',
      help: 'Sender verificado de SendGrid en el caso 09.',
      cases: ['09'],
    },
    {
      key: 'GOOGLE_OAUTH_CREDENTIALS_JSON',
      label: 'Google OAuth Credentials JSON',
      placeholder: '/run/secrets/google_credentials.json',
      link: 'https://developers.google.com/workspace/guides/create-credentials',
      help: 'Ruta al archivo OAuth2 para Google Calendar en el caso 09.',
      cases: ['09'],
    },
    {
      key: 'GOOGLE_OAUTH_TOKEN_JSON',
      label: 'Google OAuth Token JSON',
      placeholder: '/app/token.json',
      link: 'https://developers.google.com/calendar/api/quickstart/python',
      help: 'Token persistido para Google Calendar del caso 09.',
      cases: ['09'],
    },
    {
      key: 'GOOGLE_CALENDAR_ID',
      label: 'Google Calendar ID',
      placeholder: 'primary',
      link: 'https://support.google.com/calendar/answer/37111',
      help: 'Calendario usado para entrevistas del caso 09.',
      cases: ['09'],
      defaultValue: 'primary',
    },
    {
      key: 'GOOGLE_ADMIN_CREDENTIALS_JSON',
      label: 'Google Admin Credentials JSON',
      placeholder: '/ruta/a/service-account.json',
      link: 'https://developers.google.com/admin-sdk/directory/v1/guides/delegation',
      help: 'Cuenta de servicio para provisionar Google Workspace en el caso 10.',
      cases: ['10'],
    },
    {
      key: 'SLACK_BOT_TOKEN',
      label: 'Slack Bot Token',
      placeholder: 'xoxb-...',
      link: 'https://api.slack.com/apps',
      help: 'Provisiona usuario/canales y notificaciones reales del caso 10.',
      cases: ['10'],
      secret: true,
    },
    {
      key: 'GITHUB_TOKEN',
      label: 'GitHub Token',
      placeholder: 'ghp_...',
      link: 'https://github.com/settings/tokens',
      help: 'Permisos y teams reales del caso 10.',
      cases: ['10'],
      secret: true,
    },
    {
      key: 'SMTP_SERVER',
      label: 'SMTP Server',
      placeholder: 'smtp.gmail.com',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Servidor SMTP para bienvenida real del caso 10.',
      cases: ['10'],
    },
    {
      key: 'SMTP_PORT',
      label: 'SMTP Port',
      placeholder: '587',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Puerto SMTP del caso 10.',
      cases: ['10'],
      defaultValue: '587',
    },
    {
      key: 'SMTP_USER',
      label: 'SMTP User',
      placeholder: 'noreply@empresa.com',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Usuario SMTP del caso 10.',
      cases: ['10'],
    },
    {
      key: 'SMTP_PASS',
      label: 'SMTP Password',
      placeholder: '...',
      link: 'https://support.google.com/mail/answer/7126229',
      help: 'Password o app password SMTP del caso 10.',
      cases: ['10'],
      secret: true,
    },
  ];

  function getStore() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (error) {
      console.error('No se pudo leer la configuracion guardada', error);
      return {};
    }
  }

  function saveStore(values) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
  }

  function fieldValue(store, field) {
    if (typeof store[field.key] === 'string') return store[field.key];
    return field.defaultValue || '';
  }

  function envLinesForCase(caseId, store) {
    return FIELD_DEFS
      .filter((field) => field.cases.includes(caseId))
      .map((field) => `${field.key}=${fieldValue(store, field)}`)
      .join('\n');
  }

  function download(filename, content) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function filterFields(caseIds) {
    return FIELD_DEFS.filter((field) => field.cases.some((caseId) => caseIds.includes(caseId)));
  }

  function mount() {
    const rawCaseIds = (document.body.dataset.apiConfigCases || '').split(',').map((item) => item.trim()).filter(Boolean);
    if (!rawCaseIds.length) return;

    const pageTitle = document.body.dataset.apiConfigTitle || 'Centro de APIs';
    const fields = filterFields(rawCaseIds);
    const store = getStore();

    const style = document.createElement('style');
    style.textContent = `
      .api-config-fab {
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 999;
        border: 1px solid rgba(255,255,255,0.16);
        background: linear-gradient(135deg, rgba(20, 115, 230, 0.95), rgba(14, 165, 164, 0.92));
        color: #fff;
        border-radius: 999px;
        padding: 12px 18px;
        font: 600 14px/1.2 Inter, system-ui, sans-serif;
        cursor: pointer;
        box-shadow: 0 18px 36px rgba(0,0,0,0.28);
      }
      .api-config-backdrop {
        position: fixed;
        inset: 0;
        z-index: 1100;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(3, 8, 20, 0.78);
        backdrop-filter: blur(8px);
        padding: 18px;
      }
      .api-config-backdrop.is-open { display: flex; }
      .api-config-modal {
        width: min(1080px, 100%);
        max-height: 88vh;
        overflow: auto;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.12);
        background: #0f1726;
        color: #e5eefb;
        box-shadow: 0 30px 80px rgba(0,0,0,0.45);
        font-family: Inter, system-ui, sans-serif;
      }
      .api-config-header {
        padding: 24px 24px 18px;
        border-bottom: 1px solid rgba(255,255,255,0.09);
        display: flex;
        gap: 16px;
        align-items: flex-start;
        justify-content: space-between;
      }
      .api-config-header h2 {
        margin: 0 0 8px;
        font-size: 26px;
      }
      .api-config-header p {
        margin: 0;
        color: #9eb0c9;
        line-height: 1.5;
      }
      .api-config-close {
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(255,255,255,0.04);
        color: #fff;
        border-radius: 12px;
        width: 44px;
        height: 44px;
        font-size: 22px;
        cursor: pointer;
      }
      .api-config-summary {
        padding: 18px 24px 0;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
      }
      .api-config-box {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 14px;
        background: rgba(255,255,255,0.03);
      }
      .api-config-box strong {
        display: block;
        margin-bottom: 6px;
      }
      .api-config-cases {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
      .api-config-chip {
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 4px 10px;
        font-size: 12px;
        color: #86d0ff;
        background: rgba(56, 189, 248, 0.08);
      }
      .api-config-form {
        padding: 24px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
      }
      .api-config-field {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 16px;
        background: rgba(255,255,255,0.025);
      }
      .api-config-field label {
        display: block;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .api-config-field small {
        display: block;
        margin-top: 8px;
        color: #97a8be;
        line-height: 1.45;
      }
      .api-config-field input {
        width: 100%;
        box-sizing: border-box;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(5, 10, 20, 0.75);
        color: #fff;
        border-radius: 12px;
        padding: 12px 14px;
      }
      .api-config-links {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
      }
      .api-config-links a {
        color: #80d8ff;
        text-decoration: none;
        font-size: 12px;
      }
      .api-config-actions {
        padding: 0 24px 24px;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
      }
      .api-config-actions button,
      .api-config-actions select {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(255,255,255,0.04);
        color: #fff;
        padding: 12px 14px;
        cursor: pointer;
      }
      .api-config-actions button.primary {
        background: linear-gradient(135deg, #1d4ed8, #0891b2);
      }
      .api-config-note {
        padding: 0 24px 24px;
        color: #9eb0c9;
        font-size: 13px;
        line-height: 1.5;
      }
      .api-config-status {
        min-height: 20px;
        color: #86efac;
        font-size: 13px;
      }
      @media (max-width: 720px) {
        .api-config-fab {
          right: 14px;
          left: 14px;
          bottom: 14px;
          border-radius: 18px;
        }
        .api-config-header h2 { font-size: 22px; }
      }
    `;
    document.head.appendChild(style);

    const fab = document.createElement('button');
    fab.type = 'button';
    fab.className = 'api-config-fab';
    fab.textContent = rawCaseIds.length > 1 ? 'Configurar APIs del portfolio' : 'Configurar APIs de este caso';

    const backdrop = document.createElement('div');
    backdrop.className = 'api-config-backdrop';

    const caseChips = rawCaseIds
      .map((caseId) => CASES[caseId])
      .filter(Boolean)
      .map((item) => `<span class="api-config-chip">${item.label}</span>`)
      .join('');

    const fieldMarkup = fields.map((field) => {
      const cases = field.cases
        .filter((caseId) => rawCaseIds.includes(caseId))
        .map((caseId) => CASES[caseId]?.label || caseId)
        .join(' · ');
      const value = String(fieldValue(store, field)).replace(/"/g, '&quot;');
      const type = field.secret ? 'password' : 'text';
      return `
        <div class="api-config-field">
          <label for="cfg-${field.key}">${field.label}</label>
          <input id="cfg-${field.key}" name="${field.key}" type="${type}" value="${value}" placeholder="${field.placeholder || ''}" autocomplete="off" spellcheck="false" />
          <small><strong>Variable:</strong> ${field.key}</small>
          <small><strong>Casos vinculados:</strong> ${cases}</small>
          <small><strong>Uso:</strong> ${field.help}</small>
          <small><strong>Estado:</strong> opcional. Si queda vacío, el caso sigue en DEMO.</small>
          <div class="api-config-links">
            <a href="${field.link}" target="_blank" rel="noreferrer">Dónde obtenerlo</a>
          </div>
        </div>
      `;
    }).join('');

    const caseOptions = rawCaseIds
      .map((caseId) => `<option value="${caseId}">${CASES[caseId]?.label || caseId}</option>`)
      .join('');

    backdrop.innerHTML = `
      <div class="api-config-modal" role="dialog" aria-modal="true" aria-label="${pageTitle}">
        <div class="api-config-header">
          <div>
            <h2>${pageTitle}</h2>
            <p>Completa solo las APIs que realmente usarás. Puedes exportar el archivo <code>.env</code> del caso cuando quieras y solo se guardara en el navegador si tu lo decides.</p>
          </div>
          <button type="button" class="api-config-close" aria-label="Cerrar">×</button>
        </div>
        <div class="api-config-summary">
          <div class="api-config-box">
            <strong>Casos cubiertos</strong>
            <div class="api-config-cases">${caseChips}</div>
          </div>
          <div class="api-config-box">
            <strong>Ruta esperada</strong>
            <div>Instalación profesional: copia <code>.env.example</code> a <code>.env</code> y luego pega el export.</div>
          </div>
          <div class="api-config-box">
            <strong>Comportamiento</strong>
            <div>Las credenciales no son obligatorias. Sin ellas, el backend sigue funcionando en modo demo.</div>
          </div>
          <div class="api-config-box">
            <strong>Seguridad local</strong>
            <div>Solo se guarda en <code>localStorage</code> si pulsas guardar. Ese almacenamiento no esta cifrado: usalo solo en un equipo confiable.</div>
          </div>
        </div>
        <form class="api-config-form">${fieldMarkup}</form>
        <div class="api-config-actions">
          <button type="button" class="primary" data-action="save">Guardar localmente</button>
          <button type="button" data-action="copy">Copiar .env</button>
          <button type="button" data-action="download">Descargar .env</button>
          <button type="button" data-action="clear">Borrar guardado local</button>
          <select data-role="case-select">${caseOptions}</select>
          <div class="api-config-status" data-role="status"></div>
        </div>
        <div class="api-config-note">
          Esta ventana no modifica automáticamente archivos del backend. <strong>Copiar</strong> y <strong>Descargar</strong> exportan el contenido actual del formulario sin persistirlo. Solo <strong>Guardar localmente</strong> deja valores en este navegador, en texto claro dentro de <code>localStorage</code>.
        </div>
      </div>
    `;

    function openModal() {
      backdrop.classList.add('is-open');
    }

    function closeModal() {
      backdrop.classList.remove('is-open');
    }

    function collectValues(options = {}) {
      const persist = options.persist === true;
      const next = getStore();
      fields.forEach((field) => {
        const input = backdrop.querySelector(`[name="${field.key}"]`);
        next[field.key] = input ? input.value.trim() : '';
      });
      if (persist) {
        saveStore(next);
      }
      return next;
    }

    function selectedCaseId() {
      const select = backdrop.querySelector('[data-role="case-select"]');
      return select ? select.value : rawCaseIds[0];
    }

    function setStatus(message) {
      const status = backdrop.querySelector('[data-role="status"]');
      if (status) status.textContent = message;
    }

    fab.addEventListener('click', openModal);
    backdrop.addEventListener('click', (event) => {
      if (event.target === backdrop) closeModal();
    });
    backdrop.querySelector('.api-config-close').addEventListener('click', closeModal);
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeModal();
    });

    backdrop.querySelector('[data-action="save"]').addEventListener('click', () => {
      collectValues({ persist: true });
      setStatus('Valores guardados localmente en este navegador.');
    });

    backdrop.querySelector('[data-action="copy"]').addEventListener('click', async () => {
      const values = collectValues();
      const caseId = selectedCaseId();
      const content = envLinesForCase(caseId, values);
      try {
        await navigator.clipboard.writeText(content);
        setStatus(`Contenido .env copiado para ${CASES[caseId]?.label || caseId}.`);
      } catch (error) {
        console.error(error);
        setStatus('No pude copiar al portapapeles. Usa Descargar .env.');
      }
    });

    backdrop.querySelector('[data-action="download"]').addEventListener('click', () => {
      const values = collectValues();
      const caseId = selectedCaseId();
      download(`case-${caseId}.env`, envLinesForCase(caseId, values));
      setStatus(`Archivo .env descargado para ${CASES[caseId]?.label || caseId}.`);
    });

    backdrop.querySelector('[data-action="clear"]').addEventListener('click', () => {
      localStorage.removeItem(STORAGE_KEY);
      fields.forEach((field) => {
        const input = backdrop.querySelector(`[name="${field.key}"]`);
        if (input) input.value = field.defaultValue || '';
      });
      setStatus('Valores borrados del almacenamiento local del navegador.');
    });

    document.body.appendChild(fab);
    document.body.appendChild(backdrop);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();

