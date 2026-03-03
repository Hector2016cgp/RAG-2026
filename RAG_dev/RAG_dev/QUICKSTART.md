"""
Guía Rápida - RAG Platform
===========================

## 🚀 Inicio Rápido (5 minutos)

### Opción 1: Script Automático

```bash
./start.sh
```

### Opción 2: Manual

1. **Crear entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar .env:**
   ```bash
   cp .env.example .env
   nano .env  # Editar con tus credenciales
   ```

4. **Iniciar Neo4j:**
   ```bash
   cd ../src
   docker-compose up -d
   cd -
   ```

5. **Migrar base de datos:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Iniciar servidor:**
   ```bash
   python manage.py runserver
   ```

7. **Acceder:**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 📝 Flujo de Uso

1. **Registrarse** en la landing page
2. **Subir documento** PDF/TXT
3. **Crear conversación** en el chat
4. **Seleccionar motor** (FAISS o Neo4j)
5. **Hacer preguntas** sobre el documento

## ⚙️ Configuración Importante

### API Key de OpenAI
La API key proporcionada está **incompleta**. Obtén una nueva en:
https://platform.openai.com/api-keys

### PostgreSQL
```bash
# Crear base de datos
sudo -u postgres psql
CREATE DATABASE rag_platform_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE rag_platform_db TO postgres;
```

### Neo4j (Docker)
```bash
cd src/
docker-compose up -d
# Acceso: http://localhost:7474
# Usuario: neo4j
# Password: (ver docker-compose.yml)
```

## 🎯 Motores RAG

### FAISS
- ✅ Búsqueda semántica rápida
- ✅ Índice vectorial en memoria
- ✅ Ideal para: "¿Qué dice sobre...?"

### Neo4j
- ✅ Grafo de conocimiento
- ✅ Relaciones entre conceptos
- ✅ Ideal para: "¿Cómo se relaciona X con Y?"

## 🔧 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell

# Verificar deploy
python manage.py check --deploy
```

## 📂 Estructura de Carpetas

```
rag_platform/
├── accounts/       # Usuarios y autenticación
├── chat/          # Sistema de chat
├── documents/     # Gestión de documentos
├── core/          # Engines RAG
├── templates/     # HTML
└── static/        # CSS/JS
```

## 🐛 Problemas Comunes

### Error: "No module named 'django'"
```bash
pip install -r requirements.txt
```

### Error: Neo4j connection refused
```bash
docker ps  # Verificar que esté corriendo
docker-compose up -d  # Reiniciar
```

### Error: PostgreSQL authentication
```bash
# Verificar pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Cambiar método a 'md5'
```

### Error: OpenAI API rate limit
- Verifica que tu cuenta tenga créditos
- Reduce NUM_RETRIEVED_DOCS en .env

## 📚 Documentación Completa

- **README_PLATFORM.md**: Documentación completa
- **DEPLOYMENT.md**: Guía de deployment
- **requirements.txt**: Dependencias

## 🎓 Ejemplos de Uso

### Pregunta con FAISS:
```
Usuario: "¿Qué dice el documento sobre machine learning?"
Sistema: [Busca semánticamente y responde con citas]
```

### Pregunta con Neo4j:
```
Usuario: "¿Cómo se relaciona el aprendizaje supervisado con las redes neuronales?"
Sistema: [Navega el grafo de conceptos y explica relaciones]
```

## 🔗 Links Útiles

- **OpenAI**: https://platform.openai.com
- **Neo4j**: https://neo4j.com/docs
- **Django**: https://docs.djangoproject.com
- **LangChain**: https://python.langchain.com

## 💡 Tips

1. Usa FAISS para búsquedas rápidas y directas
2. Usa Neo4j para análisis complejos y relacionales
3. Mantén tus documentos organizados por tema
4. Revisa los chunks para entender cómo se fragmentó el texto
5. Ajusta CHUNK_SIZE según tus necesidades (más pequeño = más preciso, más lento)

---

**¿Necesitas ayuda?** Consulta README_PLATFORM.md o abre un issue en GitHub.
