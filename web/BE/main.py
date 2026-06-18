"""
BACKEND API: Read data from Gold Medallion Layer via REST API
=============================================================
Membaca tabel Delta dari HDFS Gold layer (hasil pipeline Bronze -> Silver -> Gold).

Catatan teknis: tabel Gold adalah Delta Lake (folder berisi parquet + _delta_log).
Membaca SEMUA parquet di folder akan salah hitung setelah overwrite/time-travel,
karena file lama belum di-VACUUM. Maka kita membaca _delta_log untuk menentukan
file parquet yang AKTIF (add - remove) pada versi terbaru.
"""

import os
import io
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyarrow.parquet as pq
from hdfs import InsecureClient

app = FastAPI(
    title="Medallion Gold API - Open Data Surabaya",
    description="REST API untuk audit kapasitas pendidikan & rekomendasi USB/RKB dari Gold Layer",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
WEBHDFS_PORT = os.getenv("WEBHDFS_PORT", "9870")
GOLD_PATH = os.getenv("GOLD_PATH", "/lakehouse/gold")

hdfs_client = InsecureClient(url=f"http://{HDFS_HOST}:{WEBHDFS_PORT}", root=GOLD_PATH)

# Tabel Gold yang tersedia (deskriptif + analitik)
GOLD_TABLES = {
    # --- Analitik utama (tujuan proyek) ---
    "gold_demand_proyeksi": "Proyeksi kebutuhan bangku SD/SMP per kecamatan 2025-2030 (cohort survival)",
    "gold_kapasitas_kecamatan": "Audit kapasitas (pagu, ruang kelas, rombel) per kecamatan",
    "gold_gap_analysis": "Gap demand vs kapasitas + siswa berpotensi tidak tertampung",
    "gold_rekomendasi_usb_rkb": "Rekomendasi prioritas USB/RKB per kecamatan",
    "gold_data_quality_report": "Hasil pemeriksaan kualitas data lakehouse",
    # --- Deskriptif ---
    "sby_sekolah_per_kecamatan": "Jumlah sekolah negeri/swasta per kecamatan",
    "sby_siswa_per_kecamatan": "Jumlah siswa negeri/swasta per kecamatan",
    "sby_sd_akreditasi_summary": "Akreditasi SD per kecamatan",
    "sby_smp_akreditasi_summary": "Akreditasi SMP per kecamatan",
    "sby_rasio_murid_guru": "Rasio murid-guru per kecamatan",
    "sby_penduduk_usia_summary": "Penduduk per usia (level kelurahan)",
}


class TableResponse(BaseModel):
    table_name: str
    description: str
    record_count: int
    columns: list[str]
    data: list[dict]


class TablesListResponse(BaseModel):
    total_tables: int
    tables: dict[str, str]


def _active_parquet_files(table_name: str) -> list[str]:
    """Tentukan file parquet AKTIF dari _delta_log (add - remove)."""
    log_dir = f"{table_name}/_delta_log"
    try:
        log_files = sorted(f for f in hdfs_client.list(log_dir) if f.endswith(".json"))
    except Exception:
        raise HTTPException(status_code=404, detail=f"Bukan tabel Delta atau tidak ada: {table_name}")

    added: list[str] = []
    removed: set[str] = set()
    for lf in log_files:
        with hdfs_client.read(f"{log_dir}/{lf}", encoding="utf-8") as reader:
            for line in reader.read().splitlines():
                if not line.strip():
                    continue
                action = json.loads(line)
                if "add" in action:
                    added.append(action["add"]["path"])
                if "remove" in action:
                    removed.add(action["remove"]["path"])
    seen = set()
    active = []
    for p in added:
        if p not in removed and p not in seen:
            seen.add(p)
            active.append(p)
    return active


def read_delta_table(table_name: str) -> list[dict]:
    """Baca isi tabel Delta (versi terbaru) sebagai list[dict]."""
    active = _active_parquet_files(table_name)
    if not active:
        return []
    all_data: list[dict] = []
    for pf in active:
        with hdfs_client.read(f"{table_name}/{pf}", encoding=None) as reader:
            buf = io.BytesIO(reader.read())  # pyarrow butuh objek seekable
        table = pq.read_table(buf)
        all_data.extend(table.to_pylist())
    for row in all_data:
        for tech in ("_gold_created_at", "_processed_at", "_updated_at", "_generated_at", "_refreshed_at"):
            row.pop(tech, None)
    return all_data


@app.get("/")
async def root():
    return {
        "message": "Medallion Gold API - Open Data Surabaya",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": ["/tables", "/tables/{name}", "/analysis/rekomendasi",
                      "/analysis/gap/{kecamatan}", "/analysis/proyeksi/{kecamatan}", "/health"],
    }


