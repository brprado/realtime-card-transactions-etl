# Pipeline de Transações Bancárias - Real-time Processing ETL

## 📋 Objetivo do Projeto

Este projeto implementa um pipeline ETL completo para processamento em tempo real de transações bancárias, utilizando uma arquitetura moderna baseada em **Medallion Architecture** (Bronze, Silver, Gold). O sistema é capaz de:

- **Ingestão em tempo real**: Captura de transações bancárias via Kafka
- **Processamento distribuído**: Transformações usando Apache Spark (Streaming e Batch)
- **Orquestração**: Automação e agendamento com Apache Airflow
- **Detecção de fraude**: Identificação de anomalias e padrões suspeitos
- **Analytics**: Agregações e métricas de negócio para análise

## 🏗️ Arquitetura

O pipeline segue o padrão Medallion Architecture:

```
Producer (Faker) → Kafka → Bronze (Raw) → Silver (Cleaned) → Gold (Aggregated)
                                                                    ↓
                                                              Dashboard/API
```

### Camadas de Dados

- **Bronze**: Dados brutos ingeridos do Kafka, armazenados em formato Delta Lake no MinIO (bucket `bronze`)
- **Silver**: Dados limpos, validados e enriquecidos com features para detecção de fraude, armazenados em Delta Lake no MinIO (bucket `silver`)
- **Gold**: Agregações de negócio, métricas e KPIs prontos para consumo, armazenados em Delta Lake no MinIO (bucket `gold`)

### Armazenamento

O projeto utiliza **MinIO** como camada de armazenamento object storage (S3-compatible) e **Delta Lake** como formato de dados:

- **MinIO**: Fornece armazenamento distribuído compatível com S3, ideal para data lakes
- **Delta Lake**: Formato transacional sobre Parquet que oferece:
  - ACID transactions
  - Time travel (versionamento de dados)
  - Schema evolution
  - Upserts e deletes eficientes
  - Auditoria completa de mudanças

## 🛠️ Stack Tecnológica

- **Apache Kafka**: Message broker para ingestão de dados em tempo real
- **Apache Spark**: Processamento distribuído (Streaming e Batch)
- **Apache Airflow**: Orquestração e agendamento de pipelines
- **PostgreSQL**: Banco de dados para metadados do Airflow
- **MinIO**: Object Storage S3-compatible para armazenamento das camadas de dados
- **Delta Lake**: Formato de armazenamento transacional sobre Parquet para dados Bronze/Silver/Gold
- **Python**: Linguagem principal para desenvolvimento

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Mínimo 8GB de RAM disponível
- Portas disponíveis: 5432, 8080, 8081, 8082, 8083, 9000, 9001, 9092, 2181

