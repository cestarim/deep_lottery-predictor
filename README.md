# deep_lottery-predictor

Dashboard experimental para explorar resultados históricos de EuroMillions y Bonoloto. Los CSV incluidos son **sintéticos de demostración**, no resultados oficiales. El análisis estadístico no predice sorteos aleatorios ni aumenta la probabilidad de premio.

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

## Bloque listo: importar CSV

El panel permite cargar CSV de hasta 5 MB. La importación valida columnas, fechas, enteros, rangos y repeticiones antes de guardar. Al superar la validación, el archivo queda activo como `data/uploads/euromillions.csv` o `data/uploads/bonoloto.csv` y se usa en el análisis posterior. Los archivos importados no se deben subir al repositorio; la carpeta está ignorada por Git.

Cabeceras esperadas:

- EuroMillions: `date,main_1,main_2,main_3,main_4,main_5,star_1,star_2`
- Bonoloto: `date,main_1,main_2,main_3,main_4,main_5,main_6,complementary,reintegro`

Fechas en formato `YYYY-MM-DD`. Confirma la convención del CSV oficial, especialmente campos secundarios, antes de importarlo.

## Estado de modelos

`frequency_baseline` está disponible para análisis descriptivo. LSTM, GRU, Transformer y CNN figuran en el catálogo, pero no se entrenan ni hacen inferencias todavía. Se requiere una fase de investigación, datos suficientes y evaluación temporal reproducible antes de habilitarlos.
