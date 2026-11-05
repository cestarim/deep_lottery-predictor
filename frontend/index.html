const gameSelect = document.getElementById('game');
const loadButton = document.getElementById('load-data');
const summaryBlock = document.getElementById('summary');
const predictionBlock = document.getElementById('prediction');
const latestBlock = document.getElementById('latest-draw');

function renderNumbers(items, cssClass = 'number') {
  return items.map((item) => `<span class="${cssClass}">${item}</span>`).join('');
}

function renderMetric(label, value) {
  return `
    <div class="metric">
      <p>${label}</p>
      <strong>${value}</strong>
    </div>
  `;
}

async function loadGameData() {
  const game = gameSelect.value;
  const response = await fetch(`/api/lottery/${game}`);
  const payload = await response.json();

  if (!response.ok) {
    summaryBlock.innerHTML = `<p>${payload.error || 'Error al cargar el juego.'}</p>`;
    return;
  }

  const { summary, prediction, latest_draw } = payload;

  summaryBlock.innerHTML = `
    <div class="grid">
      ${renderMetric('Juego', game)}
      ${renderMetric('Última fecha', summary.latest_date)}
      ${renderMetric('Número de sorteos', summary.draw_count)}
      ${renderMetric('Método', prediction.method)}
    </div>
  `;

  predictionBlock.innerHTML = `
    <h3>Predicción base</h3>
    <div class="number-list">
      ${renderNumbers(prediction.main_numbers)}
    </div>
    <div class="number-list" style="margin-top: 20px;">
      ${renderNumbers(prediction.secondary_numbers, 'badge')}
    </div>
  `;

  const latestMain = [
    latest_draw.main_1,
    latest_draw.main_2,
    latest_draw.main_3,
    latest_draw.main_4,
    latest_draw.main_5,
    ...(game === 'bonoloto' ? [latest_draw.main_6] : []),
  ];

  const secondary = game === 'euromillions'
    ? [latest_draw.star_1, latest_draw.star_2]
    : [latest_draw.complementary, latest_draw.reintegro];

  latestBlock.innerHTML = `
    <h3>Último sorteo</h3>
    <p><strong>Fecha:</strong> ${latest_draw.date}</p>
    <div class="number-list">${renderNumbers(latestMain)}</div>
    <div class="number-list" style="margin-top: 20px;">${renderNumbers(secondary, 'badge')}</div>
  `;
}

loadButton.addEventListener('click', loadGameData);
gameSelect.addEventListener('change', loadGameData);
loadGameData();
