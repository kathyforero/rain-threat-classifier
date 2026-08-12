"""
Descarga series horarias puntuales de ERA5-Land para las zonas seleccionadas.

CONFIGURACIÓN DEFINITIVA
------------------------
- Descarga: 1991-01-01 a 2026-01-01, inclusive.
- La fecha adicional de 2026 completa el 31 de diciembre de 2025
  después de convertir UTC a UTC-05:00.
- Salida: datos_horarios_crudos/completo/<zona>/
- Incluye las 12 zonas de desarrollo y las 3 de validación espacial.

Instalación:
    py -m pip install --upgrade "cdsapi>=0.7.7" truststore

Credenciales:
    C:/Users/TU_USUARIO/.cdsapirc
"""

from __future__ import annotations

import csv
import json
import shutil
import time
import zipfile
from pathlib import Path

import cdsapi
import truststore

truststore.inject_into_ssl()


DATASET = "reanalysis-era5-land-timeseries"

# El script ya queda configurado para la ejecución real.
TEST_MODE = False

TEST_START_DATE = "2024-01-01"
TEST_END_DATE = "2024-01-31"
TEST_ZONE_LIMIT = 1

# Se solicita un día adicional para completar el último día local de 2025.
FULL_START_DATE = "1991-01-01"
FULL_END_DATE = "2026-01-01"

FULL_RUN_NAME = "completo"
TEST_RUN_NAME = "prueba"

INCLUDE_SPATIAL_HOLDOUTS = True

VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "volumetric_soil_water_layer_1",
]

BASE_DIR = Path(__file__).resolve().parent
ZONES_FILE = BASE_DIR / "zonas_era5_ecuador.csv"
RAW_ROOT_DIR = BASE_DIR / "datos" / "crudos" / "era5_land"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 20
COMPLETE_MARKER_NAME = "_DESCARGA_COMPLETA.json"


def read_zones() -> list[dict[str, str]]:
    if not ZONES_FILE.exists():
        raise FileNotFoundError(f"No se encontró {ZONES_FILE}")

    with ZONES_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        zones = list(csv.DictReader(file))

    required_columns = {
        "zone_id", "ciudad", "latitud", "longitud", "rol"
    }
    if zones:
        missing = required_columns.difference(zones[0])
        if missing:
            raise ValueError(
                f"Faltan columnas en {ZONES_FILE.name}: {sorted(missing)}"
            )

    if not INCLUDE_SPATIAL_HOLDOUTS:
        zones = [zone for zone in zones if zone["rol"] == "desarrollo"]

    if TEST_MODE:
        zones = zones[:TEST_ZONE_LIMIT]

    if not zones:
        raise RuntimeError("No hay zonas seleccionadas.")

    return zones


def current_run_name() -> str:
    return TEST_RUN_NAME if TEST_MODE else FULL_RUN_NAME


def clean_incomplete_zone(zone_dir: Path) -> None:
    """
    Limpia una descarga parcial. Una zona solo se considera completa cuando
    existe el marcador JSON creado después de extraer todos los NetCDF.
    """
    marker = zone_dir / COMPLETE_MARKER_NAME
    if marker.exists():
        return

    if zone_dir.exists():
        shutil.rmtree(zone_dir)

    zone_dir.mkdir(parents=True, exist_ok=True)


def extract_download(download_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(download_path):
        with zipfile.ZipFile(download_path) as archive:
            archive.extractall(destination)
        files = sorted(destination.rglob("*.nc"))
    else:
        final_path = destination / "serie_horaria.nc"
        if final_path.exists():
            final_path.unlink()
        download_path.replace(final_path)
        files = [final_path]

    return files


def zone_is_complete(zone_dir: Path) -> bool:
    marker = zone_dir / COMPLETE_MARKER_NAME
    netcdf_files = list(zone_dir.rglob("*.nc"))
    return marker.exists() and bool(netcdf_files)


def write_complete_marker(
    zone_dir: Path,
    zone: dict[str, str],
    start_date: str,
    end_date: str,
    files: list[Path],
) -> None:
    payload = {
        "zone_id": zone["zone_id"],
        "ciudad": zone["ciudad"],
        "latitud_solicitada": float(zone["latitud"]),
        "longitud_solicitada": float(zone["longitud"]),
        "dataset": DATASET,
        "fecha_inicial_solicitada": start_date,
        "fecha_final_solicitada": end_date,
        "variables": VARIABLES,
        "archivos_netcdf": [
            str(path.relative_to(zone_dir)) for path in files
        ],
    }

    marker = zone_dir / COMPLETE_MARKER_NAME
    marker.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def download_zone(
    client: cdsapi.Client,
    zone: dict[str, str],
    start_date: str,
    end_date: str,
) -> None:
    zone_id = zone["zone_id"]
    zone_dir = RAW_ROOT_DIR / current_run_name() / zone_id

    if zone_is_complete(zone_dir):
        print(f"[OMITIDO] {zone_id}: descarga completa ya existente.")
        return

    clean_incomplete_zone(zone_dir)

    request = {
        "variable": VARIABLES,
        "location": {
            "latitude": float(zone["latitud"]),
            "longitude": float(zone["longitud"]),
        },
        "date": [f"{start_date}/{end_date}"],
        "data_format": "netcdf",
    }

    temporary_download = zone_dir / f"{zone_id}_descarga.tmp"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if temporary_download.exists():
                temporary_download.unlink()

            print(
                f"\n[{zone_id}] {start_date} a {end_date} "
                f"(intento {attempt}/{MAX_RETRIES})"
            )

            result = client.retrieve(DATASET, request)
            result.download(str(temporary_download))

            files = extract_download(temporary_download, zone_dir)
            if not files:
                raise RuntimeError(
                    f"La descarga de {zone_id} no produjo NetCDF."
                )

            write_complete_marker(
                zone_dir,
                zone,
                start_date,
                end_date,
                files,
            )

            print(
                f"[OK] {zone_id}: {len(files)} archivo(s) NetCDF."
            )
            return

        except Exception as exc:
            print(f"[ERROR] {zone_id}: {exc}")

            marker = zone_dir / COMPLETE_MARKER_NAME
            if marker.exists():
                marker.unlink()

            if attempt == MAX_RETRIES:
                raise

            time.sleep(RETRY_WAIT_SECONDS * attempt)


def main() -> None:
    RAW_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    zones = read_zones()

    if TEST_MODE:
        start_date = TEST_START_DATE
        end_date = TEST_END_DATE
        print("MODO PRUEBA ACTIVADO")
    else:
        start_date = FULL_START_DATE
        end_date = FULL_END_DATE
        print("MODO COMPLETO ACTIVADO")

    print(f"Carpeta de ejecución: {current_run_name()}")
    print(f"Zonas a descargar: {len(zones)}")
    print(f"Periodo UTC solicitado: {start_date} a {end_date}")
    print(f"Variables solicitadas: {len(VARIABLES)}")

    client = cdsapi.Client(timeout=3600)
    failures: list[str] = []

    for zone in zones:
        try:
            download_zone(client, zone, start_date, end_date)
        except Exception as exc:
            failures.append(f"{zone['zone_id']}: {exc}")

    if failures:
        print("\nDescargas con error:")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)

    print("\nTodas las descargas finalizaron correctamente.")
    print(
        "Ahora ejecuta 02_construir_dataset_mensual.py "
        "sin cambiar su configuración."
    )


if __name__ == "__main__":
    main()
