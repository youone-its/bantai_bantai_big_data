-- PostgreSQL Schema DDL: Serving Layer for Surabaya School Capacity Audit Lakehouse
-- This file acts as documentation and initialization schema for the PostgreSQL serving layer database.

-- Drop tables if they exist to allow clean setups
DROP TABLE IF EXISTS gold_data_quality_report CASCADE;
DROP TABLE IF EXISTS gold_evaluation_metrics CASCADE;
DROP TABLE IF EXISTS gold_cluster_priority CASCADE;
DROP TABLE IF EXISTS gold_school_capacity_gap_index CASCADE;
DROP TABLE IF EXISTS gold_rekomendasi_usb_rkb CASCADE;
DROP TABLE IF EXISTS gold_gap_analysis CASCADE;
DROP TABLE IF EXISTS gold_kapasitas_kecamatan CASCADE;
DROP TABLE IF EXISTS gold_demand_proyeksi CASCADE;

DROP TABLE IF EXISTS sby_sekolah_per_kecamatan CASCADE;
DROP TABLE IF EXISTS sby_siswa_per_kecamatan CASCADE;
DROP TABLE IF EXISTS sby_sd_akreditasi_summary CASCADE;
DROP TABLE IF EXISTS sby_smp_akreditasi_summary CASCADE;
DROP TABLE IF EXISTS sby_rasio_murid_guru CASCADE;
DROP TABLE IF EXISTS sby_penduduk_usia_summary CASCADE;

-- 1. Descriptive Tables
CREATE TABLE sby_sekolah_per_kecamatan (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    sekolah_negeri INT,
    sekolah_swasta INT,
    total_sekolah INT,
    tahun INT,
    periode VARCHAR(50),
    periode_norm VARCHAR(50)
);

CREATE TABLE sby_siswa_per_kecamatan (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    siswa_negeri INT,
    siswa_swasta INT,
    total_siswa INT,
    tahun INT,
    periode VARCHAR(50),
    periode_norm VARCHAR(50)
);

CREATE TABLE sby_sd_akreditasi_summary (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    akreditasi_a INT,
    akreditasi_b INT,
    akreditasi_c INT,
    belum_akreditasi INT,
    total_sekolah INT,
    tahun INT,
    periode VARCHAR(50),
    periode_norm VARCHAR(50)
);

CREATE TABLE sby_smp_akreditasi_summary (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    akreditasi_a INT,
    akreditasi_b INT,
    akreditasi_c INT,
    belum_akreditasi INT,
    total_sekolah INT,
    tahun INT,
    periode VARCHAR(50),
    periode_norm VARCHAR(50)
);

CREATE TABLE sby_rasio_murid_guru (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    sd_murid INT,
    sd_guru INT,
    sd_rasio DOUBLE PRECISION,
    smp_murid INT,
    smp_guru INT,
    smp_rasio DOUBLE PRECISION,
    mi_murid INT,
    mi_guru INT,
    mi_rasio DOUBLE PRECISION,
    mts_murid INT,
    mts_guru INT,
    mts_rasio DOUBLE PRECISION,
    tahun INT,
    periode VARCHAR(50),
    periode_norm VARCHAR(50)
);

CREATE TABLE sby_penduduk_usia_summary (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    usia_0 INT,
    usia_1 INT,
    usia_2 INT,
    usia_3 INT,
    usia_4 INT,
    usia_5 INT,
    usia_6 INT,
    usia_7 INT,
    usia_8 INT,
    usia_9 INT,
    usia_10 INT,
    usia_11 INT,
    usia_12 INT,
    usia_13 INT,
    usia_14 INT,
    usia_15 INT
);

-- 2. Analytical Tables
CREATE TABLE gold_demand_proyeksi (
    kecamatan_key VARCHAR(100),
    kecamatan_norm VARCHAR(100),
    tahun_proyeksi INT,
    demand_sd BIGINT,
    demand_smp BIGINT,
    demand_total BIGINT,
    PRIMARY KEY (kecamatan_key, tahun_proyeksi)
);

