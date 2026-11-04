# deep_lottery-predictor

Proyecto privado de analítica experimental para EuroMillions y Bonoloto. El diseño previsto combina backend Python para datos, modelos y evaluación, con dashboard HTML/JavaScript para interacción y visualización.

> Los sorteos son aleatorios: el proyecto es experimental y no garantiza predicciones ni premios.

## Estado guardado

- Repositorio creado como privado.
- Hay una hoja de estilos inicial en `frontend/static/css/styles.css`.
- El backend, la carga/validación de datos, los modelos y el dashboard conectado todavía están pendientes de implementar.
- El notebook de Mega Millions del enlace de referencia se usa solo como inspiración metodológica (ventana temporal y LSTM); no se modifica el repositorio de terceros.

## Alcance acordado

- EuroMillions: fecha `YYYY-MM-DD`, cinco números principales y dos estrellas.
- Bonoloto: fecha, seis números principales, complementario y reintegro. Confirmar nombres/rangos con el CSV o la fuente de datos antes de implementar.
- API/backend Python para carga, validación, análisis, entrenamiento y evaluación temporal.
- Interfaz HTML/CSS/JavaScript para cargar datos, configurar modelos y visualizar resultados.
- Modelos a comparar: LSTM, GRU, Transformer y CNN; opciones configurables de dropout y early stopping.
- Evaluación mediante backtesting temporal y comparación con una referencia aleatoria.

## Próximos pasos

1. Confirmar formato y fuente de los CSV de EuroMillions y Bonoloto.
2. Implementar backend FastAPI, validación de datos y endpoints.
3. Implementar preprocesamiento y baseline estadístico antes de entrenar redes profundas.
4. Añadir modelos y backtesting sin mezclar datos futuros en el entrenamiento.
5. Conectar el dashboard y documentar cómo ejecutar y probar el proyecto.

## Referencia

Notebook Mega Millions: `Megamillions_Balles_7_window_11_4_2023_LSTM.ipynb` en el repositorio de Polanitz enlazado durante la conversación.
