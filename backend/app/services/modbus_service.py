"""Modbus service with mock data (replace with pymodbus for production)."""
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

MOCK_DEVICES = [
    {"id": "dev1", "name": "温湿度传感器-A区", "ip": "192.168.1.101", "port": 502, "slave_id": 1, "online": True},
    {"id": "dev2", "name": "压力变送器-B区", "ip": "192.168.1.102", "port": 502, "slave_id": 2, "online": True},
    {"id": "dev3", "name": "电机控制器-C区", "ip": "192.168.1.103", "port": 502, "slave_id": 3, "online": False},
    {"id": "dev4", "name": "流量计-D区", "ip": "192.168.1.104", "port": 502, "slave_id": 4, "online": True},
]

_DEVICE_REGISTERS = {
    "dev1": [
        {"address": 0, "name": "温度", "type": "holding", "value": 25.6, "unit": "°C"},
        {"address": 1, "name": "湿度", "type": "holding", "value": 62.3, "unit": "%RH"},
        {"address": 2, "name": "露点", "type": "holding", "value": 17.8, "unit": "°C"},
    ],
    "dev2": [
        {"address": 0, "name": "管道压力", "type": "holding", "value": 3.45, "unit": "MPa"},
        {"address": 1, "name": "差压", "type": "holding", "value": 0.12, "unit": "kPa"},
    ],
    "dev3": [
        {"address": 0, "name": "转速", "type": "holding", "value": 1480, "unit": "RPM"},
        {"address": 1, "name": "电流", "type": "holding", "value": 12.5, "unit": "A"},
        {"address": 2, "name": "运行状态", "type": "coil", "value": True, "unit": ""},
    ],
    "dev4": [
        {"address": 0, "name": "瞬时流量", "type": "holding", "value": 156.7, "unit": "L/min"},
        {"address": 1, "name": "累计流量", "type": "holding", "value": 98234, "unit": "L"},
    ],
}

INSPECTION_RECORDS: List[Dict[str, Any]] = []


def _format_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _generate_inspection_history() -> None:
    global INSPECTION_RECORDS
    if INSPECTION_RECORDS:
        return
    records: List[Dict[str, Any]] = []
    now = datetime.now()
    day_ms = 86400000

    for day_offset in range(30):
        day_start = now - timedelta(days=day_offset)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start_ts = int(day_start.timestamp() * 1000)

        for dev in MOCK_DEVICES:
            offline_chance = 0.15 + random.random() * 0.25
            if day_offset == 0:
                offline_chance = 0.1 if dev["online"] else 0.8
            if random.random() < offline_chance:
                ts = day_start_ts + random.randint(0, day_ms)
                records.append({
                    "id": f"off_{ts}_{dev['id']}",
                    "device_id": dev["id"],
                    "device_name": dev["name"],
                    "type": "offline",
                    "message": f"{dev['name']} 设备离线",
                    "timestamp": ts,
                    "level": "warning"
                })

            overlimit_chance = 0.2 + random.random() * 0.3
            if random.random() < overlimit_chance:
                count = 1 + random.randint(0, 2)
                regs = _DEVICE_REGISTERS.get(dev["id"], [])
                for i in range(count):
                    ts = day_start_ts + random.randint(0, day_ms)
                    reg = regs[random.randint(0, len(regs) - 1)] if regs else {"name": "寄存器"}
                    is_critical = random.random() > 0.6
                    records.append({
                        "id": f"ovl_{ts}_{dev['id']}_{i}",
                        "device_id": dev["id"],
                        "device_name": dev["name"],
                        "type": "overlimit",
                        "message": f"{dev['name']} {reg['name']}超限告警",
                        "timestamp": ts,
                        "level": "critical" if is_critical else "warning"
                    })

            ack_chance = 0.3 + random.random() * 0.4
            if random.random() < ack_chance:
                ts = day_start_ts + random.randint(0, day_ms)
                records.append({
                    "id": f"ack_{ts}_{dev['id']}",
                    "device_id": dev["id"],
                    "device_name": dev["name"],
                    "type": "acknowledged",
                    "message": f"{dev['name']} 告警已人工确认",
                    "timestamp": ts,
                    "level": "info"
                })

    INSPECTION_RECORDS = sorted(records, key=lambda r: r["timestamp"], reverse=True)


def get_device_status() -> List[Dict[str, Any]]:
    result = []
    for dev in MOCK_DEVICES:
        d = dict(dev)
        d["registers"] = [
            {**r, "value": round(r["value"] + (random.random() - 0.5) * r["value"] * 0.02, 2)}
            if isinstance(r["value"], (int, float)) else r
            for r in _DEVICE_REGISTERS.get(dev["id"], [])
        ]
        result.append(d)
    return result


def read_registers(device_id: str, address: int, count: int) -> Dict[str, Any]:
    """Read registers via pymodbus (mock implementation)."""
    values = [round(random.uniform(0, 100), 2) for _ in range(count)]
    return {"device_id": device_id, "address": address, "values": values}


def get_calendar_data(year: int, month: int) -> Dict[str, Any]:
    _generate_inspection_history()
    result_days: List[Dict[str, Any]] = []

    first_day = datetime(year, month, 1)
    last_day = datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year, 12, 31)
    start_weekday = first_day.weekday() + 1
    if start_weekday == 7:
        start_weekday = 0

    for i in range(start_weekday):
        d = first_day - timedelta(days=start_weekday - i)
        result_days.append({
            "date": _format_date(d),
            "offline_count": 0,
            "overlimit_count": 0,
            "acknowledged_count": 0,
            "records": []
        })

    for day in range(1, last_day.day + 1):
        d = datetime(year, month, day)
        date_str = _format_date(d)
        day_start = int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        day_end = int(d.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)

        day_records = [r for r in INSPECTION_RECORDS if day_start <= r["timestamp"] <= day_end]
        result_days.append({
            "date": date_str,
            "offline_count": sum(1 for r in day_records if r["type"] == "offline"),
            "overlimit_count": sum(1 for r in day_records if r["type"] == "overlimit"),
            "acknowledged_count": sum(1 for r in day_records if r["type"] == "acknowledged"),
            "records": day_records
        })

    remaining = 42 - len(result_days)
    for i in range(1, remaining + 1):
        d = last_day + timedelta(days=i)
        result_days.append({
            "date": _format_date(d),
            "offline_count": 0,
            "overlimit_count": 0,
            "acknowledged_count": 0,
            "records": []
        })

    return {
        "year": year,
        "month": month,
        "days": result_days
    }


def get_records_by_date(date_str: str) -> List[Dict[str, Any]]:
    _generate_inspection_history()
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return []
    day_start = int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    day_end = int(d.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
    return [r for r in INSPECTION_RECORDS if day_start <= r["timestamp"] <= day_end]


def add_inspection_record(
    record_type: str,
    device_id: str,
    message: str,
    level: Optional[str] = None
) -> Dict[str, Any]:
    _generate_inspection_history()
    dev = next((d for d in MOCK_DEVICES if d["id"] == device_id), None)
    ts = int(time.time() * 1000)
    record = {
        "id": f"{record_type}_{ts}_{random.randint(1000, 9999)}",
        "device_id": device_id,
        "device_name": dev["name"] if dev else device_id,
        "type": record_type,
        "message": message,
        "timestamp": ts,
        "level": level
    }
    INSPECTION_RECORDS.insert(0, record)
    if len(INSPECTION_RECORDS) > 500:
        INSPECTION_RECORDS[:] = INSPECTION_RECORDS[:500]
    return record
