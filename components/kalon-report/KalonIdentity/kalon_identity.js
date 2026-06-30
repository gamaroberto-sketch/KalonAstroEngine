const NOMES_PLANETAS_PT = {
  'sol': 'Sol', 'lua': 'Lua', 'mercurio': 'Mercúrio', 'venus': 'Vênus',
  'marte': 'Marte', 'jupiter': 'Júpiter', 'saturno': 'Saturno',
  'urano': 'Urano', 'netuno': 'Netuno', 'plutao': 'Plutão'
};

function KalonIdentity(container) {
  this.el = typeof container === 'string' ? document.querySelector(container) : container;
}

KalonIdentity.prototype.render = function(identity, nivel = "essencial") {
  if (!identity) return;

  // Garante a estrutura básica
  let wrap = this.el.querySelector('.kalon-identity-container');
  if (!wrap) {
    this.el.innerHTML = `
      <div class="kalon-identity-container">
        <div class="ki-header"><h3>Identidade Astrológica</h3></div>
        <div class="ki-body"></div>
        <div class="ki-footer" style="display:none;"></div>
      </div>
    `;
    wrap = this.el.querySelector('.kalon-identity-container');
  }

  const body = wrap.querySelector('.ki-body');
  const footer = wrap.querySelector('.ki-footer');
  let html = '';

  const drawItem = (label, value) => `
    <div class="ki-item">
      <div class="ki-label">${label}</div>
      <div class="ki-value">${value}</div>
    </div>
  `;

  // --- ESSENCIAL ---
  html += '<div class="ki-grid">';
  html += drawItem('Ascendente', identity.asc.texto);
  html += drawItem('Sol', identity.sol.texto);
  html += drawItem('Lua', identity.lua.texto);
  html += drawItem('Meio do Céu', identity.mc.texto);
  html += '</div>';

  // --- EXPLORADOR ---
  if (nivel === 'explorador' || nivel === 'profissional') {
    html += '<div class="ki-grid">';
    const regClassic = identity.asc.regente_do_ascendente.classico.join(' e ');
    html += drawItem('Regente (Clássico)', regClassic);
    html += drawItem('Sistema de Casas', identity.sistema_casas);
    html += drawItem('Zodíaco', identity.zodiaco);
    html += '</div>';
  }

  // --- PROFISSIONAL ---
  if (nivel === 'profissional') {
    html += '<div class="ki-grid">';
    const planetas = ['mercurio', 'venus', 'marte', 'jupiter', 'saturno'];
    planetas.forEach(p => {
        html += drawItem(NOMES_PLANETAS_PT[p] || p, identity[p].texto);
    });
    
    const regMod = identity.asc.regente_do_ascendente.moderno;
    const implMod = identity.asc.regente_do_ascendente.moderno_implementado;
    const modFormat = regMod.map((r, i) => {
        return implMod[i] ? r : `${r} <span class="ki-warning" title="Ainda não calculado">⚠</span>`;
    }).join(' e ');
    
    html += drawItem('Regente (Moderno)', modFormat);
    html += drawItem('Efemérides', identity.efemerides);
    html += drawItem('Local', `${identity.local.cidade} (${identity.local.latitude}, ${identity.local.longitude}) UTC ${identity.local.utc}`);
    html += '</div>';

    footer.innerHTML = `
      <span>Engine v${identity.engine} | ${identity.strategy}</span>
      <span>${identity.report_id}</span>
    `;
    footer.style.display = 'flex';
  } else {
    footer.style.display = 'none';
  }

  body.innerHTML = html;
};
