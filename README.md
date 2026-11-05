# deep_lottery-predictor

Dashboard experimental para explorar resultados históricos de EuroMillions y Bonoloto. Actualmente se incluyen CSV **sintéticos de demostración**, no resultados oficiales. La frecuencia histórica es un resumen descriptivo y no permite predecir sorteos aleatorios ni aumentar la probabilidad de premio.

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

Abre <http://127.0.0.1:5000>. La comprobación de salud está en `/api/health`; los datos están en `/api/lottery/euromillions` y `/api/lottery/bonoloto`.

## Estructura actual

- `app.py`: servidor Flask y endpoints JSON.
- `backend/data_loader.py`: carga y validación de esquemas y rangos básicos.
- `backend/predictor.py`: línea base reproducible por frecuencia.
- `frontend/`: panel HTML/CSS/JavaScript.
- `data/*_sample.csv`: datos ficticios para verificar la integración.

Para usar datos reales, sustituye los CSV conservando las cabeceras requeridas; el backend valida estructura, fechas, enteros y rangos. Confirma la convención del campo complementario en el CSV oficial antes de usarlo para Bonoloto.
