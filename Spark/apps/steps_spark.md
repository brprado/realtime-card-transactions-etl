**# Entrar no container master**
docker exec -it spark-master bash

**# Dentro do container, testar com PySpark shell**
pyspark

**# Ou executar um script Python**
python /path/to/test_spark.py

**# Ou usar spark-submit**

cd /opt/spark/apps/apps
ls

# Para scripts simples (sem Kafka)
spark-submit --master local[*] test_spark.py

## Para scripts com Kafka (bronze_ingestion.py) - Spark 3.5.3

# Opção 1: Usando JARs baixados manualmente (RECOMENDADO - mais confiável)
cd /tmp

# Baixar JARs necessários (apenas primeira vez)
wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar
wget https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar
wget https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# Executar com --jars (funcionando (limpe a pasta de checkpints antes))
cd /opt/spark/apps/apps
spark-submit --master local[*] \
  --jars /tmp/spark-sql-kafka-0-10_2.12-3.5.3.jar,/tmp/kafka-clients-3.5.0.jar,/tmp/spark-token-provider-kafka-0-10_2.12-3.5.3.jar,/tmp/commons-pool2-2.11.1.jar \
  bronze_ingestion.py

# Opção 2: Usando --packages (pode ter problemas de permissão com cache do Ivy)
# Se usar esta opção e der erro de permissão, use a Opção 1 acima
spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3 \
  bronze_ingestion.py

**# Ou usar o script submit.sh (já inclui os pacotes necessários)**
# Do host (fora do container):
cd Spark/apps
./submit.sh bronze_ingestion.py

## Limpar checkpoints (se necessário reiniciar o stream)
# Dentro do container:
rm -rf /opt/spark/data/checkpoints/bronze/*


