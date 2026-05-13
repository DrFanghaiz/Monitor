/** Unified ECharts dark theme — derived from design tokens. */

const CYAN = '#38BDF8'
const BLUE = '#4F8CF7'
const GREEN = '#22C55E'
const RED = '#EF4444'
const AMBER = '#F59E0B'
const PURPLE = '#8B5CF6'
const MUTED = '#556278'
const BORDER = '#233048'
const TEXT = '#8FA0B8'
const BG = '#0D1320'

export { TEXT }
export const CHART_COLORS = [CYAN, BLUE, GREEN, AMBER, PURPLE, RED, '#EC4899', '#14B8A6', '#6366F1', '#F97316']

export const chartTheme = {
  color: CHART_COLORS,
  backgroundColor: 'transparent',
  textStyle: { color: TEXT, fontFamily: 'Inter, PingFang SC, Microsoft YaHei, sans-serif' },
  title: { textStyle: { color: '#EDF2F9', fontWeight: 600, fontSize: 14 } },
  legend: { textStyle: { color: TEXT, fontSize: 12 }, itemGap: 16 },
  tooltip: {
    backgroundColor: '#131C2E',
    borderColor: BORDER,
    textStyle: { color: '#EDF2F9', fontSize: 12 },
    extraCssText: 'border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.48);',
  },
  grid: { top: 40, right: 24, bottom: 36, left: 48, containLabel: true },
  xAxis: {
    axisLine: { lineStyle: { color: BORDER } },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { show: false },
  },
  yAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { lineStyle: { color: '#192438', type: 'dashed' as const } },
  },
  bar: {
    itemStyle: { borderRadius: [4, 4, 0, 0] },
    barWidth: '60%',
  },
  line: {
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2.5 },
    itemStyle: { borderWidth: 2, borderColor: BG },
  },
  pie: {
    radius: ['55%', '78%'],
    itemStyle: { borderColor: BG, borderWidth: 2 },
    label: { color: TEXT, fontSize: 11 },
  },
}

export function chartOption(base: Record<string, unknown>): Record<string, unknown> {
  return { ...chartTheme, ...base }
}
