# Ejecucion

Usa `iniciar.cmd` para levantar la interfaz local.

El archivo hace lo siguiente:

- instala/verifica dependencias del backend;
- inicia la API local de FastAPI en `http://127.0.0.1:8000`;
- verifica que `node` y `npm` estén disponibles;
- entra a la carpeta `app`;
- instala dependencias si no existe `node_modules`;
- abre el navegador en `http://localhost:5173`;
- ejecuta el servidor de desarrollo.

```bat
iniciar.cmd
```

## Conexión con el modelo

La interfaz consulta la API local en `http://127.0.0.1:8000/predict`.
Esa API carga `resultados/modelo_svm_rbf_operativo_2025.joblib` y ejecuta el
modelo desde Python.

```bat
iniciar.cmd
```

Requiere que Python tenga disponibles `joblib`, `pandas`, `numpy` y
`scikit-learn`. El archivo `iniciar.cmd` instala también FastAPI y uvicorn si
hacen falta.
