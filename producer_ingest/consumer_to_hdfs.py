import json
import time
import os
import subprocess
import threading
from datetime import datetime
from kafka import KafkaConsumer

# [Ni’mah Fauziyyah Atok]: Konfigurasi Pipeline
BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC_SBY_PENDUDUK = "sby-penduduk-usia"
TOPIC_SBY_SEKOLAH = "sby-sekolah-akreditasi"
TOPIC_SBY_SEKOLAH_NEGERI_SWASTA = "sby-sekolah-negeri-swasta"
TOPIC_SBY_SISWA_NEGERI_SWASTA = "sby-siswa-negeri-swasta"
TOPIC_SBY_SD_AKREDITASI_KECAMATAN = "sby-sd-akreditasi-kecamatan"
TOPIC_SBY_SMP_AKREDITASI_KECAMATAN = "sby-smp-akreditasi-kecamatan"
TOPIC_SBY_SEKOLAH_MURID_GURU_RASIO = "sby-sekolah-murid-guru-rasio"

HDFS_SBY_PENDUDUK_PATH = "/data/opendata-sby/penduduk-usia"
HDFS_SBY_SEKOLAH_PATH = "/data/opendata-sby/sekolah-akreditasi"
HDFS_SBY_SEKOLAH_NEGERI_SWASTA_PATH = "/data/opendata-sby/sekolah-negeri-swasta"
HDFS_SBY_SISWA_NEGERI_SWASTA_PATH = "/data/opendata-sby/siswa-negeri-swasta"
HDFS_SBY_SD_AKREDITASI_KECAMATAN_PATH = "/data/opendata-sby/sd-akreditasi-kecamatan"
HDFS_SBY_SMP_AKREDITASI_KECAMATAN_PATH = "/data/opendata-sby/smp-akreditasi-kecamatan"
HDFS_SBY_SEKOLAH_MURID_GURU_RASIO_PATH = "/data/opendata-sby/sekolah-murid-guru-rasio"
FLUSH_INTERVAL = 300

buffer_sby_penduduk = []
buffer_sby_sekolah = []
buffer_sby_sekolah_negeri_swasta = []
buffer_sby_siswa_negeri_swasta = []
buffer_sby_sd_akreditasi_kecamatan = []
buffer_sby_smp_akreditasi_kecamatan = []
buffer_sby_sekolah_murid_guru_rasio = []
lock_sby_penduduk = threading.Lock()
lock_sby_sekolah = threading.Lock()
lock_sby_sekolah_negeri_swasta = threading.Lock()
lock_sby_siswa_negeri_swasta = threading.Lock()
lock_sby_sd_akreditasi_kecamatan = threading.Lock()
lock_sby_smp_akreditasi_kecamatan = threading.Lock()
lock_sby_sekolah_murid_guru_rasio = threading.Lock()

def simpan_ke_hdfs(data, hdfs_path, label):
    """[Ni’mah Fauziyyah Atok]: Logika pemindahan data dari lokal ke HDFS via Docker"""
    if not data:
        return
    
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tmp_local = f"/tmp/opendata_{label}_{ts}.json"
    hdfs_dest = f"{hdfs_path}/{ts}.json"

    try:
        # 1. Tulis data ke file JSON lokal sementara
        with open(tmp_local, "w") as f:
            json.dump(data, f, ensure_ascii=False)

        # 2. Copy file dari MacBook ke dalam container hadoop-namenode
        subprocess.run(["docker", "cp", tmp_local, f"hadoop-namenode:{tmp_local}"], capture_output=True)

        # 3. Jalankan perintah HDFS put di dalam container
        result = subprocess.run(
            ["docker", "exec", "hadoop-namenode", "hdfs", "dfs", "-put", "-f", tmp_local, hdfs_dest],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"  [{label}] ✅ Berhasil simpan ke HDFS: {hdfs_dest} ({len(data)} event)")
        else:
            print(f"  [{label}] ❌ Gagal HDFS: {result.stderr.strip()}")

        # 4. Hapus file sampah di lokal dan di container
        os.remove(tmp_local)
        subprocess.run(["docker", "exec", "hadoop-namenode", "rm", tmp_local], capture_output=True)
        
    except Exception as e:
        print(f"  [{label}] ⚠️ Error proses HDFS: {e}")

