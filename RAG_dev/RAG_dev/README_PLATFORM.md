# RAG Platform - Sistema de Análisis Inteligente de Documentos

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Plataforma web profesional construida con Django y Tailwind CSS para análisis de documentos PDF/TXT utilizando técnicas avanzadas de RAG (Retrieval-Augmented Generation) con **OpenAI GPT-4o**, **FAISS** y **Neo4j GraphRAG**.

## 🎯 Características Principales

- **Doble Motor RAG**: Selección entre búsqueda semántica (FAISS) y relacional (Neo4j GraphRAG)
- **Procesamiento Inteligente**: Extracción automática de metadata, chunking optimizado y generación de embeddings
- **Chat Interactivo**: Interfaz de conversación con historial persistente y streaming de respuestas
- **Gestión de Documentos**: Subida, inspección de chunks y visualización de metadata
- **Autenticación Completa**: Sistema de usuarios con perfiles personalizados
- **Diseño Profesional**: UI moderna con Tailwind CSS responsive

## 🏗️ Arquitectura

```
rag_platform/
├── accounts/          # Autenticación y gestión de usuarios
├── chat/             # Sistema de chat con historial
├── documents/        # Gestión y procesamiento de documentos
├── core/             # Motores RAG y procesamiento
│   ├── rag_engines.py       # FaissEngine y Neo4jEngine
│   ├── processor.py         # Procesamiento de PDFs
│   └── neo4j_indexer.py     # Indexación en Neo4j
├── templates/        # Templates HTML con Tailwind
└── static/          # CSS y JavaScript
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.10+
- PostgreSQL 14+
- Neo4j 5.0+ (Docker recomendado)
- OpenAI API Key

### 1. Clonar el Repositorio

```bash
git clone https://github.com/erikycd/RAG_dev.git
cd RAG_dev/RAG_dev
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

```bash
# Crear base de datos
sudo -u postgres psql
CREATE DATABASE rag_platform_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rag_platform_db TO postgres;
\q
```

### 5. Configurar Neo4j (Docker)

```bash
# Usar el docker-compose.yml existente en src/
cd ../src
docker-compose up -d

# Verificar que está corriendo
docker ps
```

### 6. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Django Configuration
DJANGO_SECRET_KEY=tu-secret-key-segura-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Database PostgreSQL
DB_NAME=rag_platform_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# OpenAI API
OPENAI_API_KEY=sk-tu-api-key-aqui

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword

# RAG Settings
EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-dot-v1
CHUNK_SIZE=512
CHUNK_OVERLAP=50
NUM_RETRIEVED_DOCS=12
TEMPERATURE=0.1
```

**IMPORTANTE**: La API key proporcionada (`sk-qmCJDMdaTJXgZJ9atwSmT3BlbkF`) está incompleta y debe ser regenerada desde tu cuenta de OpenAI.

### 7. Ejecutar Migraciones

```bash
cd /path/to/RAG_dev/RAG_dev
python manage.py makemigrations accounts chat documents core
python manage.py migrate
```

### 8. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 9. Iniciar Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a: `http://localhost:8000`

## 📦 Deployment en Producción (Gunicorn)

### 1. Configurar Gunicorn

El archivo `gunicorn_config.py` ya está configurado para el usuario `guerrero_gutierrez_hector` y grupo `www-data`.

### 2. Crear Directorios de Logs

```bash
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo chown guerrero_gutierrez_hector:www-data /var/log/gunicorn
sudo chown guerrero_gutierrez_hector:www-data /var/run/gunicorn
```

### 3. Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 4. Iniciar Gunicorn

```bash
gunicorn -c gunicorn_config.py rag_platform.wsgi:application
```