### Iniciar o Ambiente

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar status dos containers
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f kafka
docker-compose logs -f spark-master
docker-compose logs -f airflow-webserver
```

### Acessar as Interfaces

O ambiente fornece várias interfaces web para monitoramento e gerenciamento dos serviços:

#### 1. Kafka UI
- **URL**: http://localhost:8080
- **Descrição**: Interface web para gerenciar e monitorar o Apache Kafka
- **Funcionalidades**:
  - Visualizar tópicos, mensagens e consumidores
  - Criar e gerenciar tópicos
  - Inspecionar mensagens em tempo real
  - Ver métricas de throughput e latência
  - Gerenciar consumer groups
- **Uso**: Útil para verificar se as transações estão sendo publicadas no tópico `transactions_raw` e monitorar o fluxo de dados

#### 2. Spark Master UI
- **URL**: http://localhost:8081
- **Descrição**: Interface web do Apache Spark Master para monitorar o cluster
- **Funcionalidades**:
  - Visualizar status do cluster Spark
  - Ver workers registrados e seus recursos (CPU, memória)
  - Monitorar aplicações Spark em execução
  - Ver histórico de jobs completados
  - Acessar logs de execução
  - Ver métricas de performance
- **Uso**: Essencial para monitorar os jobs Spark (Bronze, Silver, Gold) e verificar o uso de recursos do cluster

#### 3. Spark Worker UI
- **URL**: http://localhost:8082
- **Descrição**: Interface web do Apache Spark Worker para monitorar um nó individual
- **Funcionalidades**:
  - Ver recursos disponíveis do worker (cores, memória)
  - Monitorar executors em execução
  - Visualizar logs do worker
  - Ver aplicações alocadas neste worker
- **Uso**: Útil para debug e monitoramento detalhado de um worker específico do cluster

#### 4. MinIO Console
- **URL**: http://localhost:9001
- **Credenciais**:
  - Usuário: `minioadmin`
  - Senha: `minioadmin`
- **Descrição**: Interface web do MinIO para gerenciar buckets e objetos armazenados
- **Funcionalidades**:
  - Visualizar e gerenciar buckets (bronze, silver, gold)
  - Navegar pelos objetos armazenados
  - Upload/download de arquivos
  - Configurar políticas de acesso
  - Ver métricas de uso de armazenamento
  - Criar e gerenciar usuários e políticas
- **Uso**: Essencial para verificar os dados armazenados nas camadas Bronze, Silver e Gold, e gerenciar o armazenamento

#### 5. Airflow UI
- **URL**: http://localhost:8083
- **Credenciais**:
  - Usuário: `admin`
  - Senha: `admin`
- **Descrição**: Interface web do Apache Airflow para orquestração e monitoramento de pipelines
- **Funcionalidades**:
  - Visualizar e gerenciar DAGs (Directed Acyclic Graphs)
  - Monitorar execuções de tarefas em tempo real
  - Ver histórico de execuções e logs
  - Trigger manual de DAGs
  - Configurar schedules e dependências
  - Visualizar grafos de dependência entre tarefas
  - Acessar logs detalhados de cada task
- **Uso**: Interface principal para orquestrar todo o pipeline ETL, desde a geração de dados até as agregações finais

### Parar o Ambiente

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpar dados)
docker-compose down -v
```

## 📁 Estrutura do Projeto

```
realtime-processing-etl/
├── Airflow/
│   ├── dags/          # DAGs do Airflow
│   ├── logs/          # Logs de execução
│   └── plugins/       # Plugins customizados
├── Kafka/
│   └── producers/     # Producers Python para gerar dados
├── Spark/
│   └── apps/          # Jobs Spark (Bronze, Silver, Gold)
├── Data/
│   ├── Bronze/        # Dados brutos
│   ├── Silver/        # Dados limpos e enriquecidos
│   └── Gold/          # Agregações e métricas
├── docker-compose.yml # Configuração dos serviços
└── README.md          # Este arquivo
```

## 📊 Fluxo de Dados

1. **Geração**: Producer Python gera transações fake (100-1000 transações/segundo)
2. **Ingestão**: Transações são publicadas no tópico Kafka `transactions_raw`
3. **Bronze**: Spark Streaming lê do Kafka e salva dados brutos em formato Delta Lake no MinIO (bucket `bronze`)
4. **Silver**: Spark Batch processa dados Bronze do MinIO, aplica validações e cria features, salvando em Delta Lake no MinIO (bucket `silver`)
5. **Gold**: Spark Batch agrega dados Silver do MinIO em métricas de negócio, salvando em Delta Lake no MinIO (bucket `gold`)
6. **Orquestração**: Airflow coordena todo o pipeline de forma automatizada
7. **Armazenamento**: Todas as camadas (Bronze, Silver, Gold) são armazenadas no MinIO usando Delta Lake para garantir ACID transactions e versionamento

## 🔄 Próximos Passos

Consulte o arquivo `plan.md` para ver o planejamento completo de desenvolvimento em sprints.

## 📝 Notas

