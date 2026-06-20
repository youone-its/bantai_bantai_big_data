# Data Quality Report — Lakehouse Open Data Surabaya

_Generated: 2026-06-20 05:10:42_


**Ringkasan:** 47 pemeriksaan — ✅ 43 PASS · ⚠️ 4 WARN · ❌ 0 FAIL


## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_penduduk_usia | row_count_vs_ckan | 153/153 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_penduduk_usia | null_nama_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_penduduk_usia | null_nama_kelurahan | 0 (0.0%) | ✅ PASS |  |
| sby_penduduk_usia | null_data_tahun | 0 (0.0%) | ✅ PASS |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_akreditasi | row_count_vs_ckan | 3162/3162 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_akreditasi | null_kode_sekolah | 0 (0.0%) | ✅ PASS |  |
| sby_sekolah_akreditasi | null_kecamatan | 58 (1.83%) | ⚠️ WARN |  |
| sby_sekolah_akreditasi | null_kapasitas_pagu_siswa | 58 (1.83%) | ⚠️ WARN |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_negeri_swasta | row_count_vs_ckan | 1612/1612 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_negeri_swasta | null_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_sekolah_negeri_swasta | null_periode | 0 (0.0%) | ✅ PASS |  |
| sby_sekolah_negeri_swasta | null_tahun | 0 (0.0%) | ✅ PASS |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_siswa_negeri_swasta | row_count_vs_ckan | 1643/1643 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_siswa_negeri_swasta | null_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_siswa_negeri_swasta | null_periode | 0 (0.0%) | ✅ PASS |  |
| sby_siswa_negeri_swasta | null_tahun | 0 (0.0%) | ✅ PASS |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sd_akreditasi_kecamatan | row_count_vs_ckan | 1581/1581 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sd_akreditasi_kecamatan | null_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_sd_akreditasi_kecamatan | null_periode | 0 (0.0%) | ✅ PASS |  |
| sby_sd_akreditasi_kecamatan | null_tahun | 0 (0.0%) | ✅ PASS |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_smp_akreditasi_kecamatan | row_count_vs_ckan | 1581/1581 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_smp_akreditasi_kecamatan | null_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_smp_akreditasi_kecamatan | null_periode | 0 (0.0%) | ✅ PASS |  |
| sby_smp_akreditasi_kecamatan | null_tahun | 0 (0.0%) | ✅ PASS |  |

## RECONCILIATION (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_murid_guru_rasio | row_count_vs_ckan | 1500/1500 | ✅ PASS |  |

## COMPLETENESS (bronze)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_murid_guru_rasio | null_kecamatan | 0 (0.0%) | ✅ PASS |  |
| sby_sekolah_murid_guru_rasio | null_periode | 0 (0.0%) | ✅ PASS |  |
| sby_sekolah_murid_guru_rasio | null_tahun | 0 (0.0%) | ✅ PASS |  |

## CONSISTENCY (silver)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_negeri_swasta | distinct_kecamatan(raw/norm/key) | 62/32/31 | ✅ PASS | key menyatukan variasi spasi & case |
| sby_sekolah_negeri_swasta | distinct_periode(raw/norm) | 24/12 | ✅ PASS | norm distandarkan ke <=12 bulan |
| sby_siswa_negeri_swasta | distinct_kecamatan(raw/norm/key) | 63/32/31 | ✅ PASS | key menyatukan variasi spasi & case |
| sby_siswa_negeri_swasta | distinct_periode(raw/norm) | 15/12 | ✅ PASS | norm distandarkan ke <=12 bulan |
| sby_sd_akreditasi_kecamatan | distinct_kecamatan(raw/norm/key) | 32/32/31 | ✅ PASS | key menyatukan variasi spasi & case |
| sby_sd_akreditasi_kecamatan | distinct_periode(raw/norm) | 12/12 | ✅ PASS | norm distandarkan ke <=12 bulan |
| sby_smp_akreditasi_kecamatan | distinct_kecamatan(raw/norm/key) | 32/32/31 | ✅ PASS | key menyatukan variasi spasi & case |
| sby_smp_akreditasi_kecamatan | distinct_periode(raw/norm) | 12/12 | ✅ PASS | norm distandarkan ke <=12 bulan |
| sby_sekolah_murid_guru_rasio | distinct_kecamatan(raw/norm/key) | 31/31/31 | ✅ PASS |  |
| sby_sekolah_murid_guru_rasio | distinct_periode(raw/norm) | 12/12 | ✅ PASS | norm distandarkan ke <=12 bulan |

## UNIQUENESS (silver)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_negeri_swasta | dup_on_grain(kec_key,periode,tahun) | 0 | ✅ PASS |  |
| sby_siswa_negeri_swasta | dup_on_grain(kec_key,periode,tahun) | 0 | ✅ PASS |  |
| sby_sd_akreditasi_kecamatan | dup_on_grain(kec_key,periode,tahun) | 0 | ✅ PASS |  |
| sby_smp_akreditasi_kecamatan | dup_on_grain(kec_key,periode,tahun) | 0 | ✅ PASS |  |
| sby_sekolah_murid_guru_rasio | dup_on_grain(kec_key,periode,tahun) | 0 | ✅ PASS |  |

## VALIDITY (silver)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| sby_sekolah_akreditasi | kapasitas_pagu_negatif | 0 | ✅ PASS |  |
| sby_sekolah_akreditasi | kapasitas_pagu_null | 58 (1.83%) | ⚠️ WARN |  |
| sby_sekolah_murid_guru_rasio | mts_rasio_dtype | string | ⚠️ WARN | tipe beda dgn sd/smp/mi_rasio (numeric) |

## JOINABILITY (silver)

| Tabel | Metrik | Nilai | Status | Catatan |
|---|---|---|---|---|
| penduduk x akreditasi | kecamatan_match(matched/total) | 31/31 | ✅ PASS |  |
