"""
GOLD LAYER — Business Analytics (Audit Kapasitas & Rekomendasi USB/RKB)
======================================================================
Menghasilkan data mart dari Silver:

Deskriptif (snapshot terbaru per kecamatan):
  - sby_sekolah_per_kecamatan, sby_siswa_per_kecamatan
  - sby_sd_akreditasi_summary, sby_smp_akreditasi_summary
  - sby_rasio_murid_guru, sby_penduduk_usia_summary

Analitik (tujuan proyek):
  - gold_demand_proyeksi       : proyeksi demand SD/SMP 2025-2030 (cohort survival)
  - gold_kapasitas_kecamatan   : audit kapasitas per kecamatan
  - gold_gap_analysis          : demand vs kapasitas, siswa tak tertampung
  - gold_rekomendasi_usb_rkb   : prioritas USB/RKB per kecamatan

Input  : hdfs:///lakehouse/silver/<table>
Output : hdfs:///lakehouse/gold/<table>
"""

import os
from itertools import chain
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    col, lit, current_timestamp, coalesce, when, greatest, row_number, create_map
)
from pyspark.sql.functions import round as sround
from pyspark.sql.functions import sum as Fsum
from pyspark.sql.functions import max as Fmax
from pyspark.sql.functions import count as Fcount
from pyspark.sql.functions import ceil as Fceil
from delta import configure_spark_with_delta_pip

