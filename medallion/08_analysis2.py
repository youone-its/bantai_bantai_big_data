"""
ANALYSIS 2 — DSS: SCGI, K-Means Clustering & Model Evaluation
================================================================
Script PySpark untuk:
  1. Export Gold tables yang sudah ada ke CSV (untuk notebooks)
  2. MAPE Evaluation  (akurasi proyeksi cohort)
  3. School Capacity Gap Index (SCGI)
  4. K-Means Clustering (K=4) + Silhouette + Davies-Bouldin
  5. Simpan tabel Gold baru & evaluation metrics

Output Gold Tables:
  - gold_school_capacity_gap_index
  - gold_cluster_priority
  - gold_evaluation_metrics

Output CSV (dipasang di /app/exports/ → dibaca notebook):
  - demand_proyeksi.csv  kapasitas.csv  gap_analysis.csv  rekomendasi.csv
  - mape_detail.csv  scgi.csv  clusters.csv  elbow_data.csv  evaluation.csv

"""

import os, json
import numpy as np
import pandas as pd
from itertools import chain

from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    col, lit, current_timestamp, coalesce, when,
    greatest, least, row_number
)
from pyspark.sql.functions import round   as sround
from pyspark.sql.functions import sum     as Fsum
from pyspark.sql.functions import max     as Fmax
from pyspark.sql.functions import avg     as Favg
from pyspark.sql.functions import abs     as Fabs
from pyspark.sql.functions import create_map

from pyspark.ml.clustering  import KMeans
from pyspark.ml.evaluation  import ClusteringEvaluator
from pyspark.ml.feature     import VectorAssembler, MinMaxScaler
from pyspark.sql.types      import IntegerType, StringType
from pyspark.sql.functions  import udf

from delta import configure_spark_with_delta_pip

