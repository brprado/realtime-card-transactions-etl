from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, lit
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    TimestampType, MapType, BooleanType
)
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Criar SparkSession com configurações para Kafka
spark = SparkSession.builder \
    .appName("BronzeIngestion") \
    .config("spark.sql.streaming.checkpointLocation", "/opt/spark/data/checkpoints/bronze") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Definir schema das transações
transaction_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("account_id", StringType(), True),
    StructField("transaction_type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("merchant", StringType(), True),
    StructField("category", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("location", MapType(StringType(), DoubleType()), True),
    StructField("device_id", StringType(), True),
    StructField("is_fraud", BooleanType(), True)
])

# Ler stream do Kafka (usar porta 9093 para comunicação interna entre containers)
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9093") \
    .option("subscribe", "transactions_raw") \
    .option("startingOffsets", "latest") \
    .load()

############################################################################ 
# Lê apenas mensagens novas (recomendado para produção em tempo real)
# .option("startingOffsets", "latest")

# # Lê todas as mensagens desde o início (útil para backfill)
# .option("startingOffsets", "earliest")
############################################################################

# Parsear JSON e adicionar metadados
parsed_df = df.select(
    from_json(col("value").cast("string"), transaction_schema).alias("data"),
    col("timestamp").alias("kafka_timestamp"),
    current_timestamp().alias("ingestion_timestamp")
).select(
    "data.*",
    "kafka_timestamp",
    "ingestion_timestamp",
    lit("kafka").alias("source")
)

# parsed_df = spark.sql("""
#     SELECT 
#         get_json_object(CAST(value AS STRING), '$.transaction_id') AS transaction_id,
#         get_json_object(CAST(value AS STRING), '$.account_id') AS account_id,
#         get_json_object(CAST(value AS STRING), '$.transaction_type') AS transaction_type,
#         CAST(get_json_object(CAST(value AS STRING), '$.amount') AS DOUBLE) AS amount,
#         get_json_object(CAST(value AS STRING), '$.merchant') AS merchant,
#         get_json_object(CAST(value AS STRING), '$.category') AS category,
#         get_json_object(CAST(value AS STRING), '$.timestamp') AS timestamp,
#         get_json_object(CAST(value AS STRING), '$.location') AS location,
#         get_json_object(CAST(value AS STRING), '$.device_id') AS device_id,
#         CAST(get_json_object(CAST(value AS STRING), '$.is_fraud') AS BOOLEAN) AS is_fraud,
#         timestamp AS kafka_timestamp,
#         current_timestamp() AS ingestion_timestamp,
#         'kafka' AS source
#     FROM kafka_stream
# """)

# Escrever stream para Bronze (Parquet)
query = parsed_df.writeStream \
    .format("parquet") \
    .outputMode("append") \
    .option("checkpointLocation", "/opt/spark/data/checkpoints/bronze") \
    .option("path", "/opt/spark/data/bronze/transactions") \
    .partitionBy("category") \
    .trigger(processingTime="10 seconds") \
    .start()

print("✅ Bronze ingestion iniciado!")
print("📊 Processando transações do Kafka...")

# Aguardar término do stream
query.awaitTermination()