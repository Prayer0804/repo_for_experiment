FROM flink:1.19.1-scala_2.12-java17

RUN set -eux; \
    wget -O /opt/flink/lib/flink-sql-connector-kafka-3.2.0-1.19.jar \
      https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar; \
    cp /opt/flink/opt/flink-json-*.jar /opt/flink/lib/ || true

COPY flink/sql/traffic_congestion.sql /opt/flink/usrlib/traffic_congestion.sql
