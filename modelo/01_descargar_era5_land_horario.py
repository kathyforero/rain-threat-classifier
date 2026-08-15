"""
Descarga series horarias puntuales de ERA5-Land para las zonas seleccionadas.

CONFIGURACIÓN OFICIAL DEL PROYECTO
----------------------------------
- Dataset: reanalysis-era5-land-timeseries.
- Descarga: 1991-01-01 a 2026-01-01, inclusive.
- La fecha adicional de 2026 completa el 31 de diciembre de 2025
  después de convertir UTC a UTC-05:00 durante el procesamiento.
- Salida: datos/crudos/era5_land/<zona>/
- Incluye las 12 zonas de desarrollo y las 3 de validación espacial.
- Conserva las siete variables solicitadas originalmente al CDS, incluida
  volumetric_soil_water_layer_1. El hecho de que una variable se descargue
  no obliga a utilizarla posteriormente como característica del modelo.

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

# Se solicita un día adicional para completar el último día local de 2025.
START_DATE = "1991-01-01"
END_DATE = "2026-01-01"

INCLUDE_SPATIAL_HOLDOUTS = True

# Se mantienen exactamente las variables solicitadas en la descarga original.
VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "volumetric_soil_water_layer_1",
]

BASE_DIR = Path(__file__).resolve().parent.parent
ZONES_FILE = BASE_DIR / "zonas_era5_ecuador.csv"
RAW_DIR = BASE_DIR / "datos" / "crudos" / "era5_land"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 20
COMPLETE_MARKER_NAME = "_DESCARGA_COMPLETA.json"


def read_zones() -> list[dict[str, str]]:
    if not ZONES_FILE.exists():
        raise FileNotFoundError(f"No se encontró {ZONES_FILE}")

    with ZONES_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        zones = list(csv.DictReader(file))

    required_columns = {
        "zone_id",
        "ciudad",
        "latitud",
        "longitud",
        "rol",
    }

    if zones:
        missing = required_columns.difference(zones[0])
        if missing:
            raise ValueError(
                f"Faltan columnas en {ZONES_FILE.name}: {sorted(missing)}"
            )

    if not INCLUDE_SPATIAL_HOLDOUTS:
        zones = [
            zone
            for zone in zones
            if zone["rol"] == "desarrollo"
        ]

    if not zones:
        raise RuntimeError("No hay zonas seleccionadas.")

    return zones


def clean_incomplete_zone(zone_dir: Path) -> None:
    """
    Limpia una descarga parcial.

    Una zona solo se considera completa cuando existe el marcador JSON
    creado después de extraer todos los NetCDF.
    """
    marker = zone_dir / COMPLETE_MARKER_NAME

    if marker.exists():
        return

    if zone_dir.exists():
        shutil.rmtree(zone_dir)

    zone_dir.mkdir(parents=True, exist_ok=True)


def extract_download(
    download_path: Path,
    destination: Path,
) -> list[Path]:
    """
    Extrae el resultado del CDS.

    El servicio puede devolver un ZIP con varios NetCDF o un NetCDF
    directamente. El archivo temporal se elimina una vez extraído.
    """
    destination.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(download_path):
        with zipfile.ZipFile(download_path) as archive:
            archive.extractall(destination)

        files = sorted(destination.rglob("*.nc"))
        download_path.unlink(missing_ok=True)
    else:
        final_path = destination / "serie_horaria.nc"

        if final_path.exists():
            final_path.unlink()

        download_path.replace(final_path)
        files = [final_path]

    return files


def zone_is_complete(zone_dir: Path) -> bool:
    marker = zone_dir / COMPLETE_MARKER_NAME

    if not marker.exists():
        return False

    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    listed_files = payload.get("archivos_netcdf", [])
    if not listed_files:
        return False

    return all(
        (zone_dir / relative_path).exists()
        for relative_path in listed_files
    )


def write_complete_marker(
    zone_dir: Path,
    zone: dict[str, str],
    files: list[Path],
) -> None:
    payload = {
        "zone_id": zone["zone_id"],
        "ciudad": zone["ciudad"],
        "latitud_solicitada": float(zone["latitud"]),
        "longitud_solicitada": float(zone["longitud"]),
        "dataset": DATASET,
        "fecha_inicial_solicitada": START_DATE,
        "fecha_final_solicitada": END_DATE,
        "variables": VARIABLES,
        "archivos_netcdf": [
            str(path.relative_to(zone_dir))
            for path in files
        ],
    }

    marker = zone_dir / COMPLETE_MARKER_NAME
    marker.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def download_zone(
    client: cdsapi.Client,
    zone: dict[str, str],
) -> None:
    zone_id = zone["zone_id"]
    zone_dir = RAW_DIR / zone_id

    if zone_is_complete(zone_dir):
        print(
            f"[OMITIDO] {zone_id}: "
            "descarga completa ya existente."
        )
        return

    clean_incomplete_zone(zone_dir)

    request = {
        "variable": VARIABLES,
        "location": {
            "latitude": float(zone["latitud"]),
            "longitude": float(zone["longitud"]),
        },
        "date": [f"{START_DATE}/{END_DATE}"],
        "data_format": "netcdf",
    }

    temporary_download = (
        zone_dir / f"{zone_id}_descarga.tmp"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if temporary_download.exists():
                temporary_download.unlink()

            print(
                f"\n[{zone_id}] {START_DATE} a {END_DATE} "
                f"(intento {attempt}/{MAX_RETRIES})"
            )

            result = client.retrieve(DATASET, request)
            result.download(str(temporary_download))

            files = extract_download(
                temporary_download,
                zone_dir,
            )

            if not files:
                raise RuntimeError(
                    f"La descarga de {zone_id} "
                    "no produjo NetCDF."
                )

            write_complete_marker(
                zone_dir,
                zone,
                files,
            )

            print(
                f"[OK] {zone_id}: "
                f"{len(files)} archivo(s) NetCDF."
            )
            return

        except Exception as exc:
            print(f"[ERROR] {zone_id}: {exc}")

            marker = (
                zone_dir / COMPLETE_MARKER_NAME
            )
            marker.unlink(missing_ok=True)
            temporary_download.unlink(
                missing_ok=True
            )

            if attempt == MAX_RETRIES:
                raise

            time.sleep(
                RETRY_WAIT_SECONDS * attempt
            )


def main() -> None:
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    zones = read_zones()

    print("DESCARGA OFICIAL ERA5-LAND")
    print(f"Directorio de salida: {RAW_DIR}")
    print(f"Zonas a descargar: {len(zones)}")
    print(
        f"Periodo UTC solicitado: "
        f"{START_DATE} a {END_DATE}"
    )
    print(
        f"Variables solicitadas: "
        f"{len(VARIABLES)}"
    )

    client = cdsapi.Client(timeout=3600)
    failures: list[str] = []

    for zone in zones:
        try:
            download_zone(
                client,
                zone,
            )
        except Exception as exc:
            failures.append(
                f"{zone['zone_id']}: {exc}"
            )

    if failures:
        print("\nDescargas con error:")

        for failure in failures:
            print(" -", failure)

        raise SystemExit(1)

    print(
        "\nTodas las descargas "
        "finalizaron correctamente."
    )
    print(
        "Ahora ejecuta "
        "02_construir_indicadores.py."
    )


if __name__ == "__main__":
    main()
