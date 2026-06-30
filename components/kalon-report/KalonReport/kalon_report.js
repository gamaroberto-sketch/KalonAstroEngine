const KALON_REPORT_VERSION = "1.0.0";

function KalonReport(opts) {
  this.container = typeof opts.container === 'string'
    ? document.querySelector(opts.container)
    : opts.container;
  this.estrategia = opts.estrategia;
  this.nivel = opts.nivel || 'essencial';
  this.formData = {
    nome: opts.nome,
    data_nascimento: opts.data_nascimento,
    hora_nascimento: opts.hora_nascimento || '00:00',
    cidade: opts.cidade,
    data_inicio: opts.data_inicio,
    periodo_meses: opts.periodo_meses || 1
  };
  this.apiBase = opts.apiBase || '';
}

KalonReport.prototype.render = function() {
  // 1. Fetch à API
  fetch(`${this.apiBase}/api/v1/agenda`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...this.formData, estrategia_id: this.estrategia })
  })
  .then(r => r.json())
  .then(dados => this._distribuir(dados))
  .catch(err => console.error('[KalonReport] Erro ao buscar dados:', err));
};

KalonReport.prototype._distribuir = function(dados) {
  const container = this.container;

  // Limpar container
  container.innerHTML = '';

  // Sub-containers para cada bloco
  const divIdentity    = _criarDiv('kr-identity');
  const divAgenda      = _criarDiv('kr-agenda');

  container.appendChild(divIdentity);
  container.appendChild(divAgenda);

  // Distribuir para KalonIdentity
  const ki = new KalonIdentity(divIdentity);
  ki.render(dados.identity, this.nivel);

  // AgendaKalon precisa do template HTML antes de desenhar
  fetch('/components/kalon-report/AgendaKalon/agenda_kalon.html')
    .then(r => r.text())
    .then(html => {
      divAgenda.innerHTML = html;
      const agenda = new AgendaKalon(divAgenda);
      agenda.desenhar(dados);
    });

  // Disparar evento customizado com os dados completos (para uso futuro)
  container.dispatchEvent(new CustomEvent('kalon:dados-prontos', {
    detail: dados,
    bubbles: true
  }));
};

function _criarDiv(className) {
  const d = document.createElement('div');
  d.className = className;
  return d;
}
