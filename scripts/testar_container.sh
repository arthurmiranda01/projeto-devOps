#!/usr/bin/env bash
# Constroi a imagem, sobe o container e valida a API de ponta a ponta.
set -Eeuo pipefail

IMAGEM="${1:-encurtador-url:teste}"
CONTAINER="${CONTAINER:-encurtador-teste}"
PORTA="${PORTA:-8000}"
BASE="http://localhost:${PORTA}"
ETAPA="inicializacao"

SAIDA=$(mktemp)
exec > >(tee "$SAIDA") 2>&1

limpar() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}

falhou() {
  codigo=$?
  echo "FALHA durante: $ETAPA (exit $codigo)"
  docker logs "$CONTAINER" 2>&1 | tail -30 || true
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    sleep 1
    detalhe=$(tail -c 1800 "$SAIDA" | sed 's/%/%25/g; s/\r/ /g' | awk '{printf "%s%%0A", $0}')
    echo "::error title=Teste do container falhou em ${ETAPA}::exit ${codigo}%0A${detalhe}"
  fi
}

trap limpar EXIT
trap falhou ERR

if [ "${SKIP_BUILD:-0}" != "1" ]; then
  ETAPA="build da imagem"
  echo "==> Construindo a imagem $IMAGEM"
  docker build -t "$IMAGEM" .
fi

ETAPA="subida do container"
echo "==> Subindo o container"
limpar
docker run -d --name "$CONTAINER" -p "${PORTA}:8000" \
  -e "BASE_URL=${BASE}" "$IMAGEM" >/dev/null

ETAPA="healthcheck"
echo "==> Esperando o healthcheck ficar saudavel"
estado=desconhecido
for _ in $(seq 1 30); do
  estado=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo desconhecido)
  [ "$estado" = "healthy" ] && break
  if [ "$estado" = "unhealthy" ]; then
    echo "container marcado como unhealthy"
    false
  fi
  sleep 3
done
if [ "$estado" != "healthy" ]; then
  echo "o container nao ficou saudavel a tempo (estado=$estado)"
  false
fi

ETAPA="usuario sem privilegios"
echo "==> Verificando que a aplicacao nao roda como root"
uid=$(docker exec "$CONTAINER" id -u)
if [ "$uid" = "0" ]; then
  echo "o container esta rodando como root"
  false
fi
echo "    uid=$uid"

ETAPA="GET /health"
echo "==> GET /health"
curl -fsS "${BASE}/health" | grep -q '"status":"ok"'

ETAPA="POST /links"
echo "==> POST /links"
criado=$(curl -fsS -X POST "${BASE}/links" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://pucpr.br", "codigo": "pucpr"}')
echo "    $criado"
echo "$criado" | grep -q '"codigo":"pucpr"'

ETAPA="redirecionamento"
echo "==> GET /pucpr"
codigo_http=$(curl -fsS -o /dev/null -w '%{http_code}' "${BASE}/pucpr")
destino=$(curl -fsS -o /dev/null -w '%{redirect_url}' "${BASE}/pucpr")
echo "    $codigo_http -> $destino"
[ "$codigo_http" = "307" ]

ETAPA="contador de acessos"
echo "==> GET /links/pucpr"
curl -fsS "${BASE}/links/pucpr" | grep -q '"acessos":2'

ETAPA="remocao do link"
echo "==> DELETE /links/pucpr"
codigo_http=$(curl -fsS -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/links/pucpr")
[ "$codigo_http" = "204" ]

ETAPA="tamanho da imagem"
bytes=$(docker image inspect "$IMAGEM" --format '{{.Size}}')
echo "==> Tamanho da imagem: $((bytes / 1048576)) MB"

echo "==> Container validado com sucesso"
