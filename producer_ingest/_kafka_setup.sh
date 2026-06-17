#!/bin/bash

# Weather topics
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic weather-api --partitions 6 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic weather-rss --partitions 6 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092

# Open Data Surabaya topics
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-penduduk-usia --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-sekolah-akreditasi --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-sekolah-negeri-swasta --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-siswa-negeri-swasta --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-sd-akreditasi-kecamatan --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-smp-akreditasi-kecamatan --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --create --topic sby-sekolah-murid-guru-rasio --partitions 3 --replication-factor 1 --config retention.ms=86400000 --bootstrap-server localhost:9092

# List all topics
docker exec -it kafka-broker /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
