## Planejamento de Desenvolvimento - Pipeline de Transações Bancárias

Aqui está um planejamento completo estruturado em sprints de 2 semanas para você se nortear:

### Stack Tecnológica

- **Apache Kafka**: Message broker para ingestão de dados em tempo real
- **Apache Spark 3.5.3**: Processamento distribuído (Streaming e Batch)
- **Apache Airflow**: Orquestração e agendamento de pipelines
- **PostgreSQL**: Banco de dados para metadados do Airflow
- **MinIO**: Object Storage S3-compatible para armazenamento das camadas de dados
- **Delta Lake**: Formato de armazenamento transacional sobre Parquet para dados Bronze/Silver/Gold
- **Python**: Linguagem principal para desenvolvimento

### Dependências Necessárias para Jobs Spark

Todos os jobs Spark precisam incluir as seguintes dependências:

```bash
# Conector Kafka
org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3

# Delta Lake
io.delta:delta-spark_2.12:3.0.0

# Suporte S3/MinIO
org.apache.hadoop:hadoop-aws:3.3.4
com.amazonaws:aws-java-sdk-bundle:1.12.262
```

### Configurações Spark para MinIO e Delta Lake

Todos os jobs Spark devem incluir estas configurações:

```python
# Configurar acesso ao MinIO como S3
spark.conf.set("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
spark.conf.set("spark.hadoop.fs.s3a.access.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.secret.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
spark.conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# Habilitar Delta Lake
spark.conf.set("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
spark.conf.set("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
```

### Estrutura de Armazenamento no MinIO

- **Bucket `bronze`**: Dados brutos ingeridos do Kafka em formato Delta Lake
- **Bucket `silver`**: Dados limpos, validados e enriquecidos em formato Delta Lake
- **Bucket `gold`**: Agregações e métricas de negócio em formato Delta Lake

## Fase 1 Setup inicial

### Tarefas

- [X] Criar estrutura de pastas do projeto no VS Code
- [X] Configurar docker-compose.yml com Kafka, Spark, Airflow, PostgreSQL e MinIO
- [X] Testar subida de todos os containers (`docker-compose up`)
- [X] Documentar README inicial com objetivo do projeto
- [X] Configurar MinIO com buckets bronze, silver e gold
- [X] Configurar Spark para usar Delta Lake e MinIO (S3-compatible)

### Entregável

Ambiente Docker funcional com todos os serviços rodando localmente, incluindo MinIO configurado como object storage S3-compatible

---

## Fase 2: Geração de Dados (Sprint 1) - 2 semanas

### Objetivos

- Criar producer fake de transações bancárias
- Implementar ingestão no Kafka[4]

### Tarefas

- [X] Instalar biblioteca Faker: `pip install faker`
- [X] Criar schema de dados de transação:
  ```python
  {
    "transaction_id": "uuid",
    "account_id": "string",
    "transaction_type": "debit/credit/transfer",
    "amount": "float",
    "merchant": "string",
    "category": "string",
    "timestamp": "datetime",
    "location": {"lat": float, "lon": float},
    "device_id": "string"
  }
  ```
- [X] Desenvolver `kafka/producers/transaction_producer.py`[5]
- [X] Criar tópico Kafka: `transactions_raw`
- [X] Implementar lógica de geração com padrões normais e anomalias (3-5% de fraude)
- [X] Testar producer enviando 100-1000 transações/segundo
- [X] Criar consumer simples para validar dados no Kafka

### Entregável

Producer Python gerando transações fake e publicando no Kafka continuamente

---

## Fase 3: Camada Bronze - Raw Data (Sprint 2) - 2 semanas

### Objetivos

- Implementar ingestão Spark Streaming[6][4]
- Salvar dados brutos em formato Delta Lake no MinIO

### Tarefas

- [X] Criar job `spark/apps/bronze_ingestion.py`
- [X] Configurar Spark para ler do Kafka (usando porta 9093 para comunicação interna)
- [X] Parsear JSON e adicionar metadados (data de ingestão, source, kafka_timestamp)
- [X] Configurar checkpoint para fault tolerance[6]
- [X] Configurar Spark para usar Delta Lake e MinIO:
  ```python
  # Configurar acesso ao MinIO como S3
  spark.conf.set("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
  spark.conf.set("spark.hadoop.fs.s3a.access.key", "minioadmin")
  spark.conf.set("spark.hadoop.fs.s3a.secret.key", "minioadmin")
  spark.conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
  spark.conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

  # Habilitar Delta Lake
  spark.conf.set("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
  spark.conf.set("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
  ```
