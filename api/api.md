# api

## dev_id

```toml
# 主机
dev_id = "qsc_001_master"

# 从机
dev_id = "qsc_001_slave"

# 单主机
dev_id = "qsc_001_single"
```

## 服务器下发机器人

cmd/device/qsc_001/todesk

```json
{
    "seq": 1001,
    "action": "restart_todesk"
}
```

## 机器人上报应答

state/device/qsc_001/todesk

成功触发

```json
{
    "seq": 1001,
    "action": "restart_todesk",
    "status": "triggered"
}
```

冷却拦截

```json
{
    "seq": 1001,
    "action": "restart_todesk",
    "status": "rejected",
    "reason": "cooldown"
}
```
