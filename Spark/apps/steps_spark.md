**# Entrar no container master**
**docker**exec -it spark-master **bash**

**# Dentro do container, testar com PySpark shell**
pyspark

**# Ou executar um script Python**
python /path/to/test_spark.py

**# Ou usar spark-submit**

cd /opt/spark/apps/apps
ls
spark-submit --master local[*] test_spark.py
