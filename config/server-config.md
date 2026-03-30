# 服务器配置文档
*自动生成: 2026-03-30*

## 服务器信息
- **IP**: 42.193.183.176（腾讯云轻量应用）
- **OS**: Ubuntu (Linux 6.8.0-101-generic x64)
- **SSH**: 端口 22, 用户 ubuntu

## Docker
- **版本**: Docker CE 29.3.1 + Compose v5.1.1
- **镜像加速**: docker.1ms.run
- **代理**: 127.0.0.1:7890

### 容器
| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| Open Terminal | ghcr.nju.edu.cn/open-webui/open-terminal:main | 8081→8000 | Web终端API |

## 代理 (mihomo)
- **状态**: systemd, enabled
- **端口**: 127.0.0.1:7890 (HTTP + SOCKS5)
- **配置**: /etc/mihomo/config.yaml
- **节点**: 16个 Trojan 节点

## 系统服务
| 服务 | 端口 | 管理命令 |
|------|------|---------|
| ttyd | 8082 | systemctl status/start/stop/restart ttyd |
| mihomo | 7890 | systemctl status/restart mihomo |

## OpenClaw
- **安装**: pnpm global
- **插件**: @larksuite/openclaw-lark
- **Gateway**: openclaw gateway start/stop/restart

## 飞书配置
- **App ID**: cli_a948...
- **渠道**: WebSocket 模式
- **目标用户**: ou_a6469ccc2902a590994b6777b9c8ae8f

## 恢复步骤
```bash
# 1. 克隆 workspace
git clone https://gitee.com/zw093x/openclaw-workspace.git ~/.openclaw/workspace

# 2. 安装 OpenClaw
npm install -g openclaw
npx @larksuite/openclaw-lark

# 3. 启动 gateway（需扫码授权飞书）
openclaw gateway start

# 4. 导入 cron 任务
# config/cron-jobs-export.json 中有完整任务定义

# 5. 恢复系统 crontab
crontab config/system-crontab-backup.txt

# 6. 恢复代理
# 安装 mihomo + 导入 /etc/mihomo/config.yaml

# 7. 恢复 Docker 服务
# 按 server-config.md 中的表格重建容器
```
