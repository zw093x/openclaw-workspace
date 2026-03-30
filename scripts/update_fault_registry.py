#!/usr/bin/env python3
"""
Cron 故障知识库更新脚本
将今天发现的所有故障模式、根因、修复方案写入自愈系统
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
REGISTRY = WORKSPACE / "scripts" / "self_heal_registry.json"
ERROR_LOG = WORKSPACE / "memory" / "cron-error-log.jsonl"

# === 新增故障模式 ===
NEW_FIXES = {
    "cron_channel_missing": {
        "pattern": "Channel is required when multiple channels are configured",
        "fix_action": "reapply_delivery_config",
        "description": "多渠道配置后 cron 投递 channel 解析失败",
        "cli_fix": "openclaw cron edit <job_id> --channel feishu --to <target> --announce",
        "root_cause": "OpenClaw 配置 lightclawbot+飞书双渠道后，cron delivery 的 channel 字段未被正确解析",
        "auto_fix": True,
        "prevention": "新建 cron 任务时必须指定 --channel feishu --to <open_id>",
        "first_seen": "2026-03-29T07:30:00+08:00",
        "last_seen": "2026-03-30T08:25:00+08:00"
    },
    "cron_feishu_target_format": {
        "pattern": "Delivering to Feishu requires target",
        "fix_action": "reapply_delivery_config",
        "description": "飞书投递目标格式不正确",
        "cli_fix": "openclaw cron edit <job_id> --channel feishu --to <open_id> --announce",
        "root_cause": "飞书投递需要 user:open_id 格式，但实际配置格式不匹配",
        "auto_fix": True,
        "prevention": "飞书目标统一使用 open_id（如 ou_xxx）",
        "first_seen": "2026-03-29T22:00:00+08:00",
        "last_seen": "2026-03-30T08:25:00+08:00"
    },
    "cron_message_failed_transient": {
        "pattern": "Message failed",
        "fix_action": "retry_cron_job",
        "description": "消息投递瞬态错误（消息实际已送达）",
        "cli_fix": "openclaw cron run <job_id>",
        "root_cause": "投递确认阶段竞态条件，消息已发出但返回错误状态",
        "auto_fix": True,
        "prevention": "消息发送后检查 delivered 状态，忽略 status=error 但 delivered=true 的情况",
        "first_seen": "2026-03-30T07:30:00+08:00",
        "last_seen": "2026-03-30T07:30:00+08:00"
    },
    "cron_timeout": {
        "pattern": "timed out",
        "fix_action": "increase_timeout_or_optimize",
        "description": "任务执行超时",
        "cli_fix": "openclaw cron edit <job_id> --timeout-seconds <n>",
        "root_cause": "任务内容过多或网络请求超时",
        "auto_fix": False,
        "prevention": "设置合理的 timeout（搜索类任务建议 300s，简单任务 60s）",
        "first_seen": "2026-03-30T00:00:00+08:00",
        "last_seen": "2026-03-30T07:21:00+08:00"
    },
    "cron_duplicate_delivery": {
        "pattern": "重复推送",
        "fix_action": "check_dual_trigger",
        "description": "同一任务被 OpenClaw cron 和系统 crontab 同时触发",
        "cli_fix": "1. openclaw cron edit <job_id> --no-deliver  2. 确保系统 crontab 不与 OpenClaw cron 时间重叠",
        "root_cause": "配置卡片投递时，系统 crontab wrapper 和 OpenClaw cron 同时触发了同一任务",
        "auto_fix": True,
        "prevention": "卡片投递任务必须设置 --no-deliver，由系统 crontab 统一投递",
        "first_seen": "2026-03-30T09:16:00+08:00",
        "last_seen": "2026-03-30T09:23:00+08:00"
    },
    "cron_card_json_garbled": {
        "pattern": "乱码\\{\"header",
        "fix_action": "fix_card_format",
        "description": "agent 输出 JSON 卡片格式但以文本投递导致乱码",
        "cli_fix": "1. 去掉 prompt 中的 JSON 卡片输出指令  2. 改用 feishu_card_send.py 脚本投递",
        "root_cause": "cron agent 输出 JSON 但 delivery 系统以文本发送，飞书显示原始 JSON",
        "auto_fix": True,
        "prevention": "不要让 cron agent 输出 JSON 卡片格式，使用 cron_card_wrapper.py 统一处理",
        "first_seen": "2026-03-30T08:46:00+08:00",
        "last_seen": "2026-03-30T08:46:00+08:00"
    },
    "cron_agent_no_tool_call": {
        "pattern": "agent 不调用工具",
        "fix_action": "inject_data_to_prompt",
        "description": "mimo-v2-pro 在 cron 隔离会话中不调用 exec/read/web_search 工具",
        "cli_fix": "将数据预注入到 prompt 中（如天气数据），而非让 agent 自行获取",
        "root_cause": "mimo-v2-pro 模型在 isolated session 中工具调用能力不可靠",
        "auto_fix": False,
        "prevention": "1. 外部数据通过 weather_preload.py 预注入到 prompt  2. 不依赖 cron agent 调用工具  3. 复杂操作用系统 crontab 脚本处理",
        "first_seen": "2026-03-30T09:00:00+08:00",
        "last_seen": "2026-03-30T09:12:00+08:00"
    }
}


def main():
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    
    # Update registry
    with open(REGISTRY, "r") as f:
        registry = json.load(f)
    
    # Merge new fixes
    for key, fix in NEW_FIXES.items():
        if key in registry.get("fixes", {}):
            # Update existing
            registry["fixes"][key].update(fix)
        else:
            registry["fixes"][key] = fix
            registry["fixes"][key]["first_seen"] = now
    
    # Update stats
    registry["stats"]["last_comprehensive_update"] = now
    registry["stats"]["known_fix_patterns"] = len(registry.get("fixes", {}))
    
    with open(REGISTRY, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"✅ 自愈注册表已更新：{len(NEW_FIXES)} 个故障模式")
    
    # Write error log
    log_entry = {
        "timestamp": now,
        "event": "comprehensive_fault_logging",
        "total_fixes_added": len(NEW_FIXES),
        "fixes": list(NEW_FIXES.keys())
    }
    with open(ERROR_LOG, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    print(f"✅ 错误日志已追加")


if __name__ == "__main__":
    main()