- Este é um projeto de demonstração/portfólio
- Os dados gerados são fictícios usando a biblioteca Faker
- O ambiente está configurado para desenvolvimento local

## 🔍 Monitoramento e Verificação

### Verificando o Spark

Após iniciar os serviços, você pode verificar se o Spark está funcionando corretamente:

1. **Acessar a UI do Spark Master**: http://localhost:8081
   - Você deve ver o status do cluster e os workers registrados
   - Verifique se o worker aparece na lista de workers ativos

2. **Acessar a UI do Spark Worker**: http://localhost:8082
   - Mostra informações sobre o worker individual
   - Confirme que está conectado ao Master

3. **Verificar logs**:
   ```bash
   docker-compose logs spark-master
   docker-compose logs spark-worker
   ```

4. **Verificar status dos containers**:
   ```bash
   docker-compose ps spark-master spark-worker
   ```

O Spark Master e Worker devem estar com status "healthy" e o Worker deve aparecer registrado no Master.

### Quando Usar Cada Interface

- **Kafka UI**: Use para verificar se os dados estão sendo produzidos e consumidos corretamente, especialmente durante a Fase 2 (Geração de Dados)
- **Spark Master UI**: Use para monitorar jobs Spark em execução e verificar o status do cluster durante as Fases 3, 4 e 5 (Bronze, Silver, Gold)
- **Spark Worker UI**: Use para debug detalhado de problemas em um worker específico
- **MinIO Console**: Use para verificar os dados armazenados nas camadas Bronze, Silver e Gold, navegar pelos buckets e verificar o uso de armazenamento
- **Airflow UI**: Use para orquestrar todo o pipeline, visualizar dependências entre tarefas e monitorar execuções agendadas (Fase 6)

## 💾 Configuração do MinIO e Delta Lake

### Acessando o MinIO via S3 API

O MinIO está configurado como um serviço S3-compatible. Para acessar via código Spark:

```python
# Configuração para acessar MinIO como S3
spark.conf.set("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
spark.conf.set("spark.hadoop.fs.s3a.access.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.secret.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
spark.conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
```

### Buckets Disponíveis

- **bronze**: Armazena dados brutos ingeridos do Kafka em formato Delta Lake
- **silver**: Armazena dados limpos e enriquecidos em formato Delta Lake
- **gold**: Armazena agregações e métricas de negócio em formato Delta Lake

### Delta Lake

O projeto utiliza Delta Lake para todas as camadas de dados, oferecendo:

- **ACID Transactions**: Garantia de consistência dos dados
- **Time Travel**: Acesso a versões históricas dos dados
- **Schema Evolution**: Evolução automática do schema sem quebrar pipelines
- **Upserts e Deletes**: Operações eficientes de atualização e exclusão
- **Auditoria**: Histórico completo de todas as mudanças

### Exemplo de Uso no Spark

```python
# Configurar acesso ao MinIO como S3
spark.conf.set("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
spark.conf.set("spark.hadoop.fs.s3a.access.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.secret.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
spark.conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# Ler dados Delta do MinIO
df = spark.read.format("delta").load("s3a://bronze/transactions")

# Escrever dados Delta no MinIO
df.write.format("delta").mode("overwrite").save("s3a://silver/transactions_cleaned")
```

### Dependências Necessárias

Para usar Delta Lake com Spark, é necessário incluir as seguintes bibliotecas ao submeter jobs:

- `io.delta:delta-spark_2.12:3.0.0` (ou versão compatível com Spark 3.5.0)
- `org.apache.hadoop:hadoop-aws:3.3.4` (para suporte S3/MinIO)
- `com.amazonaws:aws-java-sdk-bundle:1.12.262` (para S3A filesystem)

Exemplo de submissão:
```bash
spark-submit \
  --packages io.delta:delta-spark_2.12:3.0.0,org.apache.hadoop:hadoop-aws:3.3.4 \
  --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
  --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
  your_job.py
```

