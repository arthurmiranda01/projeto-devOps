#!/usr/bin/env bash
# Constroi a imagem, sobe o container e valida a API de ponta a ponta.
set -euo pipefail

IMAGEM="${1:-encurtador-url:teste}"
CONTAINER="${CONTAINER:-encurtador-teste}"
PORTA="${PORTA:-8000}"
BASE="http://localhost:${PORTA}"

limpar() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap limpar EXIT

if [ "${SKIP_BUILD:-0}" != "1" ]; then
  echo "==> Construindo a imagem $IMAGEM"
  docker build -t "$IMAGEM" .
fi

echo "==> Subindo o container"
limpar
docker run -d --name "$CONTAINER" -p "${PORTA}:8000" \
  -e "BASE_URL=${BASE}" "$IMAGEM" >/dev/null

echo "==> Esperando o healthcheck ficar saudavel"
for _ in $(seq 1 30); do
  estado=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo desconhecido)
  [ "$estado" = "healthy" ] && break
  if [ "$estado" = "unhealthy" ]; then
    docker logs "$CONTAINER"
    echo "FALHA: container marcado como unhealthy"
    exit 1
  fi
  sleep 3
done
if [ "$estado" != "healthy" ]; then
  docker logs "$CONTAINER"
  echo "FALHA: o container nao ficou saudavel a tempo"
  exit 1
fi

echo "==> Verificando que a aplicacao nao roda como root"
uid=$(docker exec "$CONTAINER" id -u)
if [ "$uid" = "0" ]; then
  echo "FALHA: o container esta rodando como root"
  exit 1
fi
echo "    uid=$uid"

echo "==> GET /health"
curl -fsS "${BASE}/health" | grep -q '"status":"ok"'

echo "==> POST /links"
criado=$(curl -fsS -X POST "${BASE}/links" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://pucpr.br", "codigo": "pucpr"}')
echo "    $criado"
echo "$criado" | grep -q '"codigo":"pucpr"'

echo "==> GET /pucpr (redirecionamento)"
codigo_http=$(curl -fsS -o /dev/null -w '%{http_code}' "${BASE}/pucpr")
destino=$(curl -fsS -o /dev/null -w '%{redirect_url}' "${BASE}/pucpr")
echo "    $codigo_http -> $destino"
[ "$codigo_http" = "307" ]

echo "==> GET /links/pucpr (contador de acessos)"
curl -fsS "${BASE}/links/pucpr" | grep -q '"acessos":2'

echo "==> DELETE /links/pucpr"
codigo_http=$(curl -fsS -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/links/pucpr")
[ "$codigo_http" = "204" ]

echo "==> Tamanho da imagem"
docker image inspect "$IMAGEM" --format '    {{.RepoTags}} {{div .Size 1048576}} MB'

echo "==> Container validado com sucesso"
