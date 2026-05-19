#!/bin/bash
# =============================================================================
# Cloudflare Tunnel + Ollama 외부 노출 설정 스크립트
# Ubuntu GPU 서버에서 실행
#
# 사용법:
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# 실행 전 필수 설정:
#   TUNNEL_NAME, DOMAIN 변수를 실제 값으로 변경하세요
# =============================================================================

set -e  # 오류 발생 시 즉시 중단

# ── 설정값 (여기를 수정하세요) ────────────────────────────────────────────────
TUNNEL_NAME="ollama-tunnel"
DOMAIN="ollama.mydomain.com"          # 실제 도메인으로 변경
VERCEL_URL="https://your-app.vercel.app"  # Vercel 앱 URL로 변경
OLLAMA_MODEL="llama3"
# ─────────────────────────────────────────────────────────────────────────────

echo "======================================================"
echo " Cloudflare Tunnel + Ollama 설정 시작"
echo " Domain: $DOMAIN"
echo "======================================================"

# ── Step 1: cloudflared 설치 ──────────────────────────────────────────────────
echo ""
echo "[1/7] cloudflared 설치 중..."
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
  -o /tmp/cloudflared.deb
dpkg -i /tmp/cloudflared.deb
rm /tmp/cloudflared.deb
echo "✅ cloudflared 설치 완료: $(cloudflared --version)"

# ── Step 2: Cloudflare 로그인 ─────────────────────────────────────────────────
echo ""
echo "[2/7] Cloudflare 로그인..."
echo "⚠️  브라우저에서 인증 URL을 열어 로그인하세요."
cloudflared tunnel login

# ── Step 3: Tunnel 생성 ───────────────────────────────────────────────────────
echo ""
echo "[3/7] Tunnel 생성 중: $TUNNEL_NAME"
cloudflared tunnel create "$TUNNEL_NAME"

# Tunnel ID 추출
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "✅ Tunnel ID: $TUNNEL_ID"

# ── Step 4: DNS 레코드 연결 ───────────────────────────────────────────────────
echo ""
echo "[4/7] DNS 레코드 연결: $DOMAIN"
cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN"
echo "✅ DNS 연결 완료"

# ── Step 5: config.yml 작성 ───────────────────────────────────────────────────
echo ""
echo "[5/7] Tunnel config 작성 중..."
mkdir -p /etc/cloudflared

cat > /etc/cloudflared/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: /root/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ${DOMAIN}
    service: http://localhost:11434
    originRequest:
      noTLSVerify: false
      connectTimeout: 30s
      tcpKeepAlive: 30s
      httpHostHeader: "${DOMAIN}"

  - service: http_status:404
EOF

echo "✅ /etc/cloudflared/config.yml 작성 완료"

# ── Step 6: Ollama CORS 설정 ──────────────────────────────────────────────────
echo ""
echo "[6/7] Ollama 환경변수 설정 중..."
mkdir -p /etc/systemd/system/ollama.service.d

cat > /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=${VERCEL_URL},https://${DOMAIN}"
EOF

systemctl daemon-reload
systemctl restart ollama
sleep 3

# Ollama 동작 확인
if curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "✅ Ollama 정상 동작 확인"
else
  echo "⚠️  Ollama 응답 없음 — 수동으로 확인 필요: sudo systemctl status ollama"
fi

# ── Step 7: cloudflared systemd 서비스 등록 ───────────────────────────────────
echo ""
echo "[7/7] cloudflared 서비스 등록 중..."

cat > /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=Cloudflare Tunnel (Ollama)
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cloudflared
systemctl start cloudflared
sleep 3

# 서비스 상태 확인
if systemctl is-active --quiet cloudflared; then
  echo "✅ cloudflared 서비스 실행 중"
else
  echo "⚠️  cloudflared 서비스 시작 실패 — 로그 확인: journalctl -u cloudflared -n 50"
fi

# ── 완료 ──────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo " 설정 완료!"
echo "======================================================"
echo ""
echo "📌 외부 접속 테스트:"
echo "   curl https://${DOMAIN}/api/tags"
echo ""
echo "📌 서비스 상태 확인:"
echo "   sudo systemctl status cloudflared"
echo "   sudo systemctl status ollama"
echo ""
echo "📌 로그 확인:"
echo "   journalctl -u cloudflared -f"
echo ""
echo "⚠️  보안 설정 (Cloudflare Access) 은 대시보드에서 수동으로 설정하세요:"
echo "   https://one.dash.cloudflare.com → Zero Trust → Access → Applications"
echo ""
