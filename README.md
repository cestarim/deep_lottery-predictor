# Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload      # API en http://127.0.0.1:8000/docs
pytest -q
```

## Formato de CSV
- EuroMillions: `fecha, n_1..n_5, star_1, star_2`
- Bonoloto: `fecha, n_1..n_6, complementario, reintegro`

Se aceptan separadores `,` `;` y tab, y alias como `N1`, `Estrella 1`, `Fecha`.
Fechas en `YYYY-MM-DD`.

## Endpoints
- `GET /games`: juegos, columnas y rangos.
- `POST /games/{key}/upload`: sube y valida el CSV (informe de errores y filas descartadas).
- `GET /games/{key}/stats`: frecuencias por valor.
- `GET /games/{key}/dataset?window=10`: forma de los tensores y partición temporal.
- `POST /games/{key}/backtest`: backtest walk-forward frente a azar (z-score).
- `POST /games/{key}/train?kind=lstm|gru|cnn|transformer&window=10&epochs=30&dropout=0.2&patience=5`: entrena y evalúa en test frente al azar (z hipergeométrico exacto).
- `GET /games/{key}/predict`: puntuaciones del siguiente sorteo con el último modelo (no es una predicción fiable).
- `POST /games/{key}/walkforward?kind=lstm&folds=3&gap=5&test_frac=0.3`: walk-forward con gap; agrega todos los folds y contrasta frente al azar (test binomial exacto, IC de Wilson, h de Cohen).
