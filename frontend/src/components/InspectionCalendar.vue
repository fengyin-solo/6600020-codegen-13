<template>
  <div class="bg-gray-900 rounded-xl p-4 h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-200">设备巡检日历</h3>
      <div class="flex items-center gap-2">
        <button @click="prevMonth" class="w-7 h-7 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white flex items-center justify-center text-xs transition">
          ‹
        </button>
        <span class="text-sm text-orange-400 font-semibold min-w-[110px] text-center">
          {{ currentYear }}年{{ currentMonth + 1 }}月
        </span>
        <button @click="nextMonth" class="w-7 h-7 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white flex items-center justify-center text-xs transition">
          ›
        </button>
        <button @click="goToday" class="px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white text-xs transition ml-1">
          今天
        </button>
      </div>
    </div>

    <div class="flex items-center gap-4 mb-3 text-xs">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-red-500/80 inline-block"></span>
        <span class="text-gray-400">离线</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-yellow-500/80 inline-block"></span>
        <span class="text-gray-400">超限</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-blue-500/80 inline-block"></span>
        <span class="text-gray-400">人工确认</span>
      </div>
    </div>

    <div class="grid grid-cols-7 gap-1 mb-1">
      <div v-for="w in weekdays" :key="w" class="text-center text-xs text-gray-500 py-1 font-medium">
        {{ w }}
      </div>
    </div>

    <div class="grid grid-cols-7 gap-1 flex-1 content-start">
      <div
        v-for="(day, idx) in calendarData"
        :key="idx"
        @click="selectDay(day)"
        class="relative rounded-lg p-1.5 cursor-pointer transition-all min-h-[62px] border"
        :class="getDayClass(day)"
      >
        <div class="flex items-start justify-between">
          <span class="text-xs font-medium" :class="isCurrentMonth(day) ? (isToday(day) ? 'text-orange-400' : 'text-gray-200') : 'text-gray-600'">
            {{ getDayNum(day.date) }}
          </span>
          <span v-if="isToday(day)" class="text-[9px] bg-orange-500 text-white px-1 rounded">今</span>
        </div>
        <div class="mt-1 space-y-0.5">
          <div v-if="day.offlineCount > 0" class="flex items-center gap-1 text-[10px]">
            <span class="w-1.5 h-1.5 rounded-full bg-red-500 inline-block flex-shrink-0"></span>
            <span class="text-red-400 truncate">{{ day.offlineCount }}</span>
          </div>
          <div v-if="day.overlimitCount > 0" class="flex items-center gap-1 text-[10px]">
            <span class="w-1.5 h-1.5 rounded-full bg-yellow-500 inline-block flex-shrink-0"></span>
            <span class="text-yellow-400 truncate">{{ day.overlimitCount }}</span>
          </div>
          <div v-if="day.acknowledgedCount > 0" class="flex items-center gap-1 text-[10px]">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block flex-shrink-0"></span>
            <span class="text-blue-400 truncate">{{ day.acknowledgedCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedDay" class="mt-4 border-t border-gray-800 pt-3">
      <div class="flex items-center justify-between mb-2">
        <h4 class="text-sm text-gray-300 font-medium">
          {{ selectedDay.date }} 巡检记录
          <span class="text-xs text-gray-500 ml-2">
            共 {{ selectedDay.records.length }} 条
          </span>
        </h4>
        <div class="flex gap-1">
          <button
            v-for="f in filters"
            :key="f.key"
            @click="toggleFilter(f.key)"
            class="px-2 py-0.5 rounded text-[10px] transition border"
            :class="activeFilters.includes(f.key) ? f.activeClass : 'bg-gray-800 text-gray-500 border-gray-700 hover:border-gray-600'"
          >
            {{ f.label }}
          </button>
        </div>
      </div>
      <div class="max-h-[180px] overflow-y-auto space-y-1 pr-1">
        <div v-if="filteredRecords.length === 0" class="text-center text-xs text-gray-600 py-4">
          当日无符合条件的巡检记录
        </div>
        <div
          v-for="r in filteredRecords"
          :key="r.id"
          class="flex items-start gap-2 p-2 rounded-lg bg-gray-800/60 text-xs border-l-2"
          :class="getRecordBorderClass(r)"
        >
          <span class="mt-0.5 flex-shrink-0" :class="getRecordIconClass(r.type)">
            {{ getRecordIcon(r.type) }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="text-gray-200 truncate">{{ r.message }}</div>
            <div class="flex items-center gap-2 mt-0.5">
              <span class="text-gray-500">{{ formatTime(r.timestamp) }}</span>
              <span class="text-gray-600">|</span>
              <span class="text-gray-500">{{ r.deviceName }}</span>
              <span v-if="r.level" class="px-1 rounded text-[9px]" :class="getLevelClass(r.level)">
                {{ getLevelText(r.level) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useModbusStore } from '../store/modbus'
import type { DayInspection, InspectionRecord, InspectionRecordType } from '../types'

const store = useModbusStore()

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth())
const selectedDay = ref<DayInspection | null>(null)
const activeFilters = ref<InspectionRecordType[]>(['offline', 'overlimit', 'acknowledged'])

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const filters = [
  { key: 'offline' as InspectionRecordType, label: '离线', activeClass: 'bg-red-500/20 text-red-400 border-red-500/40' },
  { key: 'overlimit' as InspectionRecordType, label: '超限', activeClass: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' },
  { key: 'acknowledged' as InspectionRecordType, label: '确认', activeClass: 'bg-blue-500/20 text-blue-400 border-blue-500/40' }
]

const calendarData = computed(() => store.getCalendarData(currentYear.value, currentMonth.value))

const todayStr = computed(() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})

const filteredRecords = computed(() => {
  if (!selectedDay.value) return []
  return selectedDay.value.records.filter(r => activeFilters.value.includes(r.type))
})

watch([currentYear, currentMonth], () => {
  selectedDay.value = null
})

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

async function goToday() {
  const d = new Date()
  currentYear.value = d.getFullYear()
  currentMonth.value = d.getMonth()
  await nextTick()
  const today = calendarData.value.find(day => day.date === todayStr.value)
  if (today) selectedDay.value = today
}

function selectDay(day: DayInspection) {
  selectedDay.value = day
}

function toggleFilter(key: InspectionRecordType) {
  const idx = activeFilters.value.indexOf(key)
  if (idx > -1) {
    if (activeFilters.value.length > 1) activeFilters.value.splice(idx, 1)
  } else {
    activeFilters.value.push(key)
  }
}

function isCurrentMonth(day: DayInspection): boolean {
  const [y, m] = day.date.split('-').map(Number)
  return y === currentYear.value && m === currentMonth.value + 1
}

function isToday(day: DayInspection): boolean {
  return day.date === todayStr.value
}

function getDayNum(dateStr: string): string {
  return String(Number(dateStr.split('-')[2]))
}

function getDayClass(day: DayInspection): string {
  const classes: string[] = []
  const inMonth = isCurrentMonth(day)
  const selected = selectedDay.value?.date === day.date
  const today = isToday(day)

  if (inMonth) classes.push('bg-gray-800/40 hover:bg-gray-800')
  else classes.push('bg-gray-900/40 hover:bg-gray-800/30')

  if (selected) classes.push('ring-1 ring-orange-500 bg-gray-800')
  if (today && !selected) classes.push('ring-1 ring-orange-500/40')
  if (day.offlineCount > 0 || day.overlimitCount > 0 || day.acknowledgedCount > 0) {
    classes.push('border-gray-700')
  } else {
    classes.push('border-gray-800/50')
  }
  return classes.join(' ')
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${h}:${m}:${s}`
}

function getRecordIcon(type: InspectionRecordType): string {
  switch (type) {
    case 'offline': return '⬤'
    case 'overlimit': return '⚠'
    case 'acknowledged': return '✓'
  }
}

function getRecordIconClass(type: InspectionRecordType): string {
  switch (type) {
    case 'offline': return 'text-red-500'
    case 'overlimit': return 'text-yellow-500'
    case 'acknowledged': return 'text-blue-500'
  }
}

function getRecordBorderClass(r: InspectionRecord): string {
  switch (r.type) {
    case 'offline': return 'border-red-500'
    case 'overlimit': return 'border-yellow-500'
    case 'acknowledged': return 'border-blue-500'
  }
}

function getLevelClass(level: string): string {
  switch (level) {
    case 'critical': return 'bg-red-500/30 text-red-400'
    case 'warning': return 'bg-yellow-500/30 text-yellow-400'
    case 'info': return 'bg-blue-500/30 text-blue-400'
    default: return 'bg-gray-500/30 text-gray-400'
  }
}

function getLevelText(level: string): string {
  switch (level) {
    case 'critical': return '严重'
    case 'warning': return '警告'
    case 'info': return '信息'
    default: return level
  }
}
</script>
