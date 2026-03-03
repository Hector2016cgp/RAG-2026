#!/bin/bash
# COMANDOS ÚTILES PARA RAG PLATFORM
# ====================================

# NOTA: Ejecuta estos comandos desde la raíz del proyecto
# Asegúrate de tener el virtualenv activado: source venv/bin/activate

echo "════════════════════════════════════════════════════"
echo "     RAG PLATFORM - COMANDOS ÚTILES"
echo "════════════════════════════════════════════════════"
echo ""

# ╔══════════════════════════════════════════════════════╗
# ║  1. GESTIÓN DE SERVICIOS                             ║
# ╚══════════════════════════════════════════════════════╝

# Iniciar todos los servicios necesarios
start_all_services() {
    echo "🚀 Iniciando todos los servicios..."
    sudo systemctl start postgresql
    cd src && docker-compose up -d && cd ..
    echo "✅ PostgreSQL y Neo4j iniciados"
}

# Verificar estado de servicios
check_services() {
    echo "🔍 Verificando servicios..."
    echo ""
    echo "📊 PostgreSQL:"
    sudo systemctl status postgresql --no-pager | head -3
    echo ""
    echo "📊 Neo4j (Docker):"
    docker ps | grep neo4j || echo "❌ Neo4j no está corriendo"
    echo ""
    echo "📊 Conexión PostgreSQL:"
    pg_isready || echo "❌ PostgreSQL no está listo"
}

# Detener servicios
stop_all_services() {
    echo "🛑 Deteniendo servicios..."
    cd src && docker-compose down && cd ..
    sudo systemctl stop postgresql
    echo "✅ Servicios detenidos"
}

# ╔══════════════════════════════════════════════════════╗
# ║  2. DESARROLLO                                        ║
# ╚══════════════════════════════════════════════════════╝

# Iniciar servidor de desarrollo
dev_server() {
    cd rag_platform
    python manage.py runserver 0.0.0.0:8000
}

# Iniciar servidor con Gunicorn (producción local)
prod_server() {
    cd rag_platform
    gunicorn -c ../gunicorn_config.py rag_platform.wsgi:application
}

# Crear nuevas migraciones
make_migrations() {
    cd rag_platform
    python manage.py makemigrations
    python manage.py migrate
}

# Reset base de datos (⚠️ CUIDADO: Borra todos los datos)
reset_database() {
    read -p "⚠️  ESTO BORRARÁ TODOS LOS DATOS. ¿Continuar? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        cd rag_platform
        python manage.py flush --no-input
        python manage.py migrate
        echo "✅ Base de datos reseteada"
    else
        echo "❌ Operación cancelada"
    fi
}

# ╔══════════════════════════════════════════════════════╗
# ║  3. GESTIÓN DE BASE DE DATOS                         ║
# ╚══════════════════════════════════════════════════════╝

# Abrir shell de PostgreSQL
psql_shell() {
    psql -U rag_user -d rag_platform_db
}

# Backup de PostgreSQL
backup_postgres() {
    timestamp=$(date +%Y%m%d_%H%M%S)
    pg_dump -U rag_user rag_platform_db > "backups/postgres_backup_${timestamp}.sql"
    echo "✅ Backup creado: backups/postgres_backup_${timestamp}.sql"
}

# Restaurar backup de PostgreSQL
restore_postgres() {
    read -p "Ruta del archivo backup: " backup_file
    if [ -f "$backup_file" ]; then
        psql -U rag_user -d rag_platform_db < "$backup_file"
        echo "✅ Backup restaurado"
    else
        echo "❌ Archivo no encontrado"
    fi
}

