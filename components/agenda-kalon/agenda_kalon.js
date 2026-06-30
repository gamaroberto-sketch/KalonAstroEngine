function AgendaKalon(container) {
  this.el = typeof container === 'string' ? document.querySelector(container) : container;
  this.apiBase = 'http://localhost:8000';
}

AgendaKalon.prototype.render = function(opts) {
  this.formData = opts;
  this._fetch(opts.estrategia);
};

AgendaKalon.prototype._fetch = function(estrategiaId) {
  fetch(`${this.apiBase}/api/v1/agenda`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({...this.formData, estrategia_id: estrategiaId})
  })
  .then(r => r.json())
  .then(dados => this._draw(dados))
  .catch(err => {
    console.error('Kalon Astro erro:', err);
    // Erro básico que pode ser expandido depois
  });
};

AgendaKalon.prototype._draw = function(dados) {
  const colunas = this._descobrirColunas(dados.janelas);
  this.el.querySelector('[data-res-name]').textContent = dados.nome;
  this.el.querySelector('[data-agenda-titulo]').textContent = dados.estrategia_nome;
  this._renderCabecalho(colunas, dados.janelas);
  this._renderAgenda(dados.janelas, colunas);
  this._renderProxima(dados.janelas);
  this._bindAcoes();
  this.el.querySelector('[data-results]').style.display = 'block';
};

AgendaKalon.prototype._bindAcoes = function() {
  const self = this;
  const btnNova = this.el.querySelector('[data-action="nova"]');
  const btnPrint = this.el.querySelector('[data-action="print"]');
  const btnPdf = this.el.querySelector('[data-action="pdf"]');
  const btnPng = this.el.querySelector('[data-action="png"]');

  if (btnNova) btnNova.onclick = function() {
    self.el.querySelector('[data-results]').style.display = 'none';
    window.scrollTo({top:0,behavior:'smooth'});
    // Evento customizável para resetar form externo
    self.el.dispatchEvent(new CustomEvent('agenda:nova'));
  };
  
  if (btnPrint) btnPrint.onclick = () => window.print();
  if (btnPdf) btnPdf.onclick = () => window.print();
  if (btnPng) btnPng.onclick = () => {
    // Para simplificar, exportamos o container principal do calendário
    const alvo = self.el.querySelector('.cal-wrap');
    if(alvo && window.html2canvas) {
      window.html2canvas(alvo, {backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--card').trim() || '#13151A', scale:2}).then(canvas => {
        const a = document.createElement('a');
        a.download = 'kalon-agenda.png';
        a.href = canvas.toDataURL('image/png');
        a.click();
      });
    }
  };
};

AgendaKalon.prototype._descobrirColunas = function(janelas) {
  const cols = new Set();
  janelas.forEach(j => Object.keys(j.campos||{}).forEach(k => cols.add(k)));
  return Array.from(cols);
};

AgendaKalon.prototype._labelDe = function(col, janelas) {
  for (const j of janelas) if (j.campos[col]) return j.campos[col].label;
  return col;
};

AgendaKalon.prototype._renderCabecalho = function(colunas, janelas) {
  const dinamicas = colunas.map(c => this._labelDe(c, janelas));
  const headRow = this.el.querySelector('[data-cal-head-row]');
  headRow.innerHTML = `<tr>
    <th>Data</th>
    <th>Melhor horário</th>
    <th>Janela</th>
    ${dinamicas.map(l => `<th class="center">${l}</th>`).join('')}
    <th>Objetivo</th>
    <th class="center no-print"></th>
  </tr>`;
};