def loop_consumer(topic, buffer, lock, hdfs_path, label):
    """[Ni’mah Fauziyyar Atok]: Thread untuk membaca Kafka dan mengisi buffer"""
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=f"group-{label}",
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=1000
    )
    
    print(f"[Consumer {label}] Dimulai...")
    last_flush = time.time()

    try:
        while True:
            for msg in consumer:
                with lock:
                    buffer.append(msg.value)
            
            # Cek apakah sudah waktunya flush ke HDFS
            if time.time() - last_flush >= FLUSH_INTERVAL:
                with lock:
                    data_copy = buffer.copy()
                    buffer.clear()
                
                if data_copy:
                    simpan_ke_hdfs(data_copy, hdfs_path, label)
                last_flush = time.time()
                
    except Exception as e:
        print(f"[Consumer {label}] Error: {e}")
    finally:
        consumer.close()

if __name__ == "__main__":
    t_sby_penduduk = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_PENDUDUK, buffer_sby_penduduk, lock_sby_penduduk, HDFS_SBY_PENDUDUK_PATH, "SBY-PENDUDUK"))
    t_sby_sekolah = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SEKOLAH, buffer_sby_sekolah, lock_sby_sekolah, HDFS_SBY_SEKOLAH_PATH, "SBY-SEKOLAH"))
    t_sby_sekolah_negeri_swasta = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SEKOLAH_NEGERI_SWASTA, buffer_sby_sekolah_negeri_swasta, lock_sby_sekolah_negeri_swasta, HDFS_SBY_SEKOLAH_NEGERI_SWASTA_PATH, "SBY-SEKOLAH-NEGERI-SWASTA"))
    t_sby_siswa_negeri_swasta = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SISWA_NEGERI_SWASTA, buffer_sby_siswa_negeri_swasta, lock_sby_siswa_negeri_swasta, HDFS_SBY_SISWA_NEGERI_SWASTA_PATH, "SBY-SISWA-NEGERI-SWASTA"))
    t_sby_sd_akreditasi_kecamatan = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SD_AKREDITASI_KECAMATAN, buffer_sby_sd_akreditasi_kecamatan, lock_sby_sd_akreditasi_kecamatan, HDFS_SBY_SD_AKREDITASI_KECAMATAN_PATH, "SBY-SD-AKREDITASI"))
    t_sby_smp_akreditasi_kecamatan = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SMP_AKREDITASI_KECAMATAN, buffer_sby_smp_akreditasi_kecamatan, lock_sby_smp_akreditasi_kecamatan, HDFS_SBY_SMP_AKREDITASI_KECAMATAN_PATH, "SBY-SMP-AKREDITASI"))
    t_sby_sekolah_murid_guru_rasio = threading.Thread(target=loop_consumer, args=(TOPIC_SBY_SEKOLAH_MURID_GURU_RASIO, buffer_sby_sekolah_murid_guru_rasio, lock_sby_sekolah_murid_guru_rasio, HDFS_SBY_SEKOLAH_MURID_GURU_RASIO_PATH, "SBY-SEKOLAH-MURID-GURU"))

    t_sby_penduduk.start()
    t_sby_sekolah.start()
    t_sby_sekolah_negeri_swasta.start()
    t_sby_siswa_negeri_swasta.start()
    t_sby_sd_akreditasi_kecamatan.start()
    t_sby_smp_akreditasi_kecamatan.start()
    t_sby_sekolah_murid_guru_rasio.start()

    t_sby_penduduk.join()
    t_sby_sekolah.join()
    t_sby_sekolah_negeri_swasta.join()
    t_sby_siswa_negeri_swasta.join()
    t_sby_sd_akreditasi_kecamatan.join()
    t_sby_smp_akreditasi_kecamatan.join()
    t_sby_sekolah_murid_guru_rasio.join()