# Estadísticas de base de datos
db_stats() {
    cd rag_platform
    python manage.py shell << EOF
from accounts.models import User
from documents.models import Document, DocumentChunk
from chat.models import Conversation, Message

print("═" * 50)
print("     ESTADÍSTICAS DE BASE DE DATOS")
print("═" * 50)
print(f"👥 Usuarios: {User.objects.count()}")
print(f"📄 Documentos: {Document.objects.count()}")
print(f"  ├─ Completados: {Document.objects.filter(status='completed').count()}")
print(f"  ├─ En proceso: {Document.objects.filter(status='processing').count()}")
print(f"  └─ Fallidos: {Document.objects.filter(status='failed').count()}")
print(f"📦 Chunks: {DocumentChunk.objects.count()}")
print(f"💬 Conversaciones: {Conversation.objects.count()}")
print(f"  ├─ FAISS: {Conversation.objects.filter(engine_used='faiss').count()}")
print(f"  └─ Neo4j: {Conversation.objects.filter(engine_used='neo4j').count()}")
print(f"✉️  Mensajes: {Message.objects.count()}")
print("═" * 50)
EOF
}

# ╔══════════════════════════════════════════════════════╗
# ║  4. GESTIÓN DE NEO4J                                 ║
# ╚══════════════════════════════════════════════════════╝

# Abrir Cypher shell de Neo4j
neo4j_shell() {
    docker exec -it rag_neo4j cypher-shell -u neo4j -p your_password
}

# Estadísticas de Neo4j
neo4j_stats() {
    docker exec -it rag_neo4j cypher-shell -u neo4j -p your_password << EOF
MATCH (n:Chunk) 
RETURN count(n) as total_chunks;

MATCH ()-[r:SIMILAR_TO]->() 
RETURN count(r) as total_relationships;

CALL db.labels() YIELD label
RETURN label, count(*) as count
ORDER BY count DESC;
EOF
}

# Backup de Neo4j
backup_neo4j() {
    timestamp=$(date +%Y%m%d_%H%M%S)
    docker exec rag_neo4j neo4j-admin database dump neo4j --to-path=/backups
    docker cp rag_neo4j:/backups "backups/neo4j_backup_${timestamp}"
    echo "✅ Backup Neo4j creado: backups/neo4j_backup_${timestamp}"
}

# Limpiar base de datos Neo4j (⚠️ CUIDADO)
clean_neo4j() {
    read -p "⚠️  ESTO BORRARÁ TODOS LOS NODOS Y RELACIONES EN NEO4J. ¿Continuar? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        docker exec -it rag_neo4j cypher-shell -u neo4j -p your_password << EOF
MATCH (n) DETACH DELETE n;
EOF
        echo "✅ Neo4j limpiado"
    else
        echo "❌ Operación cancelada"
    fi
}

# ╔══════════════════════════════════════════════════════╗
# ║  5. GESTIÓN DE FAISS                                 ║
# ╚══════════════════════════════════════════════════════╝

# Listar índices FAISS
list_faiss_indexes() {
    echo "📊 Índices FAISS:"
    ls -lh rag_platform/core/faiss_indexes/
}

# Limpiar índices FAISS
clean_faiss_indexes() {
    read -p "⚠️  ESTO BORRARÁ TODOS LOS ÍNDICES FAISS. ¿Continuar? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        rm -rf rag_platform/core/faiss_indexes/*.pkl
        echo "✅ Índices FAISS limpiados"
    else
        echo "❌ Operación cancelada"
    fi
}

# Reconstruir índices FAISS desde documentos existentes
rebuild_faiss_indexes() {
    cd rag_platform
    python manage.py shell << EOF
from documents.models import Document
from core.rag_engines import FaissEngine

print("🔄 Reconstruyendo índices FAISS...")
completed_docs = Document.objects.filter(status='completed', indexed_in_faiss=True)
print(f"📄 Documentos a reindexar: {completed_docs.count()}")

for doc in completed_docs:
    print(f"  ⏳ Procesando: {doc.title}")
    engine = FaissEngine()
    chunks = doc.chunks.all()
    texts = [chunk.text for chunk in chunks]
    metadatas = [{'chunk_id': chunk.chunk_id, 'page': chunk.page_number} for chunk in chunks]
    engine.index_documents(texts, metadatas)
    engine.save_index(f"document_{doc.id}")
    doc.faiss_index_path = f"document_{doc.id}.pkl"
    doc.save()
    print(f"  ✅ {doc.title} reindexado")

print("✅ Reconstrucción completa")
EOF
}

