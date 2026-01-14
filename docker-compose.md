~~~~

# Documentação do Docker Compose - Pipeline de Dados em Tempo Real

Esta stack configura um ambiente completo de processamento de dados em tempo real usando arquitetura de Data Lakehouse com camadas Bronze, Silver e Gold.

## Arquitetura Geral

O ambiente integra orquestração (Airflow), processamento distribuído (Spark), streaming (Kafka), e armazenamento em camadas (MinIO) para construir pipelines de dados modernos.

## Componentes

## PostgreSQL

Banco de dados relacional que armazena os metadados do Airflow (histórico de execuções, configurações de DAGs, usuários e permissões).

* **Porta:** 5432
* **Credenciais:** airflow/airflow
* **Volume:** Persistência dos dados em `postgres_data`
* **Healthcheck:** Verifica disponibilidade do banco a cada 10 segundos

## Zookeeper

Serviço de coordenação distribuída necessário para o funcionamento do Kafka. Gerencia metadados do cluster, eleição de líderes e sincronização entre brokers.

* **Porta:** 2181
* **Configuração:** Client port padrão com tick time de 2 segundos

## Kafka

Message broker para streaming de eventos em tempo real. Permite ingestão e processamento de dados com alta throughput e baixa latência.

* **Portas:** 9092 (external), 9093 (internal)
* **Retenção:** 7 dias de histórico de mensagens
* **Configuração:** Single broker com auto-criação de tópicos habilitada
* **Listeners:** PLAINTEXT para comunicação interna e externa

## Kafka UI

Interface web para gerenciamento e monitoramento do Kafka. Visualiza tópicos, mensagens, consumers e métricas do cluster.

* **Porta:** 8080
* **Acesso:** [**http://localhost:8080**](http://localhost:8080/)

## MinIO

Object storage compatível com S3 que implementa a arquitetura de Data Lakehouse em três camadas:

* **Bronze:** Dados brutos (raw) sem transformação
* **Silver:** Dados limpos e validados
* **Gold:** Dados agregados prontos para análise

**Portas:**

* 9000: API S3-compatible
* 9001: Console web de gerenciamento

**Credenciais:** minioadmin/minioadmin

## MinIO Setup

Container auxiliar que inicializa os buckets automaticamente na primeira execução. Cria as três camadas (bronze, silver, gold) usando o MinIO Client (mc).

## Spark Master

Nó coordenador do cluster Spark. Gerencia recursos, distribui tarefas e monitora workers.

* **Porta UI:** 8081
* **Porta Master:** 7077
* **Volumes:**
  * `./Spark`: Scripts de processamento
  * `./Data`: Datasets
  * `spark_ivy_cache`: Cache de dependências Maven/Ivy
* **Configuração S3:** Credenciais MinIO configuradas para leitura/escrita nas camadas

## Spark Worker

Nó de processamento que executa as tarefas distribuídas pelo Master.

* **Porta UI:** 8082
* **Recursos:** 2 cores e 2GB de memória
* **Dependências:** Aguarda inicialização do Master e MinIO
* **Healthcheck:** Monitora disponibilidade do worker a cada 30 segundos

## Airflow Webserver

Interface web para gerenciamento de workflows (DAGs). Permite monitorar execuções, visualizar logs e configurar pipelines.

* **Porta:** 8083
* **Credenciais padrão:** admin/admin
* **Volumes compartilhados:** DAGs, logs, plugins, scripts Spark e dados

## Airflow Scheduler

Componente que executa as tarefas agendadas nos DAGs. Monitora triggers, gerencia dependências e dispara execuções.

* **Executor:** LocalExecutor (execução local sem Celery)
* **Dependências:** Requer Webserver e PostgreSQL saudáveis

## Airflow Init

Container de inicialização executado uma única vez. Cria o schema do banco de dados e o usuário admin padrão.

**Credenciais criadas:**

* Username: admin
* Password: admin
* Role: Admin

## Volumes Persistentes

* **postgres_data:** Metadados do Airflow
* **minio_data:** Dados das camadas Bronze/Silver/Gold
* **spark_ivy_cache:** Dependências Java/Scala do Spark

## Rede

Todos os serviços compartilham a rede `etl-network` (bridge) para comunicação interna isolada.

## Healthchecks

Os containers possuem verificações de saúde que garantem inicialização ordenada:

* PostgreSQL: Comando `pg_isready`
* Kafka: Validação do broker API
* MinIO: Endpoint de health check HTTP
* Spark Master/Worker: Verificação da UI web
* Airflow Webserver: Endpoint `/health`

## Fluxo de Dados Típico

1. **Ingestão:** Dados chegam via Kafka em tempo real
2. **Bronze:** Spark consome Kafka e grava raw data no MinIO
3. **Silver:** Jobs Spark limpam e validam dados
4. **Gold:** Agregações e métricas são computadas
5. **Orquestração:** Airflow agenda e monitora todo o pipeline

## Portas de Acesso

* 5432: PostgreSQL
* 2181: Zookeeper
* 8080: Kafka UI
* 8081: Spark Master UI
* 8082: Spark Worker UI
* 8083: Airflow Webserver
* 9000: MinIO API
* 9001: MinIO Console
* 9092/9093: Kafka

---
