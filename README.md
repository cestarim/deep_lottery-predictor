# deep_lottery-predictor

Dashboard experimental para explorar resultados históricos de EuroMillions y Bonoloto. Los CSV incluidos son **sintéticos de demostración**, no resultados oficiales. La frecuencia histórica, el backtesting y los modelos de referencia son análisis descriptivos: no permiten predecir sorteos aleatorios ni aumentar la probabilidad de premio.

## Ejecutar en local

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Abre <http://127.0.0.1:5000>. La salud del servicio está en `/api/health`; los datos y la evaluación temporal se devuelven en `/api/lottery/euromillions` y `/api/lottery/bonoloto`.

También está disponible el catálogo de modelos en `/api/models` y las rutas específicas en `/api/lottery/<game>/model/<model_name>`.

Pruebas: `python -m unittest discover -s tests`.

## Fase 3: modelos de referencia

La capa actual añade:

- catálogo de modelos (`frequency_baseline`, `lstm`, `gru`, `transformer`, `cnn`)
- validación de selección de modelo por juego
- rutas de preparación para entrenamiento con CSV reales
- estructura de base para futuros modelos temporales

Los modelos recurrentes y de atención quedan preparados como esquema de entrenamiento, pero no son predictivos aún; requieren datos reales, secuenciación temporal y entrenamiento adicional. La referencia por frecuencia sigue siendo una línea base descriptiva.

## Estructura

- `app.py`: servidor Flask y endpoints JSON.
- `backend/data_loader.py`: carga y validación de CSV.
- `backend/predictor.py`: línea base reproducible por frecuencia.
- `backend/backtest.py`: validación walk-forward y referencia aleatoria.
- `backend/models.py`: catálogo y clases base para modelos de referencia.
- `backend/model_selection.py`: comprobación de viabilidad del modelo por juego.
- `frontend/`: panel HTML/CSS/JavaScript.
- `data/*_sample.csv`: datos ficticios para pruebas de integración.

Para usar datos reales, reemplaza los CSV conservando las cabeceras requeridas y verifica reglas/rangos con fuentes oficiales.
