#!/usr/bin/env bash
# Diagnóstico para la dashboard — ejecutar en la VM cuando hay problemas
set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Diagnóstico Dashboard ===${NC}\n"

# 1. Estado del servicio
echo -e "${YELLOW}[1] Estado del servicio${NC}"
systemctl status agentic-software-boutique.service --no-pager | head -10
echo ""

# 2. Últimos logs de uvicorn
echo -e "${YELLOW}[2] Últimos 50 logs de uvicorn${NC}"
journalctl -u agentic-software-boutique.service -n 50 --no-pager
echo ""

# 3. Puerto 8765
echo -e "${YELLOW}[3] Verificando puerto 8765${NC}"
if netstat -tlnp 2>/dev/null | grep -q 8765; then
  echo -e "${GREEN}✓ Puerto 8765 está abierto${NC}"
else
  echo -e "${RED}✗ Puerto 8765 NO responde${NC}"
fi
echo ""

# 4. Nginx
echo -e "${YELLOW}[4] Estado de nginx${NC}"
systemctl status nginx --no-pager | head -5
echo ""

# 5. Errores de nginx
echo -e "${YELLOW}[5] Últimos errores de nginx${NC}"
tail -20 /var/log/nginx/error.log
echo ""

# 6. Intentar arrancar manualmente para ver el error
echo -e "${YELLOW}[6] Intentando arrancar uvicorn manualmente (3 segundos)${NC}"
cd /home/ubuntu/agentic-software-boutique/dashboard || cd /home/ubuntu/Claude/dashboard || exit 1
source .venv/bin/activate 2>/dev/null || echo "⚠ No se pudo activar venv"
timeout 3 python3 -m uvicorn main:app --host 127.0.0.1 --port 8765 2>&1 || true
echo ""

echo -e "${YELLOW}[7] Verificar que dependencies están instaladas${NC}"
pip list | grep -E "fastapi|uvicorn|pydantic" || echo "⚠ Falta alguna dependencia"
