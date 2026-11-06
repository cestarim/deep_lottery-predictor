# deep_lottery-predictor

Dashboard experimental para explorar resultados históricos de EuroMillions y Bonoloto. Los CSV incluidos son **sintéticos de demostración**, no resultados oficiales. La frecuencia y el backtesting son análisis descriptivos: no predicen sorteos aleatorios ni aumentan la probabilidad de premio.

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

Abre <http://127.0.0.1:5000>. Pruebas: `python -m unittest discover -s tests`.

## Segunda fase: backtesting

La evaluación usa un esquema walk-forward: para cada sorteo reservado, el baseline solo recibe sorteos anteriores. Se compara el promedio de aciertos con el valor esperado de una selección aleatoria. En Bonoloto también se evalúan complementario y reintegro. Esto verifica el flujo de evaluación, no demuestra capacidad predictiva futura; los CSV actuales son sintéticos y muy pequeños.

## Estructura

- `app.py`: servidor Flask y endpoints JSON.
- `backend/data_loader.py`: carga y validación de CSV.
- `backend/predictor.py`: línea base reproducible por frecuencia.
- `backend/backtest.py`: validación walk-forward y referencia aleatoria.
- `frontend/`: panel HTML/CSS/JavaScript.
- `data/*_sample.csv`: datos ficticios para integración local.

Para usar datos reales, reemplaza los CSV conservando las cabeceras requeridas y verifica reglas/rangos con fuentes oficiales.