- [X] Adicionar dependências Delta Lake ao spark-submit:
  ```bash
  --packages io.delta:delta-spark_2.12:3.0.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262
  ```
- [X] Salvar em `s3a://bronze/transactions/` como Delta Lake
- [X] Implementar particionamento por categoria (ou data: year/month/day)
- [X] Testar recuperação de falhas (simular crash do Spark)
- [X] Verificar dados no MinIO Console (http://localhost:9001)

### Entregável

Pipeline Bronze salvando dados brutos em Delta Lake no MinIO (bucket bronze) com checkpoint funcional

---

## Fase 4: Camada Silver - Limpeza e Enriquecimento (Sprint 3) - 2 semanas

### Objetivos

- Implementar transformações e validações[7][4]
- Criar features para detecção de fraude
- Processar dados Bronze do MinIO e salvar em Silver (Delta Lake)

### Tarefas

- [ ] Criar job `spark/apps/silver_transformation.py`
- [ ] Configurar Spark para acessar MinIO e Delta Lake (mesmas configurações da Fase 3)
- [ ] Ler dados Bronze do MinIO: `spark.read.format("delta").load("s3a://bronze/transactions")`
- [ ] Implementar validações:
  - Remover duplicatas por transaction_id usando Delta Lake MERGE
  - Validar valores positivos para amount
  - Filtrar transações com campos obrigatórios nulos
- [ ] Adicionar features temporais:
  - Hour of day, day of week
  - Diferença de tempo desde última transação da conta
  - Velocidade de transações (count últimas 24h por account_id)
- [ ] Enriquecer com dados dimensionais:
  - Categoria de merchant (criar tabela fake de merchants)
  - Histórico de comportamento do account (média, mediana de valores)
- [ ] Implementar detecção de anomalias simples:[6]
  - Transações > 3x desvio padrão do histórico
  - Múltiplas transações em localizações distantes (<30 min)
- [ ] Salvar em `s3a://silver/transactions_cleaned/` como Delta Lake
- [ ] Usar Delta Lake MERGE para upserts (evitar duplicatas)
- [ ] Implementar particionamento adequado (por categoria ou data)

### Entregável

Pipeline Silver com dados limpos, validados e enriquecidos com features, armazenados em Delta Lake no MinIO (bucket silver)

---

## Fase 5: Camada Gold - Agregações e Analytics (Sprint 4) - 2 semanas

### Objetivos

- Criar tabelas agregadas para análise[4]
- Implementar métricas de negócio
- Processar dados Silver do MinIO e gerar agregações em Gold (Delta Lake)

### Tarefas

- [ ] Criar job `spark/apps/gold_aggregations.py`
- [ ] Configurar Spark para acessar MinIO e Delta Lake
- [ ] Ler dados Silver do MinIO: `spark.read.format("delta").load("s3a://silver/transactions_cleaned")`
- [ ] Implementar agregações por janela de tempo:
  - Volume de transações por hora/dia
  - Valor médio de transações por categoria
  - Taxa de fraude detectada (%)
  - Top 10 merchants por volume
- [ ] Criar tabelas dimensionais no MinIO (bucket gold):
  - `s3a://gold/daily_summary/` - métricas diárias consolidadas (Delta Lake)
  - `s3a://gold/fraud_cases/` - transações suspeitas para investigação (Delta Lake)
  - `s3a://gold/account_profile/` - perfil de comportamento por conta (Delta Lake)
- [ ] Implementar SCD Type 2 para histórico de perfis de conta usando Delta Lake
- [ ] Adicionar data quality checks:[7]
  - Validar completude dos dados (% campos preenchidos)
  - Verificar consistência de valores agregados
- [ ] Usar Delta Lake para garantir ACID transactions nas agregações
- [ ] Implementar particionamento adequado para cada tabela Gold

### Entregável

Camadas Gold com métricas de negócio prontas para consumo, armazenadas em Delta Lake no MinIO (bucket gold)

---

## Fase 6: Orquestração com Airflow (Sprint 5) - 2 semanas

### Objetivos

- Automatizar pipeline end-to-end[3][8]
- Implementar scheduling e monitoramento
- Orquestrar jobs Spark que processam dados do MinIO

### Tarefas

- [ ] Criar DAG `airflow/dags/banking_pipeline_dag.py`
- [ ] Implementar tasks:
  ```python
  start_producer >> check_kafka_topic >> 
  spark_bronze_job >> spark_silver_job >> 
  spark_gold_job >> data_quality_check >> 
  send_notification
  ```
- [ ] Configurar `PythonOperator` para iniciar producer (run por 5 min)
- [ ] Configurar `SparkSubmitOperator` para jobs Spark[9] com dependências:
  - Delta Lake: `io.delta:delta-spark_2.12:3.0.0`
  - Hadoop AWS: `org.apache.hadoop:hadoop-aws:3.3.4`
  - AWS SDK: `com.amazonaws:aws-java-sdk-bundle:1.12.262`
  - Kafka connector: `org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3`
- [ ] Configurar variáveis de ambiente do Spark para MinIO em cada task
- [ ] Adicionar `BranchOperator` para executar somente se há novos dados no MinIO
- [ ] Implementar alertas via email para falhas
- [ ] Configurar schedule: executar a cada 1 hora
- [ ] Criar testes de DAG (`tests/test_dags.py`)
- [ ] Documentar cada task no DAG
- [ ] Adicionar tasks de verificação de dados no MinIO (validar buckets bronze/silver/gold)

### Entregável

Pipeline completo orquestrado pelo Airflow rodando automaticamente, processando dados do MinIO e salvando em Delta Lake

---

## Fase 7: Monitoramento e Qualidade (Sprint 6) - 1 semana

### Objetivos

- Implementar observabilidade[10]
- Garantir data quality[7]
- Monitorar dados armazenados no MinIO

### Tarefas

- [ ] Adicionar logs estruturados em cada job Spark
- [ ] Criar métricas customizadas no Airflow:
  - Tempo de processamento por layer
  - Volume de dados processados (verificar no MinIO)
  - Taxa de falha de validações
  - Tamanho dos buckets bronze/silver/gold no MinIO
- [ ] Implementar Great Expectations para data quality
- [ ] Criar dashboard simples com Streamlit:
  - Visualizar métricas da camada Gold (ler do MinIO)
  - Gráfico de transações por hora
  - Alertas de fraude detectadas
  - Status dos buckets no MinIO
- [ ] Documentar arquitetura com diagrama (draw.io ou Mermaid)
- [ ] Adicionar monitoramento do Delta Lake (time travel, versões)
- [ ] Criar alertas para crescimento excessivo dos buckets no MinIO

### Entregável

Sistema de monitoramento e dashboard funcional, incluindo métricas dos dados armazenados no MinIO

---

## Fluxo de Dados Completo

```
┌─────────────────┐
│ Faker Producer  │ Gera transações fake
│   (Python)      │ 100-1000 trans/sec
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka Topic    │ Buffer de mensagens
│ transactions_raw│ Retenção: 7 dias
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ BRONZE Layer    │ Raw data (Delta Lake)
│ Spark Streaming │ MinIO: s3a://bronze/
│                 │ Particionado por categoria/data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SILVER Layer    │ Limpeza + Features
│  Spark Batch    │ MinIO: s3a://silver/
│                 │ Detecção de anomalias
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GOLD Layer     │ Agregações de negócio
│  Spark Batch    │ MinIO: s3a://gold/
│                 │ Métricas e KPIs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dashboard/API   │ Consumo final
│   (Streamlit)   │ Visualizações
└─────────────────┘

    ↑ Orquestrado por Airflow DAG ↑
```

---

## Estimativas de Tempo Total

- Sprint 0 (Setup): 1 semana
- Sprint 1 (Producer): 2 semanas
- Sprint 2 (Bronze): 2 semanas
- Sprint 3 (Silver): 2 semanas
- Sprint 4 (Gold): 2 semanas
- Sprint 5 (Airflow): 2 semanas
- Sprint 6 (Monitoring): 1 semana
