docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic weather-api \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic weather-rss \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-penduduk-usia \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-sekolah-akreditasi \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-sekolah-negeri-swasta \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-siswa-negeri-swasta \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-sd-akreditasi-kecamatan \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-smp-akreditasi-kecamatan \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092

docker exec -it kafka-broker /opt/kafka/bin/kafka-console-consumer.sh \
  --topic sby-sekolah-murid-guru-rasio \
  --from-beginning \
  --max-messages 5 \
  --bootstrap-server localhost:9092
