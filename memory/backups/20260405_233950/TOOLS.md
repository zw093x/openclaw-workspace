# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

- **Token**: `3d1438146f355d26c67c44516d809171ae180cedf85981d2`（2026-03-29 更新）
- **UI**: http://127.0.0.1:18789（WebSocket 连接）

## 服务器称呼规范

| 称呼 | 指向 | IP |
|------|------|-----|
| **云服务器** | 腾讯云轻量应用 | 42.193.183.176 |
| **本地服务器** | P工的本机/本地部署 | 127.0.0.1 |

## Open Terminal (Docker)
- **状态**: ✅ 运行中 (Docker)
- **镜像**: ghcr.nju.edu.cn/open-webui/open-terminal:main
- **端口**: 8081 (映射容器内8000)
- **API Key**: 3SPH6J0J8nytZGU2pOphXgrjm2dkhd3y
- **API 文档**: http://159.75.77.36:8081/docs
- **管理**: cd /opt/open-terminal && docker compose up -d
- **⚠️ 需开通安全组端口 8081**

## ttyd (Web 终端)
- **状态**: ✅ 运行中 (systemd)
- **端口**: 8082
- **登录**: admin / ttyd2026
- **管理**: systemctl status/start/stop/restart ttyd
- **⚠️ 需开通安全组端口 8082**

## Docker
- **版本**: Docker CE 29.3.1 + Compose v5.1.1
- **代理**: 127.0.0.1:7890 (mihomo)
- **镜像加速**: docker.1ms.run

## 腾讯云 CLI (tccli)
- **版本**: 3.1.59.1
- **状态**: 已安装, 需配置 SecretId/SecretKey
- **配置**: `tccli configure set`

## Proxy (mihomo)

- **Status**: ✅ Running (systemd, enabled)
- **Port**: `127.0.0.1:7890` (HTTP + SOCKS5 mixed)
- **Config**: `/etc/mihomo/config.yaml`
- **Service**: `systemctl status mihomo` / `systemctl restart mihomo`
- **Nodes**: 16个 Trojan 节点（上海联通/电信/移动 → 新加坡/日本）
- **可访问**: OpenRouter ✅, Google ✅, GitHub ✅, httpbin ✅
- **不可访问**: Google API（TLS 层面被拦截，需通过 OpenRouter 中转）

## AI Models

- **当前免费模型**: `blockrun/nemotron`（Nemotron Ultra 253B，通过 BlockRun 路由，$0 成本）
- **OpenRouter**: 已充值，可用免费模型11个（详见 MEMORY.md）
- **备选付费模型**: `openrouter/google/gemini-2.5-flash`（$0.15/M 输入，性价比最高）
- **Gemini Key**: `AIzaSyAT4rLWTjDh-2Y3zepE5MRXcNfCm8w0pIg`（Google 直连不可用，暂保留）
- **所有 Cron 任务**: 已统一切换到 `blockrun/nemotron`（免费）

---

## 国际新闻RSS源（通过代理 http://127.0.0.1:7890 访问）

| 媒体 | RSS地址 | 覆盖领域 |
|------|---------|---------|
| BBC News | `https://feeds.bbci.co.uk/news/world/rss.xml` | 全球综合 |
| CNBC | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114` | 财经/市场/特朗普 |
| France 24 | `https://www.france24.com/en/rss` | 国际政治/中东 |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | 中东/伊朗 |
| The Guardian | `https://www.theguardian.com/world/rss` | 全球深度分析 |
| NPR | `https://feeds.npr.org/1001/rss.xml` | 美国国内 |
| Deutsche Welle | `https://rss.dw.com/rdf/rss-en-all` | 欧洲视角 |

**使用方式：** `curl -s --max-time 15 -x http://127.0.0.1:7890 '<RSS地址>'`

---

## Google 账号

- **邮箱：** zw093x@gmail.com
- **密码：** 0908093x.
- **用途：** X/Twitter、Google搜索、GitHub等国际网站登录

> ⚠️ 注意：密码为敏感信息，仅存储于本地服务器，不外泄。

---

Add whatever helps you do your job. This is your cheat sheet.

## 飞书文档分享规则（2026-04-04）

**所有我创建的飞书文档，创建后必须立即设置为任何人可查看。**

操作步骤：
1. 创建文档后获取 doc_id
2. 调用飞书权限API：
```bash
# 获取 token
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"cli_a9489e1f4c78dbb6","app_secret":"mKeApaf2UE3CDN8wlh1IJcDSxcJlYlhD"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")

# 设置公开
curl -s -X PATCH "https://open.feishu.cn/open-apis/drive/v1/permissions/{doc_id}/public?type=docx" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"link_share_entity": "anyone_readable"}'
```



## Open Terminal

- **状态**: 运行中（裸机模式，虚拟环境）
- **端口**: 8000
- **API Key**: `ot-2491494aac7c9b92b0099b68fbab3f63`
- **虚拟环境**: `/root/.openclaw/workspace/venvs/open-terminal`
- **启动命令**: `source /root/.openclaw/workspace/venvs/open-terminal/bin/activate && open-terminal run --host 0.0.0.0 --port 8000 --api-key <key>`
- **API文档**: http://localhost:8000/docs
- **注意**: 裸机模式无沙箱，root权限运行

## TurboQuant（KV Cache 量化算法）
- **位置**: `/root/.openclaw/workspace/TurboQuant/`
- **文件**: `turboquant_demo.py`（算法实现 + 测试套件）
- **依赖**: numpy only
- **用途**: LLM KV Cache 量化压缩，极坐标量化 + QJL 残差纠错
- **调用**: `python3 /root/.openclaw/workspace/TurboQuant/turboquant_demo.py`
- **核心 API**:
  - `block_quantize(block, bits)` — 传统均匀块量化
  - `polar_quantize_pair(x, y, bits)` — 极坐标量化（零开销）
  - `turbo_compress(k, bits, S)` — 完整 TurboQuant 压缩
  - `turbo_score(q, kp, sketch, norm_res, S)` — 推断端打分
- **适用场景**: KV Cache 压缩、注意力分数近似计算、d≤64 小维度效果最佳
- **配置参考**: d=128 推荐 PolarQuant 3-bit（10.7x 压缩）或 TurboQuant m=256（6.4x 压缩，接近传统精度）
