## Planejamento de Desenvolvimento - Pipeline de Transações Bancárias

Aqui está um planejamento completo estruturado em sprints de 2 semanas para você se nortear:

## Fase 1 Setup inicial

### Tarefas

- [X] Criar estrutura de pastas do projeto no VS Code
- [X] Configurar docker-compose.yml com Kafka, Spark, Airflow e PostgreSQL
- [X] Testar subida de todos os containers (`docker-compose up`)
- [X] Documentar README inicial com objetivo do projeto

### Entregável

Ambiente Docker funcional com todos os serviços rodando localmente

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
- [ ] Testar producer enviando 100-1000 transações/segundo
- [ ] Criar consumer simples para validar dados no Kafka

### Entregável

Producer Python gerando transações fake e publicando no Kafka continuamente

---

## Fase 3: Camada Bronze - Raw Data (Sprint 2) - 2 semanas

### Objetivos

- Implementar ingestão Spark Streaming[6][4]
- Salvar dados brutos em formato Delta/Parquet

### Tarefas

- [ ] Criar job `spark/apps/bronze_ingestion.py`
- [ ] Configurar Spark para ler do Kafka:
  ```python
  df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "transactions_raw") \
    .load()
  ```
- [ ] Parsear JSON e adicionar metadados (data de ingestão, source)
- [ ] Configurar checkpoint para fault tolerance[6]
- [ ] Salvar em `data/bronze/transactions/` como Delta Lake
- [ ] Implementar particionamento por data (year/month/day)
- [ ] Testar recuperação de falhas (simular crash do Spark)

### Entregável

Pipeline Bronze salvando dados brutos em Delta com checkpoint funcional

---

## Fase 4: Camada Silver - Limpeza e Enriquecimento (Sprint 3) - 2 semanas

### Objetivos

- Implementar transformações e validações[7][4]
- Criar features para detecção de fraude

### Tarefas

- [ ] Criar job `spark/apps/silver_transformation.py`
- [ ] Implementar validações:
  - Remover duplicatas por transaction_id
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
- [ ] Salvar em `data/silver/transactions_cleaned/`

### Entregável

Pipeline Silver com dados limpos, validados e enriquecidos com features

---

## Fase 5: Camada Gold - Agregações e Analytics (Sprint 4) - 2 semanas

### Objetivos

- Criar tabelas agregadas para análise[4]
- Implementar métricas de negócio

### Tarefas

- [ ] Criar job `spark/apps/gold_aggregations.py`
- [ ] Implementar agregações por janela de tempo:
  - Volume de transações por hora/dia
  - Valor médio de transações por categoria
  - Taxa de fraude detectada (%)
  - Top 10 merchants por volume
- [ ] Criar tabelas dimensionais:
  - `gold/daily_summary/` - métricas diárias consolidadas
  - `gold/fraud_cases/` - transações suspeitas para investigação
  - `gold/account_profile/` - perfil de comportamento por conta
- [ ] Implementar SCD Type 2 para histórico de perfis de conta
- [ ] Adicionar data quality checks:[7]
  - Validar completude dos dados (% campos preenchidos)
  - Verificar consistência de valores agregados

### Entregável

Camadas Gold com métricas de negócio prontas para consumo

---

## Fase 6: Orquestração com Airflow (Sprint 5) - 2 semanas

### Objetivos

- Automatizar pipeline end-to-end[3][8]
- Implementar scheduling e monitoramento

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
- [ ] Configurar `SparkSubmitOperator` para jobs Spark[9]
- [ ] Adicionar `BranchOperator` para executar somente se há novos dados
- [ ] Implementar alertas via email para falhas
- [ ] Configurar schedule: executar a cada 1 hora
- [ ] Criar testes de DAG (`tests/test_dags.py`)
- [ ] Documentar cada task no DAG

### Entregável

Pipeline completo orquestrado pelo Airflow rodando automaticamente

---

## Fase 7: Monitoramento e Qualidade (Sprint 6) - 1 semana

### Objetivos

- Implementar observabilidade[10]
- Garantir data quality[7]

### Tarefas

- [ ] Adicionar logs estruturados em cada job Spark
- [ ] Criar métricas customizadas no Airflow:
  - Tempo de processamento por layer
  - Volume de dados processados
  - Taxa de falha de validações
- [ ] Implementar Great Expectations para data quality
- [ ] Criar dashboard simples com Streamlit:
  - Visualizar métricas da camada Gold
  - Gráfico de transações por hora
  - Alertas de fraude detectadas
- [ ] Documentar arquitetura com diagrama (draw.io ou Mermaid)

### Entregável

Sistema de monitoramento e dashboard funcional

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
│ BRONZE Layer    │ Raw data (Delta)
│ Spark Streaming │ Particionado por data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SILVER Layer    │ Limpeza + Features
│  Spark Batch    │ Detecção de anomalias
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GOLD Layer     │ Agregações de negócio
│  Spark Batch    │ Métricas e KPIs
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
