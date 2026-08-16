# Front local

Este proyecto se ejecuta localmente con un front React y una API FastAPI en la
misma computadora.

## Qué instalar

1. Python 3.10 o superior  
   Link: https://www.python.org/downloads/

2. Node.js LTS, incluye `npm`  
   Link: https://nodejs.org/

3. Git, en caso de clonar el repositorio  
   Link: https://git-scm.com/downloads

## Archivos necesarios

Para consultar el modelo desde el front deben existir:

- `resultados/modelo_svm_rbf_operativo_2025.joblib`
- `datos/procesados/indicadores_mensuales_todas_zonas.csv`
- `resultados/analisis_caracteristicas/catalogo_caracteristicas_modelado.csv`
- `back/main.py`
- `front/app`

No hace falta descargar datos meteorológicos antes de abrir el front si esos
archivos ya están en el proyecto.

## Forma recomendada

Desde la carpeta `front`, ejecutar:

```bat
iniciar.cmd
```

Ese archivo concentra todo:

- instala/verifica dependencias del backend;
- levanta FastAPI en `http://127.0.0.1:8000`;
- instala dependencias del front si falta `node_modules`;
- abre `http://localhost:5173`;
- levanta Vite.

## Comandos manuales

Backend:

```bat
cd back
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Front:

```bat
cd front\app
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Cobertura temporal

Se tiene información procesada hasta diciembre de 2025 como mes observado. Por
esa razón, el máximo mes objetivo que puede predecirse con los datos actuales es
enero de 2026:

```text
mes de referencia: diciembre 2025
mes objetivo: enero 2026
```

Para predecir febrero de 2026 o meses posteriores se requieren nuevos datos
observados de 2026 como entrada.

## Dependencias Python

Están en `back/requirements.txt`:

- `fastapi`
- `uvicorn[standard]`
- `joblib`
- `pandas`
- `numpy`
- `scikit-learn`

## Prueba rápida de API

Con la API encendida:

```bat
curl -X POST http://127.0.0.1:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"cityId\":\"guayaquil\",\"referenceMonth\":\"2025-12\"}"
```
