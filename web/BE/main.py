"""
BACKEND API: Read data from Gold Medallion Layer via REST API
=============================================================
Endpoints untuk membaca data dari HDFS Gold layer yang dihasilkan
dari proses medallion (Bronze -> Silver -> Gold).
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyarrow.parquet as pq
from hdfs import InsecureClient

app = FastAPI(
    title="Medallion Gold API",
    description="REST API untuk membaca data dari Gold Medallion Layer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
WEBHDFS_PORT = os.getenv("WEBHDFS_PORT", "9870")
GOLD_PATH = os.getenv("GOLD_PATH", "/lakehouse/gold")

hdfs_client = InsecureClient(url=f"http://{HDFS_HOST}:{WEBHDFS_PORT}", root=GOLD_PATH)

GOLD_TABLES = {
    "weather_analytics": "Weather analytics per kota (temperature trends)",
    "weather_extremes": "Cuaca ekstrem per kota (summary stats)",
    "news_by_source": "Distribusi berita per sumber",
    "recent_news": "20 berita terbaru",
    "weather_news_correlation": "Korelasi cuaca dan berita",
    "sby_sekolah_per_kecamatan": "Sekolah per kecamatan di Surabaya",
    "sby_siswa_per_kecamatan": "Siswa per kecamatan di Surabaya",
    "sby_sd_akreditasi_summary": "Ringkasan akreditasi SD per kecamatan",
    "sby_smp_akreditasi_summary": "Ringkasan akreditasi SMP per kecamatan",
    "sby_rasio_murid_guru": "Rasio murid-guru per kecamatan",
    "sby_penduduk_usia_summary": "Ringkasan penduduk usia 7-12 tahun",
    "sby_max_kapasitas_plus_20": "Max kapasitas sekolah + 20%",
}

class TableResponse(BaseModel):
    table_name: str
    description: str
    record_count: int
    columns: list[str]
    sample_data: list[dict]

class TablesListResponse(BaseModel):
    total_tables: int
    tables: dict[str, str]

def read_delta_table(table_name: str) -> list[dict]:
    try:
        table_path = f"{GOLD_PATH}/{table_name}"
        
        files = hdfs_client.list(table_path)
        parquet_files = [f for f in files if f.endswith(".parquet")]
        
        if not parquet_files:
            raise HTTPException(status_code=404, detail=f"No parquet files found in {table_path}")
        
        all_data = []
        for pf in parquet_files:
            with hdfs_client.read(f"{table_path}/{pf}", encoding=None) as reader:
                table = pq.read_table(reader)
                all_data.extend(table.to_pylist())
        
        return all_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading table: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Medallion Gold API",
        "version": "1.0.0",
        "docs": "/docs",
        "hdfs_host": HDFS_HOST,
        "gold_path": GOLD_PATH
    }

@app.get("/tables", response_model=TablesListResponse)
async def list_tables():
    return TablesListResponse(
        total_tables=len(GOLD_TABLES),
        tables=GOLD_TABLES
    )

@app.get("/tables/{table_name}", response_model=TableResponse)
async def get_table(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0)
):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    data = read_delta_table(table_name)
    total_count = len(data)
    
    paginated_data = data[offset:offset + limit]
    
    columns = list(data[0].keys()) if data else []
    
    return TableResponse(
        table_name=table_name,
        description=GOLD_TABLES[table_name],
        record_count=total_count,
        columns=columns,
        sample_data=paginated_data
    )

@app.get("/tables/{table_name}/count")
async def get_table_count(table_name: str):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    data = read_delta_table(table_name)
    return {"table_name": table_name, "count": len(data)}

@app.get("/tables/{table_name}/columns")
async def get_table_columns(table_name: str):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    data = read_delta_table(table_name)
    columns = list(data[0].keys()) if data else []
    return {"table_name": table_name, "columns": columns}

@app.get("/tables/{table_name}/max/{column}")
async def get_max_value(table_name: str, column: str):
    if table_name not in GOLD_TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    data = read_delta_table(table_name)
    
    if not data:
        raise HTTPException(status_code=404, detail="Table is empty")
    
    if column not in data[0]:
        raise HTTPException(status_code=400, detail=f"Column '{column}' not found")
    
    values = [row[column] for row in data if row[column] is not None]
    
    if not values:
        raise HTTPException(status_code=404, detail=f"No non-null values in column '{column}'")
    
    max_value = max(values)
    max_row = next(row for row in data if row[column] == max_value)
    
    return {
        "table_name": table_name,
        "column": column,
        "max_value": max_value,
        "record_with_max": max_row
    }

@app.get("/health")
async def health_check():
    try:
        hdfs_client.list(GOLD_PATH)
        hdfs_status = "connected"
    except Exception as e:
        hdfs_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "hdfs_status": hdfs_status,
        "hdfs_host": HDFS_HOST,
        "gold_path": GOLD_PATH
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
