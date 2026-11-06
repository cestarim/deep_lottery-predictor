const gameSelect = document.getElementById('game');
const modelSelect = document.getElementById('model');
const loadButton = document.getElementById('load-data');
const summaryBlock = document.getElementById('summary');
const predictionBlock = document.getElementById('prediction');
const latestBlock = document.getElementById('latest-draw');
const backtestBlock = document.getElementById('backtest');
const modelInfoBlock = document.getElementById('model-info');
const statusBlock = document.getElementById('status');

function clear(element) { element.replaceChildren(); }
function addText(parent, tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = String(text);
  if (className) element.className = className;
  parent.append(element);
  return element;
}
function renderNumberList(parent, numbers, itemClass = 'number') {
  const list = document.createElement('div');
  list.className = 'number-list';
  numbers.forEach((value) => addText(list, 'span', value, itemClass));
  parent.append(list);
}
function renderMetric(parent, label, value) {
  const card = document.createElement('div');
  card.className = 'metric';
  addText(card, 'p', label);
  addText(card, 'strong', value);
  parent.append(card);
}

async function loadModels() {
  try {
    const response = await fetch('/api/models');
    const payload = await response.json();
    const entries = Object.entries(payload.models || {});
    modelSelect.innerHTML = entries
      .map(([key, value]) => `<option value="${key}">${value.display_name}</option>`)
      .join('');
    modelSelect.value = 'frequency_baseline';
  } catch (error) {
    statusBlock.textContent = 'No se pudo cargar la lista de modelos.';
  }
}

async function loadGameData() {
  loadButton.disabled = true;
  statusBlock.textContent = 'Cargando…';
  try {
    const response = await fetch(`/api/lottery/${encodeURIComponent(gameSelect.value)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'No se pudieron cargar los datos.');

    clear(summaryBlock);
    const summaryGrid = document.createElement('div');
    summaryGrid.className = 'grid';
    renderMetric(summaryGrid, 'Juego', payload.game === 'euromillions' ? 'EuroMillions' : 'Bonoloto');
    renderMetric(summaryGrid, 'Fecha más reciente', payload.summary.latest_date);
    renderMetric(summaryGrid, 'Sorteos', payload.summary.draw_count);
    summaryBlock.append(summaryGrid);

    clear(predictionBlock);
    addText(predictionBlock, 'p', payload.prediction.warning, 'notice');
    renderNumberList(predictionBlock, payload.prediction.main_numbers);
    if (payload.game === 'euromillions') {
      addText(predictionBlock, 'h3', 'Estrellas por frecuencia');
      renderNumberList(predictionBlock, payload.prediction.secondary_numbers, 'badge');
    } else {
      addText(predictionBlock, 'h3', 'Complementario y reintegro por frecuencia');
      renderNumberList(predictionBlock, [payload.prediction.complementary, payload.prediction.reintegro], 'badge');
    }

    clear(latestBlock);
    const draw = payload.latest_draw;
    addText(latestBlock, 'p', `Fecha: ${draw.date}`);
    const mainCount = payload.game === 'euromillions' ? 5 : 6;
    renderNumberList(latestBlock, Array.from({ length: mainCount }, (_, index) => draw[`main_${index + 1}`]));
    renderNumberList(latestBlock, payload.game === 'euromillions'
      ? [draw.star_1, draw.star_2]
      : [draw.complementary, draw.reintegro], 'badge');

    clear(backtestBlock);
    const backtest = payload.backtest;
    addText(backtestBlock, 'p', `Walk-forward: ${backtest.test_draws} sorteos de prueba.`, 'notice');
    const grid = document.createElement('div');
    grid.className = 'grid';
    renderMetric(grid, 'Aciertos principales promedio', `${backtest.main_average_hits.toFixed(2)} / ${mainCount}`);
    renderMetric(grid, 'Esperado al azar', `${backtest.main_random_expected_hits.toFixed(2)} / sorteo`);
    renderMetric(grid, 'Aciertos secundarios promedio', `${backtest.secondary_average_hits.toFixed(2)} / sorteo`);
    renderMetric(grid, 'Esperado al azar (secundario)', `${backtest.secondary_random_expected_hits.toFixed(2)} / sorteo`);
    if (backtest.reintegro_average_hits !== undefined) {
      renderMetric(grid, 'Aciertos de reintegro promedio', `${backtest.reintegro_average_hits.toFixed(2)} / sorteo`);
      renderMetric(grid, 'Esperado al azar (reintegro)', `${backtest.reintegro_random_expected_hits.toFixed(2)} / sorteo`);
    }
    backtestBlock.append(grid);
    addText(backtestBlock, 'p', backtest.interpretation, 'notice');

    clear(modelInfoBlock);
    const selectedModelName = modelSelect.value;
    const selectedModel = payload.models?.[selectedModelName] || selectedModelName;
    addText(modelInfoBlock, 'p', selectedModel ? `Modelo activo: ${selectedModel}` : 'Modelo activo: frequency_baseline');
    statusBlock.textContent = 'Datos sintéticos de demostración cargados.';
  } catch (error) {
    statusBlock.textContent = error.message;
    [summaryBlock, predictionBlock, latestBlock, backtestBlock, modelInfoBlock].forEach(clear);
  } finally {
    loadButton.disabled = false;
  }
}

loadButton.addEventListener('click', loadGameData);
gameSelect.addEventListener('change', loadGameData);
modelSelect.addEventListener('change', () => {
  const modelName = modelSelect.value;
  statusBlock.textContent = `Modelo seleccionado: ${modelName}`;
});
loadModels();
loadGameData();
