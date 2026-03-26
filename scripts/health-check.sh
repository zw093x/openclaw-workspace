#!/bin/bash
# 服务健康检查脚本
echo "=== 服务器健康检查 $(date) ==="

echo ""
echo "--- Docker 容器 ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker 未运行"

echo ""
echo "--- 系统服务 ---"
for svc in docker ttyd mihomo; do
  status=$(systemctl is-active $svc 2>/dev/null)
  echo "  $svc: $status"
done

echo ""
echo "--- 端口监听 ---"
for port in 7890 8081 8082; do
  listen=$(ss -tlnp | grep ":$port " > /dev/null && echo "✅ 监听中" || echo "❌ 未监听")
  echo "  端口 $port: $listen"
done

echo ""
echo "--- API 检查 ---"
# Open Terminal
curl -s --max-time 5 http://localhost:8081/health 2>/dev/null | grep -q "ok" && echo "  Open Terminal: ✅ 正常" || echo "  Open Terminal: ❌ 异常"
# ttyd
curl -sI --max-time 5 http://localhost:8082/ 2>/dev/null | grep -q "200\|401" && echo "  ttyd: ✅ 正常" || echo "  ttyd: ❌ 异常"

echo ""
echo "--- 磁盘空间 ---"
df -h / | tail -1 | awk '{print "  根分区: " $3 " used / " $2 " total (" $5 " used)"}'

echo ""
echo "--- 内存 ---"
free -h | grep Mem | awk '{print "  内存: " $3 " used / " $2 " total"}'
