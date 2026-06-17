#tes123
"""
GOLD LAYER: Business Analytics & Aggregations
=============================================
Membuat table Gold dengan agregasi dan analisis:
1. Weather analytics per kota (temperature trends, extremes)
2. News analytics (top news, source distribution)
3. Cross-join API + RSS (correlate weather with news)
4. Time-series analysis dengan Window Functions
5. Open Data Surabaya analytics (sekolah, siswa, akreditasi)
"""

import os
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, window, avg, min, max, count, sum as spark_sum,
    rank, dense_rank, row_number, lead, lag
)
from pyspark.sql.window import Window as WindowSpec
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

builder = (
    SparkSession.builder
    .appName("medallion-bronze")
    .config(
        "spark.sql.extensions",
        "io.delta.sql.DeltaSparkSessionExtension"
    )
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    )
)

spark = configure_spark_with_delta_pip(builder).getOrCreate()

print("="*70)
print(" GOLD LAYER: Business Analytics & Aggregations")
print("="*70)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

LAKEHOUSE_PATH = f"{HDFS_PATH}/lakehouse"
SILVER_PATH = f"{LAKEHOUSE_PATH}/silver"
GOLD_PATH = f"{LAKEHOUSE_PATH}/gold"

OPEN_DATA_GOLD_TABLES = [
    {"silver": "sby_sekolah_negeri_swasta", "gold": "sby_sekolah_per_kecamatan"},
    {"silver": "sby_siswa_negeri_swasta", "gold": "sby_siswa_per_kecamatan"},
    {"silver": "sby_sd_akreditasi_kecamatan", "gold": "sby_sd_akreditasi_summary"},
    {"silver": "sby_smp_akreditasi_kecamatan", "gold": "sby_smp_akreditasi_summary"},
    {"silver": "sby_sekolah_murid_guru_rasio", "gold": "sby_rasio_murid_guru"},
]

# ============================================================================
# WEATHER ANALYTICS (Reproduces old Spark ETS analysis)
# ============================================================================

print("\n🌡️  Creating Weather Analytics Gold Table...")
try:
    df_weather = spark.read.format("delta").load(f"{SILVER_PATH}/weather_api")
    
    # Window function untuk time-series analysis
    window_spec = WindowSpec.partitionBy("kode_kota").orderBy("timestamp")
    
    # Analisis 1: Suhu kota (current + trends)
    weather_analytics = df_weather \
        .withColumn("temp_lag1", lag("temperature").over(window_spec)) \
        .withColumn("temp_change", col("temperature") - col("temp_lag1")) \
        .withColumn("temp_ma3", 
            avg("temperature").over(window_spec.rowsBetween(-2, 0))) \
        .select(
            col("kode_kota"),
            col("nama_kota"),
            col("temperature").alias("temp_current"),
            col("temp_change").alias("temp_change_1h"),
            col("temp_ma3").alias("temp_moving_avg_3h"),
            col("humidity"),
            col("wind_speed"),
            col("timestamp").alias("reading_time"),
            current_timestamp().alias("gold_created_at")
        )
    
    # Analisis 2: Kondisi ekstrem per kota
    extremes = df_weather \
        .groupBy("kode_kota", "nama_kota") \
        .agg(
            max("temperature").alias("max_temp"),
            min("temperature").alias("min_temp"),
            avg("temperature").alias("avg_temp"),
            max("humidity").alias("max_humidity"),
            max("wind_speed").alias("max_wind"),
            count("*").alias("reading_count")
        ) \
        .withColumn("temp_range", col("max_temp") - col("min_temp"))
    
    # Tulis weather analytics
    weather_analytics.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/weather_analytics")
    extremes.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/weather_extremes")
    
    print(f"✅ Weather analytics: {weather_analytics.count()} records")
    print(f"✅ Extremes summary: {extremes.count()} kota")
    
except Exception as e:
    print(f"⚠️  Error in weather analytics: {e}")

# ============================================================================
# NEWS ANALYTICS
# ============================================================================