builder = (
    SparkSession.builder
    .appName("medallion-gold")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"
SILVER = f"{HDFS_PATH}/lakehouse/silver"
GOLD = f"{HDFS_PATH}/lakehouse/gold"

# --- Parameter & asumsi analisis (didokumentasikan untuk transparansi) ---
TAHUN_BASIS = 2025                       # snapshot penduduk-usia (Maret 2025)
HORIZON = list(range(2025, 2031))        # proyeksi 2025-2030
KAPASITAS_PER_KELAS = 32                 # standar siswa per rombongan belajar
USIA_SD = (7, 12)
USIA_SMP = (13, 15)

BULAN = {"Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6,
         "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12}
BULAN_MAP = create_map([lit(x) for x in chain(*BULAN.items())])

# Peta umur (angka) -> nama kolom dataset penduduk-usia
ANGKA = {0: "nol", 1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima", 6: "enam",
         7: "tujuh", 8: "delapan", 9: "sembilan", 10: "sepuluh", 11: "sebelas", 12: "duabelas",
         13: "tigabelas", 14: "empatbelas", 15: "limabelas", 16: "enambelas"}


def read_silver(table):
    return spark.read.format("delta").load(f"{SILVER}/{table}")


def write_gold(df, table):
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(f"{GOLD}/{table}")


def latest_snapshot(table):
    """Ambil satu baris snapshot terbaru (tahun & bulan terakhir) per kecamatan."""
    df = read_silver(table).withColumn("_mrank", BULAN_MAP[col("periode_norm")])
    w = Window.partitionBy("kecamatan_key").orderBy(col("tahun").desc(), col("_mrank").desc())
    return df.withColumn("_rn", row_number().over(w)).filter(col("_rn") == 1).drop("_rn", "_mrank")


def pop_umur(a):
    return coalesce(col(f"{ANGKA[a]}_laki"), lit(0)) + coalesce(col(f"{ANGKA[a]}_perempuan"), lit(0))


# ============================================================================
# 1. TABEL DESKRIPTIF (snapshot terbaru per kecamatan)
# ============================================================================
def build_descriptive():
    print("\n[Deskriptif] snapshot terbaru per kecamatan")
    mapping = [
        ("sby_sekolah_negeri_swasta", "sby_sekolah_per_kecamatan"),
        ("sby_siswa_negeri_swasta", "sby_siswa_per_kecamatan"),
        ("sby_sd_akreditasi_kecamatan", "sby_sd_akreditasi_summary"),
        ("sby_smp_akreditasi_kecamatan", "sby_smp_akreditasi_summary"),
        ("sby_sekolah_murid_guru_rasio", "sby_rasio_murid_guru"),
    ]
    for src, dst in mapping:
        df = latest_snapshot(src).withColumn("_gold_created_at", current_timestamp())
        write_gold(df, dst)
        print(f"  - {dst:<28} {df.count()} kecamatan")

    # penduduk: agregasi umur ke level kecamatan
    pop = read_silver("sby_penduduk_usia")
    pop_kec = pop.groupBy("kecamatan_key", "kecamatan_norm").agg(
        *[Fsum(pop_umur(a)).alias(f"usia_{a}") for a in range(0, 16)]
    ).withColumn("_gold_created_at", current_timestamp())
    write_gold(pop_kec, "sby_penduduk_usia_summary")
    print(f"  - sby_penduduk_usia_summary   {pop_kec.count()} kecamatan")


# ============================================================================
# 2. DEMAND — proyeksi cohort survival
# ============================================================================
def build_demand():
    print("\n[1/4] gold_demand_proyeksi (cohort survival)")
    pop = read_silver("sby_penduduk_usia")
    pop_kec = pop.groupBy("kecamatan_key", "kecamatan_norm").agg(
        *[Fsum(pop_umur(a)).alias(f"u{a}") for a in range(2, 16)]
    )

    proyeksi = None
    for Y in HORIZON:
        k = Y - TAHUN_BASIS
        sd_ages = [a for a in range(USIA_SD[0] - k, USIA_SD[1] - k + 1) if a in ANGKA]
        smp_ages = [a for a in range(USIA_SMP[0] - k, USIA_SMP[1] - k + 1) if a in ANGKA]
        sd_expr = sum([col(f"u{a}") for a in sd_ages]) if sd_ages else lit(0)
        smp_expr = sum([col(f"u{a}") for a in smp_ages]) if smp_ages else lit(0)
        row = pop_kec.select(
            "kecamatan_key", "kecamatan_norm",
            lit(Y).alias("tahun_proyeksi"),
            sd_expr.cast("long").alias("demand_sd"),
            smp_expr.cast("long").alias("demand_smp"),
            (sd_expr + smp_expr).cast("long").alias("demand_total"),
        )
        proyeksi = row if proyeksi is None else proyeksi.unionByName(row)

    proyeksi = proyeksi.withColumn("_gold_created_at", current_timestamp())
    write_gold(proyeksi, "gold_demand_proyeksi")
    print(f"  OK {proyeksi.count()} baris (kecamatan x tahun)")
    return proyeksi


# ============================================================================
# 3. KAPASITAS — pagu akreditasi + murid aktual (proven floor)
# ============================================================================
def build_kapasitas():
    print("\n[2/4] gold_kapasitas_kecamatan")
    akr = read_silver("sby_sekolah_akreditasi")
    tahun_pagu = akr.agg(Fmax("tahun").alias("t")).collect()[0]["t"]
    pagu = akr.filter(col("tahun") == tahun_pagu) \
              .filter(col("kecamatan_key").isNotNull()) \
              .groupBy("kecamatan_key", "kecamatan_norm").agg(
        Fsum(coalesce(col("kapasitas_pagu_siswa"), lit(0))).cast("long").alias("total_pagu"),
        Fsum(coalesce(col("jumlah_ruang_kelas"), lit(0))).cast("long").alias("total_ruang_kelas"),
        Fsum(coalesce(col("jumlah_rombel"), lit(0))).cast("long").alias("total_rombel"),
        Fcount("*").alias("jumlah_sekolah"),
    )

    # murid aktual = siswa yang nyata dilayani (snapshot terbaru) -> kapasitas minimal
    rasio = latest_snapshot("sby_sekolah_murid_guru_rasio")
    murid = rasio.select(
        "kecamatan_key",
        (coalesce(col("sd_murid"), lit(0)) + coalesce(col("smp_murid"), lit(0))
         + coalesce(col("mi_murid"), lit(0)) + coalesce(col("mts_murid"), lit(0)))
        .cast("long").alias("murid_aktual"),
    )

    kapasitas = (pagu.join(murid, "kecamatan_key", "left")
                 .withColumn("murid_aktual", coalesce(col("murid_aktual"), lit(0)))
                 # kapasitas = yang lebih besar antara pagu terdaftar & siswa nyata dilayani
                 .withColumn("kapasitas", greatest(col("total_pagu"), col("murid_aktual")).cast("long"))
                 .withColumn("tahun_kapasitas", lit(tahun_pagu))
                 .withColumn("_gold_created_at", current_timestamp()))
    write_gold(kapasitas, "gold_kapasitas_kecamatan")
    print(f"  OK {kapasitas.count()} kecamatan (pagu thn {tahun_pagu}; kapasitas=max(pagu,murid))")
    return kapasitas


# ============================================================================
# 4. GAP — demand vs kapasitas
# ============================================================================
def build_gap(proyeksi, kapasitas):
    print("\n[3/4] gold_gap_analysis")
    cap = kapasitas.select("kecamatan_key", "kapasitas", "total_pagu", "murid_aktual",
                           "total_ruang_kelas", "jumlah_sekolah")
    gap = (proyeksi.join(cap, "kecamatan_key", "left")
           .withColumn("kapasitas", coalesce(col("kapasitas"), lit(0)))
           .withColumn("gap", (col("demand_total") - col("kapasitas")).cast("long"))
           .withColumn("siswa_tak_tertampung", greatest(col("gap"), lit(0)).cast("long"))
           .withColumn("utilisasi_pct",
                       when(col("kapasitas") > 0, sround(col("demand_total") / col("kapasitas") * 100, 1)))
           .withColumn("_gold_created_at", current_timestamp()))
    write_gold(gap, "gold_gap_analysis")
    print(f"  OK {gap.count()} baris gap")
    return gap


# ============================================================================
# 5. REKOMENDASI USB/RKB (tahun horizon terakhir)
# ============================================================================
def build_rekomendasi(gap, kapasitas):
    print("\n[4/4] gold_rekomendasi_usb_rkb")
    tahun_target = HORIZON[-1]
    base = gap.filter(col("tahun_proyeksi") == tahun_target) \
        .join(kapasitas.select("kecamatan_key", "total_rombel"), "kecamatan_key", "left")

    rekom = (base
             .withColumn("rata_kapasitas_sekolah",
                         when(col("jumlah_sekolah") > 0, col("kapasitas") / col("jumlah_sekolah")).otherwise(lit(0)))
             .withColumn("ruang_kelas_baru",
                         Fceil(col("siswa_tak_tertampung") / lit(KAPASITAS_PER_KELAS)).cast("int"))
             .withColumn("rekomendasi",
                         when(col("siswa_tak_tertampung") <= 0, lit("CUKUP"))
                         .when(col("siswa_tak_tertampung") >= col("rata_kapasitas_sekolah"), lit("USB"))
                         .otherwise(lit("RKB")))
             .withColumn("skor_prioritas", col("siswa_tak_tertampung").cast("long")))

    w = Window.orderBy(col("skor_prioritas").desc())
    rekom = (rekom.withColumn("peringkat_prioritas", row_number().over(w))
             .select("peringkat_prioritas", "kecamatan_key", "kecamatan_norm",
                     lit(tahun_target).alias("tahun_target"),
                     "demand_total", "kapasitas", "siswa_tak_tertampung", "utilisasi_pct",
                     "jumlah_sekolah", "ruang_kelas_baru", "rekomendasi", "skor_prioritas")
             .withColumn("_gold_created_at", current_timestamp()))
    write_gold(rekom, "gold_rekomendasi_usb_rkb")
    print(f"  OK {rekom.count()} kecamatan (target {tahun_target})")
    print("\n  Top 5 prioritas:")
    rekom.orderBy("peringkat_prioritas").select(
        "peringkat_prioritas", "kecamatan_norm", "demand_total", "kapasitas",
        "siswa_tak_tertampung", "utilisasi_pct", "rekomendasi", "ruang_kelas_baru").show(5, truncate=False)


def main():
    print("=" * 70)
    print(" GOLD LAYER — Analytics Audit Kapasitas & USB/RKB")
    print("=" * 70)
    build_descriptive()
    proyeksi = build_demand()
    kapasitas = build_kapasitas()
    gap = build_gap(proyeksi, kapasitas)
    build_rekomendasi(gap, kapasitas)
    print("=" * 70)
    print(" Gold selesai.")
    print("=" * 70)
    spark.stop()


if __name__ == "__main__":
    main()