AgendaKalon.prototype._renderAgenda = function(janelas, colunas) {
  const colspanTotal = 4 + colunas.length;
  const self = this;
  this.el.querySelector('[data-cal-body]').innerHTML = janelas.map((item, i) => {
    const celulas = colunas.map(col => {
      const c = item.campos[col];
      const icone = c ? c.icone : '—';
      const cor = c ? c.cor : 'dim';
      return `<td class="td-sym sym-${cor}">${icone}</td>`;
    }).join('');

    const ativos = colunas.filter(c => item.campos[c]).map(c => item.campos[c].label);

    return `
    <tr data-row="${i}">
      <td><div class="date-day">${item.day}</div><div class="date-mon">${item.mon}</div></td>
      <td><div class="time-peak">${item.pico}</div></td>
      <td><div class="time-win">${item.inicio} → ${item.fim}</div></td>
      ${celulas}
      <td class="td-obj">${ativos.length ? ativos.join(' + ') : '—'}</td>
      <td class="td-chevron" data-chev="${i}">›</td>
    </tr>
    <tr class="detail-row" data-detail="${i}">
      <td colspan="${colspanTotal}" class="detail-cell"><div class="detail-box">${this._renderDetalhe(item, colunas)}</div></td>
    </tr>`;
  }).join('');

  this.el.querySelectorAll('[data-row]').forEach(tr => {
    tr.addEventListener('click', () => self._toggleDetail(tr.dataset.row));
  });
};

AgendaKalon.prototype._renderDetalhe = function(item, colunas) {
  return colunas.filter(c => item.campos[c]).map(col => {
    const c = item.campos[col];
    const grupos = c.auditoria.map(grupo => {
      const linhas = grupo.itens.map(it =>
        `<div class="prof-row"><span class="pk">${it.label}</span><span class="pv">${it.valor}</span></div>`
      ).join('');
      return `<div class="prof-sec"><div class="prof-sec-lbl">${grupo.titulo}</div>${linhas}</div>`;
    }).join('');
    return `<div class="campo-bloco"><h4>${c.label}</h4>${grupos}</div>`;
  }).join('');
};

AgendaKalon.prototype._toggleDetail = function(i) {
  const dr = this.el.querySelector(`[data-detail="${i}"]`);
  const row = this.el.querySelector(`[data-row="${i}"]`);
  const isOpen = dr.classList.contains('open');
  this.el.querySelectorAll('.detail-row').forEach(r=>r.classList.remove('open'));
  this.el.querySelectorAll('[data-row]').forEach(r=>r.classList.remove('expanded'));
  
  if (!isOpen) { 
    dr.classList.add('open'); 
    row.classList.add('expanded');
  }
};

AgendaKalon.prototype._renderProxima = function(janelas) {
  const hoje = new Date();
  hoje.setHours(0,0,0,0);
  const MESES = {JAN:0,FEV:1,MAR:2,ABR:3,MAI:4,JUN:5,JUL:6,AGO:7,SET:8,OUT:9,NOV:10,DEZ:11};
  const proxima = janelas.find(item => {
    const mes = MESES[item.mon];
    if (mes === undefined) return false;
    const ano = hoje.getFullYear() + (mes < hoje.getMonth() ? 1 : 0);
    const d = new Date(ano, mes, parseInt(item.day));
    return d >= hoje;
  });
  if (!proxima) return;
  
  const bloco = this.el.querySelector('[data-proxima]');
  const MESES_PT = {JAN:'Jan',FEV:'Fev',MAR:'Mar',ABR:'Abr',MAI:'Mai',JUN:'Jun',JUL:'Jul',AGO:'Ago',SET:'Set',OUT:'Out',NOV:'Nov',DEZ:'Dez'};
  const mes = MESES[proxima.mon];
  const ano = hoje.getFullYear() + (mes < hoje.getMonth() ? 1 : 0);
  const dataProx = new Date(ano, mes, parseInt(proxima.day));
  const diffDias = Math.round((dataProx - hoje) / 86400000);
  
  this.el.querySelector('[data-prox-date]').textContent = proxima.day + ' de ' + (MESES_PT[proxima.mon] || proxima.mon);
  this.el.querySelector('[data-prox-time]').textContent = proxima.pico;
  this.el.querySelector('[data-prox-dias]').textContent = diffDias === 0 ? 'Hoje!' : diffDias === 1 ? 'em 1 dia' : \`em \${diffDias} dias\`;
  bloco.style.display = 'flex';
};