CREATE TABLE gold_kapasitas_kecamatan (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    total_pagu BIGINT,
    total_ruang_kelas BIGINT,
    total_rombel BIGINT,
    jumlah_sekolah BIGINT,
    murid_aktual BIGINT,
    kapasitas BIGINT,
    tahun_kapasitas INT
);

CREATE TABLE gold_gap_analysis (
    kecamatan_key VARCHAR(100),
    kecamatan_norm VARCHAR(100),
    tahun_proyeksi INT,
    demand_total BIGINT,
    kapasitas BIGINT,
    gap BIGINT,
    siswa_tak_tertampung BIGINT,
    utilisasi_pct DOUBLE PRECISION,
    PRIMARY KEY (kecamatan_key, tahun_proyeksi)
);

CREATE TABLE gold_rekomendasi_usb_rkb (
    peringkat_prioritas INT PRIMARY KEY,
    kecamatan_key VARCHAR(100),
    kecamatan_norm VARCHAR(100),
    tahun_target INT,
    demand_total BIGINT,
    kapasitas BIGINT,
    siswa_tak_tertampung BIGINT,
    utilisasi_pct DOUBLE PRECISION,
    jumlah_sekolah BIGINT,
    ruang_kelas_baru INT,
    rekomendasi VARCHAR(50),
    skor_prioritas BIGINT
);

CREATE TABLE gold_school_capacity_gap_index (
    scgi_rank INT PRIMARY KEY,
    kecamatan_key VARCHAR(100),
    kecamatan_norm VARCHAR(100),
    demand_2025 DOUBLE PRECISION,
    demand_2030 DOUBLE PRECISION,
    kapasitas DOUBLE PRECISION,
    jumlah_sekolah BIGINT,
    deficit_rate DOUBLE PRECISION,
    utilisasi_norm DOUBLE PRECISION,
    growth_rate DOUBLE PRECISION,
    scgi_raw DOUBLE PRECISION,
    utilisasi_2030 DOUBLE PRECISION,
    deficit_2030 DOUBLE PRECISION,
    scgi_score DOUBLE PRECISION,
    scgi_category VARCHAR(50)
);

CREATE TABLE gold_cluster_priority (
    kecamatan_key VARCHAR(100) PRIMARY KEY,
    kecamatan_norm VARCHAR(100),
    scgi_score DOUBLE PRECISION,
    scgi_category VARCHAR(50),
    scgi_rank INT,
    demand_2025 DOUBLE PRECISION,
    demand_2030 DOUBLE PRECISION,
    kapasitas DOUBLE PRECISION,
    deficit_rate DOUBLE PRECISION,
    utilisasi_norm DOUBLE PRECISION,
    growth_rate DOUBLE PRECISION,
    scgi_raw DOUBLE PRECISION,
    utilisasi_2030 DOUBLE PRECISION,
    deficit_2030 DOUBLE PRECISION,
    cluster_id INT,
    priority_rank INT,
    priority_label VARCHAR(50)
);

CREATE TABLE gold_evaluation_metrics (
    model VARCHAR(100),
    metric VARCHAR(100),
    value DOUBLE PRECISION,
    unit VARCHAR(50),
    status VARCHAR(50),
    interpretasi TEXT,
    PRIMARY KEY (model, metric)
);

CREATE TABLE gold_data_quality_report (
    id SERIAL PRIMARY KEY,
    "table" VARCHAR(100),
    layer VARCHAR(50),
    dimension VARCHAR(50),
    metric VARCHAR(100),
    value VARCHAR(255),
    status VARCHAR(50),
    note TEXT
);

-- Optimize queries with indexes
CREATE INDEX idx_demand_proyeksi_key ON gold_demand_proyeksi (kecamatan_key);
CREATE INDEX idx_gap_analysis_key ON gold_gap_analysis (kecamatan_key);
CREATE INDEX idx_rekomendasi_usb_rkb_key ON gold_rekomendasi_usb_rkb (kecamatan_key);
CREATE INDEX idx_cluster_priority_rank ON gold_cluster_priority (priority_rank);
