# deep_lottery-predictor

Dashboard experimental para explorar resultados históricos de EuroMillions y Bonoloto. Los CSV incluidos son **sintéticos de demostración**, no resultados oficiales. La frecuencia histórica y el backtesting son análisis descriptivos: no permiten predecir sorteos aleatorios ni aumentar la probabilidad de premio.

## Ejecutar en local

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Abre <http://127.0.0.1:5000>. La salud del servicio está en `/api/health`; los datos y la evaluación temporal se devuelven en `/api/lottery/euromillions` y `/api/lottery/bonoloto`.

Pruebas: `python -m unittest discover -s tests`.

## Segunda fase: backtesting

La evaluación implementa un esquema walk-forward: para cada sorteo reservado, el baseline solo ve sorteos anteriores. El resultado se compara con el valor esperado de una selección aleatoria (incluyendo la regla de que el complementario de Bonoloto no puede coincidir con los seis números principales). Esto sirve como comprobación metodológica del código, no como prueba de predicción; los datos actuales son sintéticos y muy pequeños.

## Estructura

- `app.py`: servidor Flask y endpoints JSON.
- `backend/data_loader.py`: carga y validación de CSV.
- `backend/predictor.py`: línea base reproducible por frecuencia.
- `backend/backtest.py`: validación walk-forward y referencia aleatoria.
- `frontend/`: panel HTML/CSS/JavaScript.
- `data/*_sample.csv`: datos ficticios para pruebas de integración.

Para usar datos reales, reemplaza los CSV conservando las cabeceras requeridas; el backend valida estructura, fechas, enteros y rangos básicos. Verifica los rangos y reglas con fuentes oficiales antes de analizar datos reales.
