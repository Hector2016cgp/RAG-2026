#!/bin/bash

# =====================================================
# Script de Inicio Rápido - RAG Platform
# =====================================================

echo "🚀 Iniciando RAG Platform..."

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar Python
echo -e "${YELLOW}📌 Verificando Python...${NC}"
python3 --version || { echo -e "${RED}❌ Python no encontrado. Instala Python 3.10+${NC}"; exit 1; }

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
echo -e "${YELLOW}🔧 Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${YELLOW}📥 Instalando dependencias...${NC}"
pip install -r requirements.txt

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️  Archivo .env no encontrado.${NC}"
    echo -e "${YELLOW}Copiando .env.example a .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Archivo .env creado. Por favor, configúralo antes de continuar.${NC}"
    exit 1
fi

# Verificar PostgreSQL
echo -e "${YELLOW}🐘 Verificando PostgreSQL...${NC}"
pg_isready -q || { echo -e "${RED}❌ PostgreSQL no está corriendo. Inícialo primero.${NC}"; exit 1; }

# Verificar Neo4j (Docker)
echo -e "${YELLOW}🐳 Verificando Neo4j...${NC}"
if ! docker ps | grep -q neo4j; then
    echo -e "${YELLOW}Iniciando Neo4j con Docker...${NC}"
    cd ../src
    docker-compose up -d
    cd -
    echo -e "${GREEN}✅ Neo4j iniciado${NC}"
    sleep 5
fi

# Ejecutar migraciones
echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
python manage.py makemigrations
python manage.py migrate

# Crear superusuario (solo si no existe)
echo -e "${YELLOW}👤 ¿Deseas crear un superusuario? (s/n)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    python manage.py createsuperuser
fi

# Recolectar archivos estáticos
echo -e "${YELLOW}📁 Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ RAG Platform está listo!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}Para iniciar el servidor:${NC}"
echo -e "  ${GREEN}python manage.py runserver${NC}"
echo ""
echo -e "${YELLOW}Accede a:${NC}"
echo -e "  ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Panel de administración:${NC}"
echo -e "  ${GREEN}http://localhost:8000/admin${NC}"
echo ""

# Iniciar servidor (opcional)
echo -e "${YELLOW}¿Deseas iniciar el servidor ahora? (s/n)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    python manage.py runserver
fi
