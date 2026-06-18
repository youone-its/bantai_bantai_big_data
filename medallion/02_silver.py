"""
SILVER LAYER — Cleaning & Standardization
=========================================
Membersihkan tabel Bronze dan menstandarkan kunci agar dapat di-join lintas
dataset, lalu menulis ke Delta.

Transformasi:
  - trim seluruh kolom string
  - kecamatan_norm : buang prefix "Kec."/"Kel.", rapikan spasi, UPPER (tampilan)
  - kecamatan_key  : tanpa spasi (kunci join andal, menyatukan variasi penulisan)
  - periode_norm   : nama bulan distandarkan ke Title Case
  - dedup pada grain yang benar untuk tiap dataset

Input  : hdfs:///lakehouse/bronze/<table>
Output : hdfs:///lakehouse/silver/<table>
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, upper, lower, initcap, regexp_replace, current_timestamp
from delta import configure_spark_with_delta_pip

builder = (
    SparkSession.builder
    .appName("medallion-silver")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

BRONZE_PATH = f"{HDFS_PATH}/lakehouse/bronze"
SILVER_PATH = f"{HDFS_PATH}/lakehouse/silver"

META_COLS = {"_ingested_at", "_source", "_hdfs_source", "source_resource_id", "ingested_at"}

# Konfigurasi pembersihan per tabel.
#   kecamatan_src : kolom sumber nama kecamatan
#   periode_src   : kolom periode bulan (None bila tidak ada)
#   dedup_cols    : grain unik (diverifikasi terhadap field CKAN)
TABLES = [
    {"table": "sby_penduduk_usia",            "kecamatan_src": "nama_kecamatan", "periode_src": None,
     "dedup_cols": ["kecamatan_key", "nama_kelurahan", "data_bulan", "data_tahun"]},
    {"table": "sby_sekolah_akreditasi",       "kecamatan_src": "kecamatan",      "periode_src": None,
     "dedup_cols": ["kode_sekolah", "tahun"]},
    {"table": "sby_sekolah_negeri_swasta",    "kecamatan_src": "kecamatan",      "periode_src": "periode",
     "dedup_cols": ["kecamatan_key", "periode_norm", "tahun"]},
    {"table": "sby_siswa_negeri_swasta",      "kecamatan_src": "kecamatan",      "periode_src": "periode",
     "dedup_cols": ["kecamatan_key", "periode_norm", "tahun"]},
    {"table": "sby_sd_akreditasi_kecamatan",  "kecamatan_src": "kecamatan",      "periode_src": "periode",
     "dedup_cols": ["kecamatan_key", "periode_norm", "tahun"]},
    {"table": "sby_smp_akreditasi_kecamatan", "kecamatan_src": "kecamatan",      "periode_src": "periode",
     "dedup_cols": ["kecamatan_key", "periode_norm", "tahun"]},
    {"table": "sby_sekolah_murid_guru_rasio", "kecamatan_src": "kecamatan",      "periode_src": "periode",
     "dedup_cols": ["kecamatan_key", "periode_norm", "tahun"]},
]


def clean(cfg):
    table = cfg["table"]
    print(f"  - {table}")
    try:
        df = spark.read.format("delta").load(f"{BRONZE_PATH}/{table}")
        n_in = df.count()
        if n_in == 0:
            print("    (kosong) lewati")
            return

        # 1. trim seluruh kolom string non-metadata
        for f in df.schema.fields:
            if f.dataType.simpleString() == "string" and f.name not in META_COLS:
                df = df.withColumn(f.name, trim(col(f.name)))

        # 2. kecamatan_norm (tampilan) + kecamatan_key (join)
        kec_clean = upper(trim(regexp_replace(
            regexp_replace(col(cfg["kecamatan_src"]), r"(?i)^\s*(kec\.|kel\.)\s*", ""),
            r"\s+", " ")))
        df = df.withColumn("kecamatan_norm", kec_clean)
        df = df.withColumn("kecamatan_key", regexp_replace(col("kecamatan_norm"), r"\s+", ""))

        # 3. periode_norm
        if cfg["periode_src"]:
            df = df.withColumn("periode_norm", initcap(lower(trim(col(cfg["periode_src"])))))

        # 4. dedup + metadata
        df = df.dropDuplicates(cfg["dedup_cols"]).withColumn("_processed_at", current_timestamp())

        n_out = df.count()
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(f"{SILVER_PATH}/{table}")
        print(f"    OK {n_in} -> {n_out} record")
    except Exception as e:
        print(f"    GAGAL: {e}")


def main():
    print("=" * 70)
    print(" SILVER LAYER — Cleaning & Standardisasi")
    print("=" * 70)
    for cfg in TABLES:
        clean(cfg)
    print("=" * 70)
    print(" Silver selesai.")
    print("=" * 70)
    spark.stop()


if __name__ == "__main__":
    main()
