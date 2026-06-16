from fastapi import APIRouter, Query
from typing import Optional
from app.services.modbus_service import (
    read_registers,
    get_device_status,
    get_calendar_data,
    get_records_by_date,
    add_inspection_record
)
from app.models.schemas import CalendarResponse, InspectionRecord

router = APIRouter()

@router.get("/modbus/devices")
def list_devices():
    return get_device_status()

@router.get("/modbus/read/{device_id}/{address}/{count}")
def read_holding(device_id: str, address: int, count: int = 1):
    """Read holding registers from a Modbus device."""
    return read_registers(device_id, address, count)

@router.post("/modbus/write/{device_id}/{address}")
def write_register(device_id: str, address: int, value: int):
    return {"device_id": device_id, "address": address, "value": value, "status": "written"}

@router.get("/inspection/calendar", response_model=CalendarResponse)
def inspection_calendar(
    year: int = Query(..., description="年份，如 2025"),
    month: int = Query(..., ge=1, le=12, description="月份，1-12")
):
    """获取指定年月的设备巡检日历数据"""
    return get_calendar_data(year, month)

@router.get("/inspection/records/{date_str}")
def inspection_records_by_date(date_str: str):
    """按日期获取设备巡检记录，日期格式 YYYY-MM-DD"""
    return get_records_by_date(date_str)

@router.post("/inspection/record", response_model=InspectionRecord)
def create_inspection_record(
    record_type: str = Query(..., pattern="^(offline|overlimit|acknowledged)$"),
    device_id: str = Query(...),
    message: str = Query(...),
    level: Optional[str] = Query(None, pattern="^(info|warning|critical)$")
):
    """新增设备巡检记录"""
    return add_inspection_record(record_type, device_id, message, level)