@app.get("/tables", response_model=TablesListResponse)
async def list_tables():
    return TablesListResponse(total_tables=len(GOLD_TABLES), tables=GOLD_TABLES)


@app.get("/tables/{table_name}", response_model=TableResponse)
async def get_table(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    data = read_delta_table(table_name)
    columns = list(data[0].keys()) if data else []
    return TableResponse(
        table_name=table_name,
        description=GOLD_TABLES[table_name],
        record_count=len(data),
        columns=columns,
        data=data[offset:offset + limit],
    )


@app.get("/tables/{table_name}/count")
async def get_table_count(table_name: str):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return {"table_name": table_name, "count": len(read_delta_table(table_name))}


# ---------------------------------------------------------------------------
# ENDPOINT ANALISIS (dipakai frontend untuk dashboard USB/RKB)
# ---------------------------------------------------------------------------
@app.get("/analysis/rekomendasi")
async def rekomendasi(
    top: int = Query(default=10, ge=1, le=31),
    filter_rekom: Optional[str] = Query(default=None, description="USB | RKB | CUKUP"),
):
    """Daftar rekomendasi USB/RKB diurutkan berdasarkan prioritas (defisit terbesar)."""
    data = read_delta_table("gold_rekomendasi_usb_rkb")
    if filter_rekom:
        data = [r for r in data if r.get("rekomendasi") == filter_rekom.upper()]
    data.sort(key=lambda r: r.get("peringkat_prioritas", 9999))
    return {"count": len(data), "data": data[:top]}


@app.get("/analysis/gap/{kecamatan}")
async def gap_kecamatan(kecamatan: str):
    """Tren gap demand vs kapasitas per tahun untuk satu kecamatan."""
    key = kecamatan.upper().replace(" ", "")
    data = [r for r in read_delta_table("gold_gap_analysis") if r.get("kecamatan_key") == key]
    if not data:
        raise HTTPException(status_code=404, detail=f"Kecamatan '{kecamatan}' tidak ditemukan")
    data.sort(key=lambda r: r.get("tahun_proyeksi", 0))
    return {"kecamatan": kecamatan, "count": len(data), "data": data}


@app.get("/analysis/proyeksi/{kecamatan}")
async def proyeksi_kecamatan(kecamatan: str):
    """Proyeksi demand SD/SMP per tahun untuk satu kecamatan."""
    key = kecamatan.upper().replace(" ", "")
    data = [r for r in read_delta_table("gold_demand_proyeksi") if r.get("kecamatan_key") == key]
    if not data:
        raise HTTPException(status_code=404, detail=f"Kecamatan '{kecamatan}' tidak ditemukan")
    data.sort(key=lambda r: r.get("tahun_proyeksi", 0))
    return {"kecamatan": kecamatan, "count": len(data), "data": data}


@app.get("/health")
async def health_check():
    try:
        hdfs_client.list("")
        hdfs_status = "connected"
    except Exception as e:
        hdfs_status = f"disconnected: {str(e)}"
    return {"status": "healthy", "hdfs_status": hdfs_status, "gold_path": GOLD_PATH}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
