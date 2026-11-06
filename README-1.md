# deep_lottery-predictor

Proyecto de analítica experimental para EuroMillions y Bonoloto. El diseño combina un backend Python para datos, modelos y evaluación con un dashboard HTML/JavaScript para interacción y visualización.

> Los sorteos son aleatorios: el proyecto es experimental y no garantiza predicciones ni premios. No lo uses como base para apostar.

## Estado

- Hay una hoja de estilos inicial en `frontend/static/css/styles.css`.
- Pendiente de implementar: backend, carga/validación de datos, modelos y dashboard conectado.

## Alcance

- EuroMillions: fecha `YYYY-MM-DD`, cinco números principales y dos estrellas.
- Bonoloto: fecha, seis números principales, complementario y reintegro. Confirmar nombres y rangos con el CSV o la fuente de datos antes de implementar.
- API/backend Python para carga, validación, análisis, entrenamiento y evaluación temporal.
- Interfaz HTML/CSS/JavaScript para cargar datos, configurar modelos y visualizar resultados.
- Modelos a comparar: LSTM, GRU, Transformer y CNN, con dropout y early stopping configurables.
- Evaluación mediante backtesting temporal y comparación con una referencia aleatoria.

## Hoja de ruta

1. Preparar los CSV de EuroMillions y Bonoloto (no se incluyen en el repositorio).
2. Confirmar nombres de columnas y rangos.
3. Implementar la API.
4. Montar el dashboard.
5. Añadir los modelos y el backtesting.
6. Probar con datos reales y ajustar.

## Referencia

El notebook de Mega Millions `Megamillions_Balles_7_window_11_4_2023_LSTM.ipynb` (repositorio de Polanitz) se usa solo como inspiración metodológica (ventana temporal y LSTM).

## Licencia

MIT. Consulta el archivo `LICENSE`.
