const gameSelect = document.getElementById('game');
const loadButton = document.getElementById('load-data');
const summaryBlock = document.getElementById('summary');
const predictionBlock = document.getElementById('prediction');
const latestBlock = document.getElementById('latest-draw');
const statusBlock = document.getElementById('status');

function clear(element) {
  element.replaceChildren();
}

function addText(parent, tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = String(text);
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function renderNumberList(parent, numbers, className = 'number-list', itemClass = 'number') {
  const list = document.createElement('div');
  list.className = className;
  numbers.forEach((number) => addText(list, 'span', number, itemClass));
  parent.append(list);
}

function renderMetric(parent, label, value) {
  const metric = document.createElement('div');
  metric.className = 'metric';
  addText(metric, 'p', label);
  addText(metric, 'strong', value);
  parent.append(metric);
}

async function loadGameData() {
  loadButton.disabled = true;
  statusBlock.textContent = 'Cargando…';
  try {
    const response = await fetch(`/api/lottery/${encodeURIComponent(gameSelect.value)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'No se pudieron cargar los datos.');

    clear(summaryBlock);
    const grid = document.createElement('div');
    grid.className = 'grid';
    renderMetric(grid, 'Juego', payload.game === 'euromillions' ? 'EuroMillions' : 'Bonoloto');
    renderMetric(grid, 'Última fecha de muestra', payload.summary.latest_date);
    renderMetric(grid, 'Sorteos de muestra', payload.summary.draw_count);
    renderMetric(grid, 'Método', 'Frecuencia histórica');
    summaryBlock.append(grid);

    clear(predictionBlock);
    addText(predictionBlock, 'p', payload.prediction.warning, 'notice');
    renderNumberList(predictionBlock, payload.prediction.main_numbers);
    if (payload.game === 'euromillions') {
      addText(predictionBlock, 'h3', 'Estrellas (frecuencia)');
      renderNumberList(predictionBlock, payload.prediction.secondary_numbers, 'number-list', 'badge');
    } else {
      addText(predictionBlock, 'h3', 'Complementario y reintegro (frecuencia)');
      renderNumberList(predictionBlock, [payload.prediction.complementary, payload.prediction.reintegro], 'number-list', 'badge');
    }

    clear(latestBlock);
    const draw = payload.latest_draw;
    addText(latestBlock, 'p', `Fecha: ${draw.date}`);
    const mainCount = payload.game === 'euromillions' ? 5 : 6;
    const main = Array.from({ length: mainCount }, (_, index) => draw[`main_${index + 1}`]);
    renderNumberList(latestBlock, main);
    const secondary = payload.game === 'euromillions'
      ? [draw.star_1, draw.star_2]
      : [draw.complementary, draw.reintegro];
    renderNumberList(latestBlock, secondary, 'number-list', 'badge');
    statusBlock.textContent = 'Datos de ejemplo cargados.';
  } catch (error) {
    statusBlock.textContent = error.message;
    clear(summaryBlock);
    clear(predictionBlock);
    clear(latestBlock);
  } finally {
    loadButton.disabled = false;
  }
}

loadButton.addEventListener('click', loadGameData);
gameSelect.addEventListener('change', loadGameData);
loadGameData();
