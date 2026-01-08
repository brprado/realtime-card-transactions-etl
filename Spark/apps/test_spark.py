from pyspark.sql import SparkSession

# Criar SparkSession
spark = SparkSession.builder \
    .appName("TestSpark") \
    .master("local[*]") \
    .getOrCreate()

# Verificar versão
print(f"Spark Version: {spark.version}")

# Teste simples: criar DataFrame
data = [("Alice", 34), ("Bob", 45), ("Cathy", 29)]
columns = ["Name", "Age"]
df = spark.createDataFrame(data, columns)

# Mostrar dados
df.show()

# Teste de operação
df.filter(df.Age > 30).show()

# Contar registros
count = df.count()
print(f"Total de registros: {count}")

# Parar SparkSession
spark.stop()
print("✅ Spark está funcionando!")
