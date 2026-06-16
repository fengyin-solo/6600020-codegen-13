from pydantic import BaseModel
from typing import List, Optional, Literal

class ModbusRegister(BaseModel):
    address: int
    name: str
    type: str
    value: float
    unit: str

class Device(BaseModel):
    id: str
    name: str
    ip: str
    port: int
    slave_id: int
    online: bool
    registers: List[ModbusRegister] = []

InspectionRecordType = Literal['offline', 'overlimit', 'acknowledged']
AlarmLevel = Literal['info', 'warning', 'critical']

class InspectionRecord(BaseModel):
    id: str
    device_id: str
    device_name: str
    type: InspectionRecordType
    message: str
    timestamp: int
    level: Optional[AlarmLevel] = None

class DayInspection(BaseModel):
    date: str
    offline_count: int
    overlimit_count: int
    acknowledged_count: int
    records: List[InspectionRecord] = []

class CalendarResponse(BaseModel):
    year: int
    month: int
    days: List[DayInspection]
