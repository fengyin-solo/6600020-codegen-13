import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Device, Alarm, ModbusRegister, InspectionRecord, DayInspection, InspectionRecordType } from '../types'

export const useModbusStore = defineStore('modbus', () => {
  const devices = ref<Device[]>([])
  const alarms = ref<Alarm[]>([])
  const historyData = ref<Record<string, { time: number[]; values: number[] }>>({})
  const isPolling = ref(false)
  const pollInterval = ref(1000)
  const selectedDevice = ref<Device | null>(null)
  const inspectionRecords = ref<InspectionRecord[]>([])

  const criticalAlarms = computed(() => alarms.value.filter(a => a.level === 'critical' && !a.acknowledged))
  const onlineDevices = computed(() => devices.value.filter(d => d.online))

  function formatDate(d: Date): string {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  function initMockDevices() {
    devices.value = [
      {
        id: 'dev1', name: '温湿度传感器-A区', ip: '192.168.1.101', port: 502, slaveId: 1, online: true,
        registers: [
          { address: 0, name: '温度', type: 'holding', value: 25.6, unit: '°C', updatedAt: Date.now() },
          { address: 1, name: '湿度', type: 'holding', value: 62.3, unit: '%RH', updatedAt: Date.now() },
          { address: 2, name: '露点', type: 'holding', value: 17.8, unit: '°C', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev2', name: '压力变送器-B区', ip: '192.168.1.102', port: 502, slaveId: 2, online: true,
        registers: [
          { address: 0, name: '管道压力', type: 'holding', value: 3.45, unit: 'MPa', updatedAt: Date.now() },
          { address: 1, name: '差压', type: 'holding', value: 0.12, unit: 'kPa', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev3', name: '电机控制器-C区', ip: '192.168.1.103', port: 502, slaveId: 3, online: false,
        registers: [
          { address: 0, name: '转速', type: 'holding', value: 1480, unit: 'RPM', updatedAt: Date.now() },
          { address: 1, name: '电流', type: 'holding', value: 12.5, unit: 'A', updatedAt: Date.now() },
          { address: 2, name: '运行状态', type: 'coil', value: true, unit: '', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev4', name: '流量计-D区', ip: '192.168.1.104', port: 502, slaveId: 4, online: true,
        registers: [
          { address: 0, name: '瞬时流量', type: 'holding', value: 156.7, unit: 'L/min', updatedAt: Date.now() },
          { address: 1, name: '累计流量', type: 'holding', value: 98234, unit: 'L', updatedAt: Date.now() },
        ]
      },
    ]
    selectedDevice.value = devices.value[0]
    generateInspectionHistory()
  }

  function generateInspectionHistory() {
    const records: InspectionRecord[] = []
    const now = Date.now()
    const dayMs = 86400000

    for (let dayOffset = 0; dayOffset < 30; dayOffset++) {
      const dayStart = new Date(now - dayOffset * dayMs)
      dayStart.setHours(0, 0, 0, 0)
      const dayStartTime = dayStart.getTime()

      for (const dev of devices.value) {
        const offlineChance = dayOffset === 0 ? (dev.online ? 0.1 : 0.8) : 0.15 + Math.random() * 0.25
        if (Math.random() < offlineChance) {
          const ts = dayStartTime + Math.floor(Math.random() * dayMs)
          records.push({
            id: `off_${ts}_${dev.id}`,
            deviceId: dev.id,
            deviceName: dev.name,
            type: 'offline',
            message: `${dev.name} 设备离线`,
            timestamp: ts,
            level: 'warning'
          })
        }

        const overlimitChance = 0.2 + Math.random() * 0.3
        if (Math.random() < overlimitChance) {
          const count = 1 + Math.floor(Math.random() * 3)
          for (let i = 0; i < count; i++) {
            const ts = dayStartTime + Math.floor(Math.random() * dayMs)
            const reg = dev.registers[Math.floor(Math.random() * dev.registers.length)]
            const isCritical = Math.random() > 0.6
            records.push({
              id: `ovl_${ts}_${dev.id}_${i}`,
              deviceId: dev.id,
              deviceName: dev.name,
              type: 'overlimit',
              message: `${dev.name} ${reg.name}超限告警`,
              timestamp: ts,
              level: isCritical ? 'critical' : 'warning'
            })
          }
        }

        const ackChance = 0.3 + Math.random() * 0.4
        if (Math.random() < ackChance) {
          const ts = dayStartTime + Math.floor(Math.random() * dayMs)
          records.push({
            id: `ack_${ts}_${dev.id}`,
            deviceId: dev.id,
            deviceName: dev.name,
            type: 'acknowledged',
            message: `${dev.name} 告警已人工确认`,
            timestamp: ts,
            level: 'info'
          })
        }
      }
    }
    inspectionRecords.value = records.sort((a, b) => b.timestamp - a.timestamp)
  }

  function addInspectionRecord(type: InspectionRecordType, deviceId: string, message: string, level?: 'info' | 'warning' | 'critical') {
    const dev = devices.value.find(d => d.id === deviceId)
    const record: InspectionRecord = {
      id: `${type}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      deviceId,
      deviceName: dev?.name || deviceId,
      type,
      message,
      timestamp: Date.now(),
      level
    }
    inspectionRecords.value.unshift(record)
    if (inspectionRecords.value.length > 500) {
      inspectionRecords.value = inspectionRecords.value.slice(0, 500)
    }
  }

  function getCalendarData(year: number, month: number): DayInspection[] {
    const result: DayInspection[] = []
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startWeekday = firstDay.getDay()

    for (let i = 0; i < startWeekday; i++) {
      const d = new Date(year, month, -startWeekday + i + 1)
      result.push({ date: formatDate(d), offlineCount: 0, overlimitCount: 0, acknowledgedCount: 0, records: [] })
    }

    for (let day = 1; day <= lastDay.getDate(); day++) {
      const d = new Date(year, month, day)
      const dateStr = formatDate(d)
      const dayStart = d.setHours(0, 0, 0, 0)
      const dayEnd = d.setHours(23, 59, 59, 999)

      const dayRecords = inspectionRecords.value.filter(r => r.timestamp >= dayStart && r.timestamp <= dayEnd)
      result.push({
        date: dateStr,
        offlineCount: dayRecords.filter(r => r.type === 'offline').length,
        overlimitCount: dayRecords.filter(r => r.type === 'overlimit').length,
        acknowledgedCount: dayRecords.filter(r => r.type === 'acknowledged').length,
        records: dayRecords
      })
    }

    const remaining = 42 - result.length
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i)
      result.push({ date: formatDate(d), offlineCount: 0, overlimitCount: 0, acknowledgedCount: 0, records: [] })
    }

    return result
  }

  function getRecordsByDate(dateStr: string): InspectionRecord[] {
    const [y, m, d] = dateStr.split('-').map(Number)
    const date = new Date(y, m - 1, d)
    const dayStart = date.setHours(0, 0, 0, 0)
    const dayEnd = date.setHours(23, 59, 59, 999)
    return inspectionRecords.value.filter(r => r.timestamp >= dayStart && r.timestamp <= dayEnd)
  }

  function simulatePoll() {
    for (const dev of devices.value) {
      if (!dev.online) continue
      for (const reg of dev.registers) {
        if (typeof reg.value === 'number') {
          const noise = (Math.random() - 0.5) * reg.value * 0.02
          reg.value = Math.round((reg.value + noise) * 100) / 100
          reg.updatedAt = Date.now()
          const key = `${dev.id}_${reg.address}`
          if (!historyData.value[key]) historyData.value[key] = { time: [], values: [] }
          historyData.value[key].time.push(Date.now())
          historyData.value[key].values.push(reg.value)
          if (historyData.value[key].time.length > 100) {
            historyData.value[key].time.shift()
            historyData.value[key].values.shift()
          }
          if (reg.name === '温度' && reg.value > 28) {
            const isCritical = reg.value > 30
            alarms.value.unshift({
              id: `a_${Date.now()}`, deviceId: dev.id, register: reg.name,
              message: `${dev.name} ${reg.name}超限: ${reg.value}${reg.unit}`,
              level: isCritical ? 'critical' : 'warning',
              timestamp: Date.now(), acknowledged: false
            })
            addInspectionRecord('overlimit', dev.id, `${dev.name} ${reg.name}超限: ${reg.value}${reg.unit}`, isCritical ? 'critical' : 'warning')
          }
        }
      }
    }
    if (alarms.value.length > 50) alarms.value = alarms.value.slice(0, 50)
  }

  function acknowledgeAlarm(id: string) {
    const a = alarms.value.find(a => a.id === id)
    if (a) {
      a.acknowledged = true
      const dev = devices.value.find(d => d.id === a.deviceId)
      addInspectionRecord('acknowledged', a.deviceId, `${dev?.name || a.deviceId} 告警已人工确认: ${a.message}`, 'info')
    }
  }

  function toggleDevice(id: string) {
    const d = devices.value.find(d => d.id === id)
    if (d) {
      const wasOnline = d.online
      d.online = !d.online
      if (wasOnline && !d.online) {
        addInspectionRecord('offline', d.id, `${d.name} 设备离线`, 'warning')
      } else if (!wasOnline && d.online) {
        addInspectionRecord('acknowledged', d.id, `${d.name} 设备恢复在线`, 'info')
      }
    }
  }

  return {
    devices, alarms, historyData, isPolling, pollInterval, selectedDevice, inspectionRecords,
    criticalAlarms, onlineDevices,
    initMockDevices, simulatePoll, acknowledgeAlarm, toggleDevice,
    getCalendarData, getRecordsByDate, addInspectionRecord
  }
})
