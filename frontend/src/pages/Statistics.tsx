import { useState } from 'react'
import { motion } from 'framer-motion'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useUserStats, useHourlyStats, useDailyStats, useDistribution } from '../hooks/useStatistics'
import { Card } from '../components/ui/Card'
import { CHART_COLORS, chartTheme, TEXT } from '../components/charts/chartTheme'
import { fadeInUp, staggerContainer } from '../theme/motion'

echarts.use([BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

type ChartType = 'bar' | 'pie' | 'trend' | 'heatmap'

const CHART_OPTIONS: { value: ChartType; label: string }[] = [
  { value: 'bar', label: '活跃用户' },
  { value: 'pie', label: '使用分布' },
  { value: 'trend', label: '趋势' },
  { value: 'heatmap', label: '热力图' },
]

export function Statistics() {
  const [chart, setChart] = useState<ChartType>('bar')
  const { data: userStats } = useUserStats('all')
  const { data: hourlyStats } = useHourlyStats()
  const { data: dailyStats } = useDailyStats(30)
  const { data: distribution } = useDistribution('all')

  const users = userStats?.users ?? []
  const totalHours = users.reduce((s, u) => s + u.total_seconds / 3600, 0)
  const totalUsers = users.length

  function getChartOption(): Record<string, unknown> {
    switch (chart) {
      case 'bar': {
        const top5 = users.slice(0, 8).reverse()
        return {
          ...chartTheme,
          tooltip: { ...chartTheme.tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
          xAxis: { type: 'value', ...chartTheme.xAxis, axisLabel: { ...chartTheme.xAxis?.axisLabel, formatter: '{value}h' } },
          yAxis: { type: 'category', data: top5.map((u) => u.user_name), ...chartTheme.yAxis, axisLabel: { ...chartTheme.yAxis?.axisLabel, fontSize: 12 } },
          series: [{ type: 'bar', data: top5.map((u) => +(u.total_seconds / 3600).toFixed(1)), color: CHART_COLORS[0] }],
        }
      }
      case 'pie': {
        const dist = distribution?.distribution ?? []
        const data = dist.slice(0, 8).map((d, i) => ({ name: d.user_name, value: +(d.total_seconds / 3600).toFixed(1), itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] } }))
        return { ...chartTheme, series: [{ type: 'pie', data, ...chartTheme.pie }] }
      }
      case 'trend': {
        const daily = dailyStats?.daily ?? []
        return {
          ...chartTheme,
          tooltip: { ...chartTheme.tooltip, trigger: 'axis' },
          xAxis: { type: 'category', data: daily.map((d) => d.date.slice(5)), ...chartTheme.xAxis },
          yAxis: [
            { type: 'value', name: '小时', ...chartTheme.yAxis, axisLabel: { ...chartTheme.yAxis?.axisLabel } },
            { type: 'value', name: '用户', ...chartTheme.yAxis, axisLabel: { ...chartTheme.yAxis?.axisLabel } },
          ],
          series: [
            { name: '使用时长', type: 'line', data: daily.map((d) => +d.hours.toFixed(1)), smooth: true, areaStyle: { opacity: 0.1 }, color: CHART_COLORS[0] },
            { name: '用户数', type: 'line', yAxisIndex: 1, data: daily.map((d) => d.users), smooth: true, lineStyle: { type: 'dashed' }, color: CHART_COLORS[3] },
          ],
        }
      }
      case 'heatmap': {
        const hourly = hourlyStats?.hourly ?? []
        const dates = [...new Set(hourly.map((h) => h.date))].sort().slice(-21)
        const hours = Array.from({ length: 24 }, (_, i) => i)
        const matrix = hours.map((h) => dates.map((d) => {
          const found = hourly.find((r) => r.date === d && r.hour === h)
          return found ? +found.hours.toFixed(2) : 0
        }))
        return {
          ...chartTheme,
          tooltip: { ...chartTheme.tooltip, trigger: 'item' },
          xAxis: { type: 'category', data: dates.map((d) => d.slice(5)), ...chartTheme.xAxis },
          yAxis: { type: 'category', data: hours.map((h) => `${h}:00`), ...chartTheme.yAxis, axisLabel: { ...chartTheme.yAxis?.axisLabel, fontSize: 10 } },
          visualMap: { min: 0, max: Math.max(...matrix.flat(), 1), calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#0D1320', '#164E63', '#0E7490', '#22D3EE'] }, textStyle: { color: TEXT } },
          series: [{ type: 'heatmap', data: matrix.flatMap((row, yi) => row.map((v, xi) => [xi, yi, v])), label: { show: false } }],
        }
      }
      default:
        return {}
    }
  }

  return (
    <motion.div className="space-y-6" variants={staggerContainer} initial="hidden" animate="visible">
      <motion.div variants={fadeInUp}>
        <h1 className="text-2xl font-bold text-primary tracking-tight font-display">数据统计</h1>
      </motion.div>

      {/* KPI cards */}
      <motion.div variants={fadeInUp} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card><div className="text-xs text-muted uppercase tracking-wider mb-2">总用户数</div><div className="text-2xl font-bold text-primary tabular-nums font-display">{totalUsers}</div></Card>
        <Card><div className="text-xs text-muted uppercase tracking-wider mb-2">总使用时长</div><div className="text-2xl font-bold text-primary tabular-nums font-display">{totalHours.toFixed(1)}<span className="text-sm text-muted ml-1">h</span></div></Card>
        <Card><div className="text-xs text-muted uppercase tracking-wider mb-2">人均使用</div><div className="text-2xl font-bold text-primary tabular-nums font-display">{totalUsers ? (totalHours / totalUsers).toFixed(1) : '0'}<span className="text-sm text-muted ml-1">h</span></div></Card>
      </motion.div>

      {/* Chart area */}
      <motion.div variants={fadeInUp}>
        <Card>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider font-display">图表分析</h2>
            <div className="flex gap-1 bg-surface rounded-lg p-1">
              {CHART_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setChart(opt.value)}
                  className={`px-3.5 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
                    chart === opt.value
                      ? 'bg-accent-cyan/15 text-accent-cyan'
                      : 'text-muted hover:text-secondary'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <ReactEChartsCore echarts={echarts} option={getChartOption()} style={{ height: 380 }} notMerge />
        </Card>
      </motion.div>
    </motion.div>
  )
}
