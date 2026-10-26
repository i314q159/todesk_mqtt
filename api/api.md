# api

## dev_id

```toml
# 扫地车
dev_id = "qsc_001"

# 洗涤车
dev_id = "xdc_002"
```

## 服务器下发机器人

cmd/device/qsc_001/todesk

seq 每次需要不一样，一样的会被丢弃

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

seq 重复

```json
{
"seq": 1001,
"action": "restart_todesk",
"status": "rejected",
"reason": "duplicate",
}
```

冷却拦截

多个不同的 seq 发来，5 秒冷静期，用于todeskd重启的时间

```json
{
    "seq": 1001,
    "action": "restart_todesk",
    "status": "rejected",
    "reason": "cooldown"
}
```