### 5. Configurar Nginx (Opcional)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location /static/ {
        alias /path/to/RAG_dev/staticfiles/;
    }

    location /media/ {
        alias /path/to/RAG_dev/rag_platform/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 6. Servicio Systemd

Crea `/etc/systemd/system/rag_platform.service`:

```ini
[Unit]
Description=RAG Platform Gunicorn Service
After=network.target

[Service]
User=guerrero_gutierrez_hector
Group=www-data
WorkingDirectory=/path/to/RAG_dev/RAG_dev
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py rag_platform.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start rag_platform
sudo systemctl enable rag_platform
```

## 🎮 Uso de la Plataforma

### 1. Registro e Inicio de Sesión
- Accede a la landing page
- Regístrate con usuario, email y contraseña
- Inicia sesión

### 2. Subir Documentos
- Ve a "Documentos" → "Subir Documento"
- Selecciona un PDF o TXT (máximo 50MB)
- Elige las opciones de indexación:
  - **FAISS**: Búsqueda semántica rápida
  - **Neo4j**: Grafo de conocimiento relacional
- El documento se procesará automáticamente

### 3. Chat con Documentos
- Ve al Dashboard de Chat
- Crea una nueva conversación
- Selecciona el motor RAG:
  - **FAISS**: Ideal para búsquedas por similitud semántica
  - **Neo4j**: Ideal para preguntas sobre relaciones entre conceptos
- Elige el documento (o todos)
- Comienza a hacer preguntas

### 4. Inspeccionar Chunks
- Ve a "Documentos" → Selecciona un documento
- Haz clic en "Ver chunks"
- Visualiza el texto fragmentado, metadata y embeddings

## 🔧 Motores RAG

### FAISS (Búsqueda Semántica)
```python
# Características:
- Índice vectorial en memoria
- Búsqueda por similitud coseno
- Ultra-rápido (milisegundos)
- Ideal para: "¿Qué dice sobre X?"
```

### Neo4j GraphRAG (Búsqueda Relacional)
```python
# Características:
- Índice vectorial + grafo de relaciones
- Expansión por similitud entre chunks
- Contexto relacional rico
- Ideal para: "¿Cómo se relaciona X con Y?"
```

## 📊 Modelo de Datos

### User (accounts)
- username, email, password
- preferred_engine (faiss/neo4j)
- avatar, bio

### Document (documents)
- title, file, status
- author, year, doi, abstract
- total_chunks, indexed_in_faiss, indexed_in_neo4j

### DocumentChunk (documents)
- chunk_id, text, chunk_index
- page_number, section
- embedding_preview

### Conversation (chat)
- title, engine_used
- is_active

### Message (chat)
- role (user/assistant/system)
- content, engine_used
- retrieval_time, generation_time
- retrieved_chunks_count

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.0, Python 3.10+
- **Base de Datos**: PostgreSQL 14+
- **Vector Store**: FAISS 1.8
- **Graph Database**: Neo4j 5.24
- **LLM**: OpenAI GPT-4o
- **Embeddings**: sentence-transformers (multi-qa-mpnet-base-dot-v1)
- **PDF Processing**: PyMuPDF, pypdf
- **Framework RAG**: LangChain
- **Frontend**: Tailwind CSS, Vanilla JavaScript
- **Server**: Gunicorn

## 🔐 Seguridad

- Secret keys en variables de entorno
- Passwords hasheados con PBKDF2
- CSRF protection habilitado
- SQL injection protection (Django ORM)
- Validación de tipos de archivo
- Límite de tamaño de archivos

## 📈 Optimizaciones

- Lazy loading de embedders
- Batch processing de embeddings
- Índices de base de datos optimizados
- Paginación en listas grandes
- Reranking local en Neo4j
- Caché de índices FAISS

## 🐛 Troubleshooting

### Error: "No module named 'django'"
```bash
pip install -r requirements.txt
```

### Error: Neo4j connection refused
```bash
# Verificar que el contenedor está corriendo
docker ps
docker-compose up -d
```

### Error: OpenAI API rate limit
- Verifica que tu API key tenga créditos
- Reduce TEMPERATURE o NUM_RETRIEVED_DOCS

### Error: PostgreSQL "role does not exist"
```bash
sudo -u postgres createuser tu_usuario
```

## 📝 Licencia

MIT License - Ver archivo LICENSE

## 👤 Autor

**Desarrollado por CUAED**
- Basado en: [RAG_dev](https://github.com/erikycd/RAG_dev)

## 🙏 Agradecimientos

- Arquitectura RAG base: erikycd/RAG_dev
- OpenAI GPT-4o
- LangChain Framework
- Neo4j Graph Database
- FAISS Vector Store

---

**Nota**: Esta plataforma utiliza la arquitectura de recuperación del repositorio RAG_dev y la extiende con una interfaz web completa, autenticación de usuarios y gestión avanzada de documentos.

Para más información sobre la arquitectura RAG base, consulta: https://github.com/erikycd/RAG_dev
