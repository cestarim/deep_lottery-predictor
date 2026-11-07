# deep_lottery-predictor

Proyecto de analítica experimental para EuroMillions y Bonoloto. El diseño previsto combina backend Python para datos, modelos y evaluación, con dashboard HTML/JavaScript para interacción y visualización.

> Los sorteos son aleatorios: el proyecto es experimental y no garantiza predicciones ni premios.

## Estado en construcción.

- Repositorio creado seguiendo una 
- hoja de estilos inicial en `frontend/static/css/styles.css`.
- El backend, la carga/validación de datos, los modelos y el dashboard conectado todavía están pendientes de implementar.
- El notebook de Mega Millions del enlace de referencia se usa solo como inspiración metodológica (ventana temporal y LSTM); no se modifica el repositorio de terceros.

## Alcance acordado

- EuroMillions: fecha `YYYY-MM-DD`, cinco números principales y dos estrellas.
- Bonoloto: fecha, seis números principales, complementario y reintegro. Confirmar nombres/rangos con el CSV o la fuente de datos antes de implementar.
- API/backend Python para carga, validación, análisis, entrenamiento y evaluación temporal.
- Interfaz HTML/CSS/JavaScript para cargar datos, configurar modelos y visualizar resultados.
- Modelos a comparar: LSTM, GRU, Transformer y CNN; opciones configurables de dropout y early stopping.
- Evaluación mediante backtesting temporal y comparación con una referencia aleatoria.

## Próximos pasos para retomar

1. Preparar los CSV reales de EuroMillions y Bonoloto.
2. Confirmar los nombres de columnas y rangos.
3. Implementar la API.
4. Montar el dashboard.
5. Añadir los modelos y el backtesting.
6. Probar con datos reales y ajustar.

Al retomar, ayudar a corregir errores y completar los archivos necesarios manteniendo la continuidad del proyecto. El siguiente bloque de trabajo puede incluir la estructura exacta de la API, endpoints de carga y predicción, preprocesado para secuencias y HTML conectado al backend, con el objetivo de dejarlo operativo.

## Referencia

Notebook Mega Millions: `Megamillions_Balles_7_window_11_4_2023_LSTM.ipynb` en el repositorio de Polanitz enlazado durante la conversación.