print("\n📰 Creating News Analytics Gold Table...")
try:
    df_news = spark.read.format("delta").load(f"{SILVER_PATH}/weather_rss")
    
    # Analisis 1: News distribution by source
    news_by_source = df_news \
        .groupBy("sumber") \
        .agg(
            count("*").alias("article_count"),
            max("waktu_terbit").alias("latest_article")
        ) \
        .orderBy(col("article_count").desc())
    
    # Analisis 2: Recent news with ranking
    window_spec_news = WindowSpec.orderBy(col("waktu_terbit").desc())
    recent_news = df_news \
        .withColumn("news_rank", rank().over(window_spec_news)) \
        .filter(col("news_rank") <= 20) \
        .select(
            col("news_rank"),
            col("judul"),
            col("sumber"),
            col("waktu_terbit"),
            col("ringkasan"),
            current_timestamp().alias("gold_created_at")
        )
    
    # Tulis news analytics
    news_by_source.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/news_by_source")
    recent_news.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/recent_news")
    
    print(f"✅ News by source: {news_by_source.count()} sources")
    print(f"✅ Recent news (top 20): {recent_news.count()} articles")
    
except Exception as e:
    print(f"⚠️  Error in news analytics: {e}")

# ============================================================================
# CROSS-JOIN: WEATHER + NEWS CORRELATION
# ============================================================================

print("\n🔗 Creating Weather-News Correlation Gold Table...")
try:
    df_weather = spark.read.format("delta").load(f"{SILVER_PATH}/weather_api")
    df_news = spark.read.format("delta").load(f"{SILVER_PATH}/weather_rss")
    
    # Join weather + news dalam time window (1 jam)
    weather_hour = df_weather \
        .withColumn("hour", window(col("timestamp"), "1 hour")) \
        .groupBy("kode_kota", "nama_kota", "hour") \
        .agg(
            avg("temperature").alias("avg_temp"),
            max("humidity").alias("max_humidity"),
            max("wind_speed").alias("max_wind")
        )
    
    news_hour = df_news \
        .withColumn("hour", window(col("waktu_terbit"), "1 hour")) \
        .groupBy("hour") \
        .agg(count("*").alias("news_count"))
    
    # Cross join untuk correlation analysis
    correlation = weather_hour.join(
        news_hour, on="hour", how="left"
    ).fillna(0, subset=["news_count"])
    
    correlation.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/weather_news_correlation")
    print(f"✅ Weather-News correlation: {correlation.count()} records")
    
except Exception as e:
    print(f"⚠️  Error in correlation analysis: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print(" Weather Gold layer complete!")
print(f" Tables created:")
print(f"   - weather_analytics (time-series analysis)")
print(f"   - weather_extremes (summary stats)")
print(f"   - news_by_source (news distribution)")
print(f"   - recent_news (top 20 articles)")
print(f"   - weather_news_correlation (joined weather + news)")
print("="*70 + "\n")

# ============================================================================
# OPEN DATA SURABAYA: Business Analytics
# ============================================================================

print("\n" + "="*70)
print(" OPEN DATA SURABAYA: Business Analytics")
print("="*70)

for ds in OPEN_DATA_GOLD_TABLES:
    silver_table = ds["silver"]
    gold_table = ds["gold"]
    silver_input = f"{SILVER_PATH}/{silver_table}"
    gold_output = f"{GOLD_PATH}/{gold_table}"
    
    print(f"\n Creating: {gold_table}")
    print(f"  Silver Input: {silver_input}")
    print(f"  Gold Output: {gold_output}")
    
    try:
        df_silver = spark.read.format("delta").load(silver_input)
        record_count = df_silver.count()
        print(f"  Read {record_count} records from Silver")
        
        if record_count == 0:
            print(f"  No data, skipping...")
            continue
        
        df_gold = df_silver.withColumn("_gold_created_at", current_timestamp())
        
        df_gold.write.format("delta").mode("overwrite").save(gold_output)
        print(f"  Written {df_gold.count()} records to Gold")
        
    except Exception as e:
        print(f"  Error processing {silver_table}: {e}")
        print(f"  (Silver data may not exist yet)")

print("\n  Creating: sby_penduduk_usia_summary")
try:
    df_penduduk = spark.read.format("delta").load(f"{SILVER_PATH}/sby_penduduk_usia")
    if df_penduduk.count() > 0:
        penduduk_summary = df_penduduk \
            .withColumn("_gold_created_at", current_timestamp())
        penduduk_summary.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/sby_penduduk_usia_summary")
        print(f"  Written {penduduk_summary.count()} records to Gold")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*70)
print(" Gold layer complete!")
print(f" Weather tables: {GOLD_PATH}/weather_*")
print(f" Open Data SBY tables: {GOLD_PATH}/sby_*")
print("="*70 + "\n")

spark.stop()
