const gameSelect = document.getElementById('game');
const modelSelect = document.getElementById('model');
const fileInput = document.getElementById('csv-file');
const uploadButton = document.getElementById('upload-data');
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
    modelSelect.replaceChildren();
    Object.entries(payload.models || {}).forEach(([key, value]) => {
      const option = document.createElement('option');
      option.value = key;
      option.textContent = `${value.display_name} (${value.status})`;
      modelSelect.append(option);
    });
    modelSelect.value = 'frequency_baseline';
  } catch (_error) {
    statusBlock.textContent = 'No se pudo cargar la lista de modelos.';
  }
}

async function uploadCsv() {
  if (!fileInput.files.length) {
    statusBlock.textContent = 'Selecciona primero un archivo CSV.';
    return;
  }
  uploadButton.disabled = true;
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  try {
    const response = await fetch(`/api/lottery/${encodeURIComponent(gameSelect.value)}/upload`, {
      method: 'POST',
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'No se pudo importar el CSV.');
    statusBlock.textContent = `${payload.message} ${payload.summary.draw_count} sorteos importados.`;
    await loadGameData();
  } catch (error) {
    statusBlock.textContent = error.message;
  } finally {
    uploadButton.disabled = false;
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
    const grid = document.createElement('div');
    grid.className = 'grid';
    renderMetric(grid, 'Juego', payload.game === 'euromillions' ? 'EuroMillions' : 'Bonoloto');
    renderMetric(grid, 'Fecha más reciente', payload.summary.latest_date);
    renderMetric(grid, 'Sorteos', payload.summary.draw_count);
    renderMetric(grid, 'Fuente', payload.summary.source === 'synthetic_sample' ? 'Ejemplo sintético' : 'CSV importado');
    summaryBlock.append(grid);

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
    const count = payload.game === 'euromillions' ? 5 : 6;
    renderNumberList(latestBlock, Array.from({ length: count }, (_, index) => draw[`main_${index + 1}`]));
    renderNumberList(latestBlock, payload.game === 'euromillions' ? [draw.star_1, draw.star_2] : [draw.complementary, draw.reintegro], 'badge');

    clear(backtestBlock);
    const backtest = payload.backtest;
    addText(backtestBlock, 'p', `Walk-forward: ${backtest.test_draws} sorteos de prueba.`, 'notice');
    const metrics = document.createElement('div');
    metrics.className = 'grid';
    renderMetric(metrics, 'Aciertos principales promedio', `${backtest.main_average_hits.toFixed(2)} / ${count}`);
    renderMetric(metrics, 'Esperado al azar', `${backtest.main_random_expected_hits.toFixed(2)} / sorteo`);
    renderMetric(metrics, 'Aciertos secundarios', `${backtest.secondary_average_hits.toFixed(2)} / sorteo`);
    renderMetric(metrics, 'Esperado al azar (secundario)', `${backtest.secondary_random_expected_hits.toFixed(2)} / sorteo`);
    if (backtest.reintegro_average_hits !== undefined) {
      renderMetric(metrics, 'Aciertos reintegro', `${backtest.reintegro_average_hits.toFixed(2)} / sorteo`);
      renderMetric(metrics, 'Esperado al azar (reintegro)', `${backtest.reintegro_random_expected_hits.toFixed(2)} / sorteo`);
    }
    backtestBlock.append(metrics);
    addText(backtestBlock, 'p', backtest.interpretation, 'notice');

    clear(modelInfoBlock);
    const active = payload.models?.[modelSelect.value] || modelSelect.value;
    addText(modelInfoBlock, 'p', `Modelo seleccionado: ${active}. Los modelos deep learning permanecen en estado planificado y no generan predicciones.`);
    statusBlock.textContent = payload.sample_data ? 'Datos sintéticos de demostración cargados.' : 'CSV importado cargado.';
  } catch (error) {
    statusBlock.textContent = error.message;
    [summaryBlock, predictionBlock, latestBlock, backtestBlock, modelInfoBlock].forEach(clear);
  } finally {
    loadButton.disabled = false;
  }
}

loadButton.addEventListener('click', loadGameData);
uploadButton.addEventListener('click', uploadCsv);
gameSelect.addEventListener('change', loadGameData);
modelSelect.addEventListener('change', loadGameData);
loadModels();
loadGameData();
