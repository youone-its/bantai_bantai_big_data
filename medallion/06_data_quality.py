"""
DATA QUALITY REPORT: Pemeriksaan Kualitas Data Lakehouse
========================================================
Menjalankan pemeriksaan kualitas data terhadap layer Bronze & Silver,
lalu menghasilkan:
  1. Tabel Delta  -> {GOLD_PATH}/gold_data_quality_report
  2. Laporan Markdown -> /app/DATA_QUALITY_REPORT.md (muncul di host: medallion/)

Dimensi kualitas yang diperiksa:
  - Completeness : jumlah & persentase null pada kolom kunci
  - Consistency  : konsistensi nama kecamatan & periode (case/spasi)
  - Validity     : kolom numerik berisi string kosong, tipe tidak konsisten
  - Uniqueness   : duplikat pada grain (kecamatan x periode x tahun)
  - Reconciliation: jumlah baris Bronze vs total CKAN
"""

import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, countDistinct, trim, lit
from delta import configure_spark_with_delta_pip

builder = (
    SparkSession.builder
    .appName("medallion-data-quality")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"
LAKEHOUSE = f"{HDFS_PATH}/lakehouse"
BRONZE = f"{LAKEHOUSE}/bronze"
SILVER = f"{LAKEHOUSE}/silver"
GOLD = f"{LAKEHOUSE}/gold"

print("=" * 70)
print(" DATA QUALITY REPORT")
print("=" * 70)

# Jumlah baris referensi dari sumber CKAN (untuk rekonsiliasi)
EXPECTED = {
    "sby_penduduk_usia": 153,
    "sby_sekolah_akreditasi": 3162,
    "sby_sekolah_negeri_swasta": 1612,
    "sby_siswa_negeri_swasta": 1643,
    "sby_sd_akreditasi_kecamatan": 1581,
    "sby_smp_akreditasi_kecamatan": 1581,
    "sby_sekolah_murid_guru_rasio": 1500,
}

# Kolom kunci untuk pengecekan completeness per tabel
KEY_COLS = {
    "sby_penduduk_usia": ["nama_kecamatan", "nama_kelurahan", "data_tahun"],
    "sby_sekolah_akreditasi": ["kode_sekolah", "kecamatan", "kapasitas_pagu_siswa"],
    "sby_sekolah_negeri_swasta": ["kecamatan", "periode", "tahun"],
    "sby_siswa_negeri_swasta": ["kecamatan", "periode", "tahun"],
    "sby_sd_akreditasi_kecamatan": ["kecamatan", "periode", "tahun"],
    "sby_smp_akreditasi_kecamatan": ["kecamatan", "periode", "tahun"],
    "sby_sekolah_murid_guru_rasio": ["kecamatan", "periode", "tahun"],
}

rows = []  # baris hasil untuk tabel Delta
md = []    # baris markdown

def add(table, layer, dimension, metric, value, status, note=""):
    rows.append((table, layer, dimension, metric, str(value), status, note))

# ---------------------------------------------------------------------------
# 1. RECONCILIATION & COMPLETENESS (Bronze)
# ---------------------------------------------------------------------------
print("\n[1] Reconciliation & Completeness (Bronze)...")
for table, expected in EXPECTED.items():
    try:
        df = spark.read.format("delta").load(f"{BRONZE}/{table}")
        n = df.count()
        status = "PASS" if n == expected else "WARN"
        add(table, "bronze", "reconciliation", "row_count_vs_ckan",
            f"{n}/{expected}", status)

        for kc in KEY_COLS.get(table, []):
            if kc in df.columns:
                nulls = df.filter(col(kc).isNull() | (trim(col(kc).cast("string")) == "")).count()
                pct = round(nulls / n * 100, 2) if n else 0
                st = "PASS" if nulls == 0 else ("WARN" if pct < 5 else "FAIL")
                add(table, "bronze", "completeness", f"null_{kc}", f"{nulls} ({pct}%)", st)
    except Exception as e:
        add(table, "bronze", "reconciliation", "row_count_vs_ckan", "ERROR", "FAIL", str(e)[:80])

# ---------------------------------------------------------------------------
# 2. CONSISTENCY (Silver) - kecamatan & periode
# ---------------------------------------------------------------------------
print("[2] Consistency (Silver)...")
KEC_DATASETS = ["sby_sekolah_negeri_swasta", "sby_siswa_negeri_swasta",
                "sby_sd_akreditasi_kecamatan", "sby_smp_akreditasi_kecamatan",
                "sby_sekolah_murid_guru_rasio"]
for table in KEC_DATASETS:
    try:
        df = spark.read.format("delta").load(f"{SILVER}/{table}")
        raw_kec = df.select(countDistinct("kecamatan")).collect()[0][0]
        norm_kec = df.select(countDistinct("kecamatan_norm")).collect()[0][0]
        key_kec = df.select(countDistinct("kecamatan_key")).collect()[0][0]
        # Surabaya memiliki 31 kecamatan -> key harus mendekati 31
        st = "PASS" if key_kec == 31 else "WARN"
        add(table, "silver", "consistency", "distinct_kecamatan(raw/norm/key)",
            f"{raw_kec}/{norm_kec}/{key_kec}", st,
            "key menyatukan variasi spasi & case" if key_kec < norm_kec else "")
        if "periode_norm" in df.columns:
            raw_p = df.select(countDistinct("periode")).collect()[0][0]
            norm_p = df.select(countDistinct("periode_norm")).collect()[0][0]
            st = "PASS" if norm_p <= 12 else "FAIL"
            add(table, "silver", "consistency", "distinct_periode(raw/norm)",
                f"{raw_p}/{norm_p}", st, "norm distandarkan ke <=12 bulan")
    except Exception as e:
        add(table, "silver", "consistency", "kecamatan", "ERROR", "FAIL", str(e)[:80])

# ---------------------------------------------------------------------------
# 3. UNIQUENESS (Silver) - duplikat pada grain
# ---------------------------------------------------------------------------
print("[3] Uniqueness (Silver)...")
for table in KEC_DATASETS:
    try:
        df = spark.read.format("delta").load(f"{SILVER}/{table}")
        n = df.count()
        distinct_grain = df.select("kecamatan_key", "periode_norm", "tahun").distinct().count()
        dup = n - distinct_grain
        st = "PASS" if dup == 0 else "WARN"
        add(table, "silver", "uniqueness", "dup_on_grain(kec_key,periode,tahun)",
            dup, st)
    except Exception as e:
        add(table, "silver", "uniqueness", "grain", "ERROR", "FAIL", str(e)[:80])

# ---------------------------------------------------------------------------
# 4. VALIDITY - tipe & kapasitas non-negatif (akreditasi & rasio)
# ---------------------------------------------------------------------------
print("[4] Validity (Silver)...")
try:
    df = spark.read.format("delta").load(f"{SILVER}/sby_sekolah_akreditasi")
    n = df.count()
    neg = df.filter(col("kapasitas_pagu_siswa") < 0).count()
    nullcap = df.filter(col("kapasitas_pagu_siswa").isNull()).count()
    add("sby_sekolah_akreditasi", "silver", "validity", "kapasitas_pagu_negatif", neg,
        "PASS" if neg == 0 else "FAIL")
    add("sby_sekolah_akreditasi", "silver", "validity", "kapasitas_pagu_null",
        f"{nullcap} ({round(nullcap/n*100,2)}%)", "PASS" if nullcap == 0 else "WARN")
except Exception as e:
    add("sby_sekolah_akreditasi", "silver", "validity", "kapasitas", "ERROR", "FAIL", str(e)[:80])

try:
    df = spark.read.format("delta").load(f"{SILVER}/sby_sekolah_murid_guru_rasio")
    dtypes = dict(df.dtypes)
    # mts_rasio diketahui bertipe text di sumber, sedangkan rasio lain numeric
    mts_type = dtypes.get("mts_rasio", "n/a")
    st = "WARN" if mts_type == "string" else "PASS"
    add("sby_sekolah_murid_guru_rasio", "silver", "validity", "mts_rasio_dtype",
        mts_type, st, "tipe beda dgn sd/smp/mi_rasio (numeric)")
except Exception as e:
    add("sby_sekolah_murid_guru_rasio", "silver", "validity", "mts_rasio", "ERROR", "FAIL", str(e)[:80])

# ---------------------------------------------------------------------------
# 5. JOINABILITY - kecocokan kecamatan penduduk vs sekolah (untuk Gold)
# ---------------------------------------------------------------------------
print("[5] Joinability (Silver)...")
try:
    pop = spark.read.format("delta").load(f"{SILVER}/sby_penduduk_usia") \
        .select("kecamatan_key").distinct()
    sek = spark.read.format("delta").load(f"{SILVER}/sby_sekolah_akreditasi") \
        .select("kecamatan_key").distinct()
    pop_n = pop.count()
    matched = pop.join(sek, "kecamatan_key", "inner").count()
    unmatched = pop_n - matched
    st = "PASS" if unmatched == 0 else "WARN"
    add("penduduk x akreditasi", "silver", "joinability",
        "kecamatan_match(matched/total)", f"{matched}/{pop_n}", st,
        "kecamatan penduduk yg tdk ketemu di sekolah" if unmatched else "")
except Exception as e:
    add("penduduk x akreditasi", "silver", "joinability", "match", "ERROR", "FAIL", str(e)[:80])

# ---------------------------------------------------------------------------
# TULIS HASIL: Delta table + Markdown
# ---------------------------------------------------------------------------
print("\n[6] Menulis hasil...")
schema = ["table", "layer", "dimension", "metric", "value", "status", "note"]
df_report = spark.createDataFrame(rows, schema).withColumn("_generated_at", lit(datetime.now().isoformat()))
df_report.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .save(f"{GOLD}/gold_data_quality_report")
print(f"  Tabel Delta: {GOLD}/gold_data_quality_report ({len(rows)} pemeriksaan)")

# Markdown
n_pass = sum(1 for r in rows if r[5] == "PASS")
n_warn = sum(1 for r in rows if r[5] == "WARN")
n_fail = sum(1 for r in rows if r[5] == "FAIL")

md.append(f"# Data Quality Report — Lakehouse Open Data Surabaya\n")
md.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
md.append(f"\n**Ringkasan:** {len(rows)} pemeriksaan — "
          f"✅ {n_pass} PASS · ⚠️ {n_warn} WARN · ❌ {n_fail} FAIL\n")
emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
last_dim = None
for r in rows:
    table, layer, dim, metric, value, status, note = r
    if dim != last_dim:
        md.append(f"\n## {dim.upper()} ({layer})\n")
        md.append("| Tabel | Metrik | Nilai | Status | Catatan |")
        md.append("|---|---|---|---|---|")
        last_dim = dim
    md.append(f"| {table} | {metric} | {value} | {emoji.get(status,'')} {status} | {note} |")

md_text = "\n".join(md) + "\n"
with open("/app/DATA_QUALITY_REPORT.md", "w", encoding="utf-8") as f:
    f.write(md_text)
print("  Markdown: /app/DATA_QUALITY_REPORT.md (host: medallion/DATA_QUALITY_REPORT.md)")

print("\n" + "=" * 70)
print(f" DQ SELESAI: {n_pass} PASS / {n_warn} WARN / {n_fail} FAIL")
print("=" * 70)
df_report.select("table", "dimension", "metric", "value", "status").show(60, truncate=False)

spark.stop()
