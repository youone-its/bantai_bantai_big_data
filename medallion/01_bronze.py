"""
BRONZE LAYER — Raw Ingestion
============================
Membaca file JSON mentah Open Data Surabaya dari HDFS (hasil Kafka consumer)
lalu menulisnya sebagai tabel Delta apa adanya, hanya ditambah metadata teknis.
Tidak ada transformasi di layer ini (menjaga keaslian data sumber).

Input  : hdfs:///data/opendata-sby/<dataset>/*.json
Output : hdfs:///lakehouse/bronze/<bronze_table>  (Delta)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp
from delta import configure_spark_with_delta_pip

builder = (
    SparkSession.builder
    .appName("medallion-bronze")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

INPUT_BASE = f"{HDFS_PATH}/data/opendata-sby"
BRONZE_PATH = f"{HDFS_PATH}/lakehouse/bronze"

DATASETS = [
    {"name": "penduduk_usia",            "subpath": "penduduk-usia",            "table": "sby_penduduk_usia"},
    {"name": "sekolah_akreditasi",       "subpath": "sekolah-akreditasi",       "table": "sby_sekolah_akreditasi"},
    {"name": "sekolah_negeri_swasta",    "subpath": "sekolah-negeri-swasta",    "table": "sby_sekolah_negeri_swasta"},
    {"name": "siswa_negeri_swasta",      "subpath": "siswa-negeri-swasta",      "table": "sby_siswa_negeri_swasta"},
    {"name": "sd_akreditasi_kecamatan",  "subpath": "sd-akreditasi-kecamatan",  "table": "sby_sd_akreditasi_kecamatan"},
    {"name": "smp_akreditasi_kecamatan", "subpath": "smp-akreditasi-kecamatan", "table": "sby_smp_akreditasi_kecamatan"},
    {"name": "sekolah_murid_guru_rasio", "subpath": "sekolah-murid-guru-rasio", "table": "sby_sekolah_murid_guru_rasio"},
]


def ingest(dataset):
    name = dataset["name"]
    source = f"{INPUT_BASE}/{dataset['subpath']}"
    target = f"{BRONZE_PATH}/{dataset['table']}"
    print(f"  - {name:<26} <- {source}")

    try:
        df = spark.read.option("multiline", "true").json(source)
        n = df.count()
        if n == 0:
            print(f"    (kosong) lewati — jalankan producer & consumer dahulu")
            return
        df = (df
              .withColumn("_ingested_at", current_timestamp())
              .withColumn("_source", lit(name))
              .withColumn("_hdfs_source", lit(source)))
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(target)
        print(f"    OK {n} record -> {dataset['table']}")
    except Exception as e:
        print(f"    GAGAL: {e}")


def main():
    print("=" * 70)
    print(" BRONZE LAYER — Ingest Open Data Surabaya ke Delta")
    print("=" * 70)
    for ds in DATASETS:
        ingest(ds)
    print("=" * 70)
    print(" Bronze selesai.")
    print("=" * 70)
    spark.stop()


if __name__ == "__main__":
    main()