# --------------------------------------------------------------------------
# Spark Session
# --------------------------------------------------------------------------
builder = (
    SparkSession.builder
    .appName("medallion-analysis2")
    .config("spark.sql.extensions",        "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST  = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT  = os.getenv("HDFS_PORT", "8020")
HDFS_PATH  = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"
SILVER     = f"{HDFS_PATH}/lakehouse/silver"
GOLD       = f"{HDFS_PATH}/lakehouse/gold"
EXPORT_DIR = "/app/exports"          # → host: ./medallion/exports/

# Analytic parameters (documented for transparency)
N_CLUSTERS        = 4
TAHUN_BASIS       = 2025
TAHUN_HORIZON     = 2030
KAPASITAS_PER_RKB = 32

BULAN = {"Januari":1,"Februari":2,"Maret":3,"April":4,"Mei":5,"Juni":6,
          "Juli":7,"Agustus":8,"September":9,"Oktober":10,"November":11,"Desember":12}
BULAN_MAP = create_map([lit(x) for x in chain(*BULAN.items())])

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def read_silver(table):
    return spark.read.format("delta").load(f"{SILVER}/{table}")

def read_gold(table):
    return spark.read.format("delta").load(f"{GOLD}/{table}")

def write_gold(df, table):
    (df.write.format("delta").mode("overwrite")
       .option("overwriteSchema", "true")
       .save(f"{GOLD}/{table}"))

def export_csv(df, name):
    """Tulis DataFrame (kecil) ke CSV lokal untuk dibaca notebook."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = f"{EXPORT_DIR}/{name}.csv"
    df.toPandas().to_csv(path, index=False)
    print(f"  → {path}")

def latest_snapshot(table):
    df = read_silver(table).withColumn("_mrank", BULAN_MAP[col("periode_norm")])
    w  = Window.partitionBy("kecamatan_key").orderBy(col("tahun").desc(), col("_mrank").desc())
    return df.withColumn("_rn", row_number().over(w)).filter(col("_rn") == 1).drop("_rn","_mrank")


# ============================================================================
# STEP 0 — Export existing Gold tables to CSV (input untuk notebooks)
# ============================================================================
def export_existing_gold():
    print("\n[0] Export existing Gold → CSV...")
    try:
        export_csv(
            read_gold("gold_demand_proyeksi").select(
                "kecamatan_key","kecamatan_norm","tahun_proyeksi",
                "demand_sd","demand_smp","demand_total"),
            "demand_proyeksi")
        export_csv(
            read_gold("gold_kapasitas_kecamatan").select(
                "kecamatan_key","kecamatan_norm","kapasitas","total_pagu",
                "murid_aktual","total_ruang_kelas","jumlah_sekolah"),
            "kapasitas")
        export_csv(
            read_gold("gold_gap_analysis").select(
                "kecamatan_key","kecamatan_norm","tahun_proyeksi",
                "demand_total","kapasitas","gap","siswa_tak_tertampung","utilisasi_pct"),
            "gap_analysis")
        export_csv(
            read_gold("gold_rekomendasi_usb_rkb").select(
                "peringkat_prioritas","kecamatan_key","kecamatan_norm","tahun_target",
                "demand_total","kapasitas","siswa_tak_tertampung","utilisasi_pct",
                "jumlah_sekolah","ruang_kelas_baru","rekomendasi"),
            "rekomendasi")
        print("  OK")
    except Exception as e:
        print(f"  WARN: {e}")


# ============================================================================
# STEP 1 — MAPE Evaluation (Cohort Projection Accuracy)
# ============================================================================
def compute_mape():
    """
    Evaluasi akurasi model cohort survival:

        MAPE = (1/N) × Σ |Proyeksi_2025ᵢ − Aktualᵢ| / Aktualᵢ × 100

    Proyeksi : demand_total tahun 2025 dari gold_demand_proyeksi
                (populasi usia 7-15 → usia SD+SMP, k=0)
    Aktual   : sd_murid + smp_murid dari snapshot terbaru
                sby_sekolah_murid_guru_rasio

    Referensi:
      Hyndman & Koehler (2006) — "Another look at measures of forecast accuracy",
      International Journal of Forecasting 22(4): 679-688.
    """
    print("\n[1] MAPE Evaluation (Cohort Projection)...")

    rasio  = latest_snapshot("sby_sekolah_murid_guru_rasio")
    actual = (rasio
              .select("kecamatan_key",
                      (coalesce(col("sd_murid"), lit(0)) +
                       coalesce(col("smp_murid"), lit(0)))
                      .cast("double").alias("actual_murid"))
              .filter(col("actual_murid") > 0))

    projected = (read_gold("gold_demand_proyeksi")
                 .filter(col("tahun_proyeksi") == TAHUN_BASIS)
                 .select("kecamatan_key",
                         col("demand_total").cast("double").alias("projected_murid")))

    mape_df = (projected
               .join(actual, "kecamatan_key", "inner")
               .withColumn("ape",
                   Fabs(col("projected_murid") - col("actual_murid"))
                   / col("actual_murid") * 100))

    n_kec       = mape_df.count()
    mape_value  = round(float(mape_df.agg(Favg("ape")).collect()[0][0] or 0), 2)
    print(f"  N kecamatan  = {n_kec}")
    print(f"  MAPE         = {mape_value}%  "
          f"({'BAIK <20%' if mape_value < 20 else 'CUKUP <30%' if mape_value < 30 else 'PERLU PERBAIKAN'})")

    export_csv(mape_df.select("kecamatan_key","projected_murid","actual_murid","ape"), "mape_detail")
    return mape_value


# ============================================================================
# STEP 2 — School Capacity Gap Index (SCGI)
# ============================================================================
def build_scgi():
    """
    SCGI = 0.50 × deficit_rate + 0.30 × utilisasi_norm + 0.20 × growth_rate

    Komponen:
      deficit_rate   = max(0, demand_2030 − kapasitas) / demand_2030
                       → proporsi demand yang tidak dapat dilayani kapasitas saat ini
      utilisasi_norm = min(utilisasi_2030 / 200, 1.0)
                       → tingkat utilisasi ternormalisasi (cap 200%)
      growth_rate    = max(0, (demand_2030 − demand_2025) / demand_2025), cap 1.0
                       → tekanan pertumbuhan demand selama horizon proyeksi

    SCGI ∈ [0, 100]  →  Kategori:
      ≥ 70 : KRITIS   (intervensi mendesak)
      ≥ 50 : TINGGI   (perlu perencanaan segera)
      ≥ 30 : SEDANG   (monitoring ketat)
      >  0 : RENDAH   (perhatikan perkembangan)
      ≤  0 : AMAN     (kapasitas cukup)
    """
    print("\n[2] Membangun SCGI (School Capacity Gap Index)...")

    d_all  = read_gold("gold_demand_proyeksi")
    kap    = read_gold("gold_kapasitas_kecamatan")
    gap_all = read_gold("gold_gap_analysis")

    d2025 = (d_all.filter(col("tahun_proyeksi") == TAHUN_BASIS)
             .select("kecamatan_key","kecamatan_norm",
                     col("demand_total").cast("double").alias("demand_2025")))
    d2030 = (d_all.filter(col("tahun_proyeksi") == TAHUN_HORIZON)
             .select("kecamatan_key",
                     col("demand_total").cast("double").alias("demand_2030")))
    g2030 = (gap_all.filter(col("tahun_proyeksi") == TAHUN_HORIZON)
             .select("kecamatan_key",
                     coalesce(col("utilisasi_pct"),lit(0.0)).cast("double").alias("utilisasi_2030"),
                     coalesce(col("siswa_tak_tertampung"),lit(0)).cast("double").alias("deficit_2030")))
    kap_s = kap.select("kecamatan_key",
                        coalesce(col("kapasitas"),lit(0)).cast("double").alias("kapasitas"),
                        col("jumlah_sekolah"))

    base = (d2025
            .join(d2030,  "kecamatan_key")
            .join(g2030,  "kecamatan_key")
            .join(kap_s,  "kecamatan_key"))

    scgi = (base
        .withColumn("deficit_rate",
            when(col("demand_2030") > 0,
                 greatest(lit(0.0),
                          (col("demand_2030") - col("kapasitas")) / col("demand_2030")))
            .otherwise(lit(0.0)))
        .withColumn("utilisasi_norm",
            least(lit(1.0), col("utilisasi_2030") / lit(200.0)))
        .withColumn("growth_rate",
            when(col("demand_2025") > 0,
                 least(lit(1.0), greatest(lit(0.0),
                       (col("demand_2030") - col("demand_2025")) / col("demand_2025"))))
            .otherwise(lit(0.0)))
        .withColumn("scgi_raw",       # composite 0-1
            lit(0.50) * col("deficit_rate") +
            lit(0.30) * col("utilisasi_norm") +
            lit(0.20) * col("growth_rate"))
        .withColumn("scgi_score",     # scaled 0-100
            sround(least(lit(100.0), col("scgi_raw") * lit(100.0)), 2))
        .withColumn("scgi_category",
            when(col("scgi_score") >= 70, lit("KRITIS"))
            .when(col("scgi_score") >= 50, lit("TINGGI"))
            .when(col("scgi_score") >= 30, lit("SEDANG"))
            .when(col("scgi_score") >  0, lit("RENDAH"))
            .otherwise(lit("AMAN")))
        .withColumn("_gold_created_at", current_timestamp()))

    w    = Window.orderBy(col("scgi_score").desc())
    scgi = scgi.withColumn("scgi_rank", row_number().over(w))

    write_gold(scgi, "gold_school_capacity_gap_index")
    export_csv(scgi.select(
        "scgi_rank","kecamatan_key","kecamatan_norm",
        "demand_2025","demand_2030","kapasitas","jumlah_sekolah",
        "deficit_rate","utilisasi_norm","growth_rate","scgi_raw",
        "utilisasi_2030","deficit_2030","scgi_score","scgi_category"), "scgi")

    cnt = scgi.count()
    print(f"  OK {cnt} kecamatan")
    print()
    scgi.orderBy("scgi_rank").select(
        "scgi_rank","kecamatan_norm","scgi_score","scgi_category"
    ).show(cnt, truncate=False)
    return scgi


# ============================================================================
# STEP 3 — K-Means Clustering + Silhouette + Davies-Bouldin
# ============================================================================
def _davies_bouldin(X: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> float:
    """
    Manual Davies-Bouldin Index.

        DB = (1/K) × Σᵢ max_{j≠i} [ (sᵢ + sⱼ) / d(cᵢ,cⱼ) ]

    sᵢ = intra-cluster avg distance ke centroid i
    d(cᵢ,cⱼ) = Euclidean distance antar centroid

    Interpretasi: DB yang lebih kecil → cluster lebih kompak & terpisah.
      DB < 1.0 : Baik
      DB < 2.0 : Cukup
      DB ≥ 2.0 : Lemah
    """
    k = len(centers)
    s = []
    for i in range(k):
        mask = labels == i
        s.append(float(np.mean(np.linalg.norm(X[mask] - centers[i], axis=1)))
                 if mask.sum() > 0 else 0.0)
    db = 0.0
    for i in range(k):
        max_r = max(
            ((s[i] + s[j]) / np.linalg.norm(centers[i] - centers[j]))
            for j in range(k)
            if i != j and np.linalg.norm(centers[i] - centers[j]) > 0
        ) if k > 1 else 0.0
        db += max_r
    return round(db / k, 4)


def build_clusters(scgi_df):
    """
    K-Means (K=4) menggunakan fitur SCGI yang sudah ternormalisasi:
      - deficit_rate   : tingkat defisit kapasitas (0-1)
      - utilisasi_norm : tingkat utilisasi ternormalisasi (0-1)
      - growth_rate    : tekanan pertumbuhan (0-1)
      - scgi_raw       : SCGI komposit (0-1)

    Cluster di-rank berdasarkan rata-rata fitur → priority label:
      Priority 1: KRITIS  (cluster dg fitur tertinggi)
      Priority 2: TINGGI
      Priority 3: SEDANG
      Priority 4: RENDAH  (cluster paling aman)

    Evaluasi:
      - Silhouette Score  (PySpark ClusteringEvaluator)
        Range −1 to 1; > 0.5 = Baik, > 0.25 = Cukup
      - Davies-Bouldin Index  (implementasi manual numpy)
        < 1.0 = Baik, < 2.0 = Cukup
    """
    print(f"\n[3] K-Means Clustering (K={N_CLUSTERS})...")

    feature_cols = ["deficit_rate", "utilisasi_norm", "growth_rate", "scgi_raw"]

    # -- Assemble & scale features --
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw",
                                handleInvalid="skip")
    df_vec    = assembler.transform(scgi_df)
    scaler_m  = MinMaxScaler(inputCol="features_raw", outputCol="features").fit(df_vec)
    df_scaled = scaler_m.transform(df_vec)

    # -- Elbow curve (K=2..8) --
    print("  Elbow curve K=2..8...")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    elbow = []
    for k in range(2, 9):
        m = KMeans(k=k, seed=42, featuresCol="features", maxIter=100).fit(df_scaled)
        elbow.append({"k": k, "inertia": round(m.summary.trainingCost, 4)})
    pd.DataFrame(elbow).to_csv(f"{EXPORT_DIR}/elbow_data.csv", index=False)
    print(f"  → {EXPORT_DIR}/elbow_data.csv")

    # -- Final model K=4 --
    km      = KMeans(k=N_CLUSTERS, seed=42, featuresCol="features", maxIter=300)
    model   = km.fit(df_scaled)
    df_pred = model.transform(df_scaled)

    # -- Silhouette Score (PySpark) --
    evaluator  = ClusteringEvaluator(featuresCol="features", metricName="silhouette",
                                     distanceMeasure="squaredEuclidean")
    silhouette = round(evaluator.evaluate(df_pred), 4)
    print(f"  Silhouette Score     = {silhouette}")

    # -- Davies-Bouldin (manual numpy) --
    pdf      = df_pred.select(feature_cols + ["prediction"]).toPandas()
    X        = pdf[feature_cols].values.astype(float)
    labels   = pdf["prediction"].values
    # clusterCenters() sudah mengembalikan numpy.ndarray di PySpark 3.5
    raw_centers = model.clusterCenters()
    centers  = np.array([c.toArray() if hasattr(c, 'toArray') else np.array(c)
                         for c in raw_centers])
    db_score = _davies_bouldin(X, labels, centers)
    print(f"  Davies-Bouldin Index = {db_score}")

    # -- Assign priority labels --
    cluster_means  = pd.DataFrame(X, columns=feature_cols)
    cluster_means["cluster"] = labels
    cluster_rank   = cluster_means.groupby("cluster").mean().mean(axis=1).sort_values(ascending=False)
    priority_map   = {int(c): i + 1 for i, c in enumerate(cluster_rank.index)}
    label_map      = {1: "KRITIS", 2: "TINGGI", 3: "SEDANG", 4: "RENDAH"}

    pmap_bc = spark.sparkContext.broadcast(priority_map)
    lmap_bc = spark.sparkContext.broadcast(label_map)

    get_priority = udf(lambda p: pmap_bc.value.get(int(p), N_CLUSTERS), IntegerType())
    get_label    = udf(lambda p: lmap_bc.value.get(pmap_bc.value.get(int(p), N_CLUSTERS),
                                                    "RENDAH"), StringType())

    result = (df_pred
        .withColumn("cluster_id",     col("prediction"))
        .withColumn("priority_rank",  get_priority(col("prediction")))
        .withColumn("priority_label", get_label(col("prediction")))
        .select("kecamatan_key","kecamatan_norm",
                "scgi_score","scgi_category","scgi_rank",
                "demand_2025","demand_2030","kapasitas",
                "deficit_rate","utilisasi_norm","growth_rate","scgi_raw",
                "utilisasi_2030","deficit_2030",
                "cluster_id","priority_rank","priority_label",
                "_gold_created_at"))

    write_gold(result, "gold_cluster_priority")
    export_csv(result.drop("_gold_created_at"), "clusters")

    print(f"  OK {result.count()} kecamatan ter-cluster")
    result.orderBy("priority_rank","scgi_rank").select(
        "priority_rank","priority_label","kecamatan_norm","scgi_score","cluster_id"
    ).show(50, truncate=False)

    return silhouette, db_score


# ============================================================================
# STEP 4 — Simpan Evaluation Metrics ke Gold
# ============================================================================
def save_evaluation(mape, silhouette, db_score):
    print("\n[4] Menyimpan gold_evaluation_metrics...")

    def status_mape(v):
        return "BAIK" if v < 20 else ("CUKUP" if v < 30 else "PERLU_PERBAIKAN")
    def status_sil(v):
        return "BAIK" if v > 0.5 else ("CUKUP" if v > 0.25 else "LEMAH")
    def status_db(v):
        return "BAIK" if v < 1.0 else ("CUKUP" if v < 2.0 else "LEMAH")

    rows = [
        ("cohort_projection", "MAPE", round(float(mape), 2), "persen",
         status_mape(mape), "< 20% = Baik | < 30% = Cukup | ≥ 30% = Perlu Perbaikan"),
        ("kmeans_clustering", "Silhouette_Score", float(silhouette), "rasio",
         status_sil(silhouette), "0.5–1.0 = Baik | 0.25–0.5 = Cukup | < 0.25 = Lemah"),
        ("kmeans_clustering", "Davies_Bouldin_Index", float(db_score), "rasio",
         status_db(db_score), "< 1.0 = Baik | < 2.0 = Cukup | ≥ 2.0 = Lemah"),
    ]
    schema = ["model", "metric", "value", "unit", "status", "interpretasi"]
    df_eval = (spark.createDataFrame(rows, schema)
               .withColumn("_generated_at", current_timestamp()))

    write_gold(df_eval, "gold_evaluation_metrics")
    export_csv(df_eval, "evaluation")

    print(f"  MAPE             = {mape}%  [{status_mape(mape)}]")
    print(f"  Silhouette Score = {silhouette}  [{status_sil(silhouette)}]")
    print(f"  Davies-Bouldin   = {db_score}  [{status_db(db_score)}]")


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 70)
    print(" ANALYSIS 2 — SCGI, K-Means & Model Evaluation")
    print("=" * 70)

    export_existing_gold()
    mape                = compute_mape()
    scgi_df             = build_scgi()
    silhouette, db_score = build_clusters(scgi_df)
    save_evaluation(mape, silhouette, db_score)

    print("=" * 70)
    print(" ANALYSIS 2 SELESAI")
    print()
    print("  Gold Tables baru:")
    print("    gold_school_capacity_gap_index")
    print("    gold_cluster_priority")
    print("    gold_evaluation_metrics")
    print()
    print(f"  CSV exports : {EXPORT_DIR}/")
    print("=" * 70)
    spark.stop()


if __name__ == "__main__":
    main()