# ╔══════════════════════════════════════════════════════╗
# ║  6. TESTING Y DEPURACIÓN                             ║
# ╚══════════════════════════════════════════════════════╝

# Ejecutar shell de Django
django_shell() {
    cd rag_platform
    python manage.py shell
}

# Verificar configuración
check_config() {
    cd rag_platform
    python manage.py check
}

# Test completo del sistema
test_system() {
    echo "🧪 Testing sistema RAG..."
    cd rag_platform
    python << EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_platform.settings')
django.setup()

from core.rag_engines import FaissEngine, Neo4jEngine

print("═" * 50)
print("     TEST DE MOTORES RAG")
print("═" * 50)

# Test FAISS
print("\n🔍 Test FaissEngine:")
try:
    faiss_engine = FaissEngine()
    print("  ✅ FaissEngine inicializado")
    print(f"  ├─ Embedder: {faiss_engine.embedder.__class__.__name__}")
    print(f"  └─ LLM: {faiss_engine.llm.__class__.__name__}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test Neo4j
print("\n🔍 Test Neo4jEngine:")
try:
    neo4j_engine = Neo4jEngine()
    if neo4j_engine._check_connection():
        print("  ✅ Neo4jEngine inicializado")
        print(f"  ├─ Conexión: OK")
        print(f"  ├─ Embedder: {neo4j_engine.embedder.__class__.__name__}")
        print(f"  └─ LLM: {neo4j_engine.llm.__class__.__name__}")
    else:
        print("  ⚠️  Neo4j no conectado")
    neo4j_engine.close()
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n═" * 50)
EOF
}

# Logs en tiempo real
tail_logs() {
    tail -f rag_platform/logs/debug.log
}

# ╔══════════════════════════════════════════════════════╗
# ║  7. MANTENIMIENTO                                     ║
# ╚══════════════════════════════════════════════════════╝

# Limpiar archivos temporales
clean_temp() {
    echo "🧹 Limpiando archivos temporales..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name ".DS_Store" -delete
    echo "✅ Archivos temporales limpiados"
}

# Actualizar dependencias
update_dependencies() {
    pip install --upgrade pip
    pip install -r requirements.txt --upgrade
    echo "✅ Dependencias actualizadas"
}

# Recolectar archivos estáticos
collect_static() {
    cd rag_platform
    python manage.py collectstatic --no-input
    echo "✅ Archivos estáticos recolectados"
}

# Verificar integridad del sistema
health_check() {
    echo "🏥 Verificación de salud del sistema..."
    echo ""
    
    # Virtualenv
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "✅ Virtualenv activado: $VIRTUAL_ENV"
    else
        echo "⚠️  Virtualenv NO activado"
    fi
    
    # Python
    python --version && echo "✅ Python OK" || echo "❌ Python no encontrado"
    
    # Django
    python -c "import django; print(f'✅ Django {django.get_version()} OK')" 2>/dev/null || echo "❌ Django no instalado"
    
    # PostgreSQL
    pg_isready && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL no disponible"
    
    # Neo4j
    docker ps | grep -q neo4j && echo "✅ Neo4j OK" || echo "❌ Neo4j no corriendo"
    
    # FAISS
    python -c "import faiss; print('✅ FAISS OK')" 2>/dev/null || echo "❌ FAISS no instalado"
    
    # OpenAI
    python -c "import openai; print('✅ OpenAI OK')" 2>/dev/null || echo "❌ OpenAI no instalado"
    
    # LangChain
    python -c "import langchain; print('✅ LangChain OK')" 2>/dev/null || echo "❌ LangChain no instalado"
}

# ╔══════════════════════════════════════════════════════╗
# ║  MENÚ INTERACTIVO                                     ║
# ╚══════════════════════════════════════════════════════╝

show_menu() {
    clear
    echo "════════════════════════════════════════════════════"
    echo "     RAG PLATFORM - MENÚ DE COMANDOS"
    echo "════════════════════════════════════════════════════"
    echo ""
    echo "📦 SERVICIOS:"
    echo "  1) Iniciar todos los servicios"
    echo "  2) Verificar estado de servicios"
    echo "  3) Detener todos los servicios"
    echo ""
    echo "💻 DESARROLLO:"
    echo "  4) Iniciar servidor desarrollo (runserver)"
    echo "  5) Iniciar servidor producción (gunicorn)"
    echo "  6) Crear migraciones"
    echo "  7) Reset base de datos"
    echo ""
    echo "🗄️  BASE DE DATOS:"
    echo "  8) PostgreSQL shell"
    echo "  9) Backup PostgreSQL"
    echo " 10) Estadísticas DB"
    echo ""
    echo "🔷 NEO4J:"
    echo " 11) Neo4j Cypher shell"
    echo " 12) Estadísticas Neo4j"
    echo " 13) Backup Neo4j"
    echo " 14) Limpiar Neo4j"
    echo ""
    echo "⚡ FAISS:"
    echo " 15) Listar índices FAISS"
    echo " 16) Reconstruir índices FAISS"
    echo " 17) Limpiar índices FAISS"
    echo ""
    echo "🧪 TESTING:"
    echo " 18) Django shell"
    echo " 19) Test sistema RAG"
    echo " 20) Verificar salud del sistema"
    echo ""
    echo "🔧 MANTENIMIENTO:"
    echo " 21) Limpiar archivos temporales"
    echo " 22) Actualizar dependencias"
    echo " 23) Recolectar archivos estáticos"
    echo ""
    echo " 0) Salir"
    echo ""
    echo "════════════════════════════════════════════════════"
}

# Loop del menú
if [ "$1" == "--menu" ]; then
    while true; do
        show_menu
        read -p "Selecciona una opción: " choice
        echo ""
        
        case $choice in
            1) start_all_services ;;
            2) check_services ;;
            3) stop_all_services ;;
            4) dev_server ;;
            5) prod_server ;;
            6) make_migrations ;;
            7) reset_database ;;
            8) psql_shell ;;
            9) backup_postgres ;;
            10) db_stats ;;
            11) neo4j_shell ;;
            12) neo4j_stats ;;
            13) backup_neo4j ;;
            14) clean_neo4j ;;
            15) list_faiss_indexes ;;
            16) rebuild_faiss_indexes ;;
            17) clean_faiss_indexes ;;
            18) django_shell ;;
            19) test_system ;;
            20) health_check ;;
            21) clean_temp ;;
            22) update_dependencies ;;
            23) collect_static ;;
            0) echo "👋 ¡Hasta luego!"; exit 0 ;;
            *) echo "❌ Opción inválida" ;;
        esac
        
        echo ""
        read -p "Presiona Enter para continuar..."
    done
else
    echo ""
    echo "💡 USO:"
    echo "  ./useful_commands.sh --menu    → Menú interactivo"
    echo "  source useful_commands.sh      → Cargar funciones en shell"
    echo ""
    echo "📝 FUNCIONES DISPONIBLES (después de source):"
    echo "  start_all_services     - Iniciar PostgreSQL + Neo4j"
    echo "  check_services         - Verificar estado servicios"
    echo "  dev_server            - Servidor desarrollo"
    echo "  db_stats              - Estadísticas base de datos"
    echo "  test_system           - Test completo motores RAG"
    echo "  health_check          - Verificación salud sistema"
    echo "  rebuild_faiss_indexes - Reconstruir índices FAISS"
    echo "  clean_temp            - Limpiar archivos temporales"
    echo ""
    echo "📚 Más info: Ver comentarios en el archivo"
    echo ""
fi
