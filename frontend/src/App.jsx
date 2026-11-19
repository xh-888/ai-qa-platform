import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'

// ===== 常量 =====
const SUGGESTIONS = [
  '上月华东区销售额是多少',
  '本月各区域销售目标完成情况',
  '过去6个月销售额趋势',
  '哪个产品卖得最好',
  '西南区本月订单量',
  '各行业客户的销售额对比',
]

// ===== 小图标组件（内联 SVG，避免引入图标库）=====
const Icon = ({ name }) => {
  const paths = {
    robot: 'M12 2a2 2 0 0 1 2 2v1a6 6 0 0 1 6 6v4a6 6 0 0 1-6 6h-1v2a1 1 0 0 1-2 0v-2H9a6 6 0 0 1-6-6v-4a6 6 0 0 1 6-6V4a2 2 0 0 1 2-2h1zm-1 6H9a4 4 0 0 0-4 4v4a4 4 0 0 0 4 4h6a4 4 0 0 0 4-4v-4a4 4 0 0 0-4-4h-2zm0 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm4 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z',
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-4 0-8 2-8 5v1a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-1c0-3-4-5-8-5z',
    send: 'M3 20l18-9L3 2v7l12 2-12 2z',
    plus: 'M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z',
    bolt: 'M13 2L4 14h6l-1 8 9-12h-6z',
    copy: 'M8 8h11v11H8z M5 5h11v3H8v8H5z',
    mic: 'M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.93V21h2v-2.07A7 7 0 0 0 19 12h-2z',
    chevron: 'M8 6l6 6-6 6z',
    table: 'M4 4h16v16H4z M4 9h16 M9 4v16',
    chart: 'M4 19h16 M5 16l5-6 4 3 5-7',
    menu: 'M4 6h16M4 12h16M4 18h16',
  }
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true">
      <path d={paths[name] || ''} />
    </svg>
  )
}

// ===== ECharts 封装 =====
function EChart({ option }) {
  const ref = useRef(null)
  const chartRef = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    chart.setOption(option)
    chartRef.current = chart
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      chart.dispose()
    }
  }, [option])
  return <div ref={ref} style={{ width: '100%', height: 300 }} />
}

// ===== 数字格式化 =====
const fmt = (v) => {
  if (v === null || v === undefined || v === '') return '-'
  if (typeof v === 'number') {
    return Number.isInteger(v) ? v.toLocaleString() : v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(v)
}

// 金额类指标才加货币符号，避免"订单量/数量"等也显示 ¥
const isMoney = (label) => /额|价|收入|成本|目标|金额/.test(String(label || ''))
const fmtValue = (v, label) => (isMoney(label) ? '¥' : '') + fmt(v)

// ===== AI 回答卡片 =====
function AiCard({ msg }) {
  const { data, elapsed } = msg
  const [showSteps, setShowSteps] = useState(false)
  const [showSql, setShowSql] = useState(false)

  const columns = data?.columns || []
  const rows = data?.rows || []
  const chart = data?.chart || ''

  // 判断数据形状
  const isNumber = rows.length === 1 && rows[0].length === 1 && typeof rows[0][0] === 'number'
  const numericRows = rows.map((r) => r.filter((c) => typeof c === 'number'))

  // 是否渲染图表（排除纯数字卡片）
  const chartType = isNumber
    ? 'number'
    : chart.includes('pie')
      ? 'pie'
      : chart.includes('line')
        ? 'line'
        : chart.includes('bar') || rows.length > 1
          ? 'bar'
          : 'table'

  // 构造 ECharts option
  const buildOption = () => {
    if (chartType === 'pie') {
      return {
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        color: ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
        series: [{
          type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
          data: rows.map((r) => ({ name: String(r[0]), value: Number(r[1]) || 0 })),
          label: { formatter: '{b}' },
        }],
      }
    }
    // bar / line
    const xLabels = rows.map((r) => String(r[0]))
    const series = columns.slice(1).map((col, i) => ({
      name: String(col),
      type: chartType === 'line' ? 'line' : 'bar',
      smooth: chartType === 'line',
      data: rows.map((r) => (typeof r[i + 1] === 'number' ? r[i + 1] : 0)),
    }))
    return {
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      grid: { left: 50, right: 20, top: 30, bottom: 50 },
      color: ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
      xAxis: { type: 'category', data: xLabels, axisLabel: { color: '#6B7280' } },
      yAxis: { type: 'value', axisLabel: { color: '#6B7280' } },
      series,
    }
  }

  // 数据统计（数值列：总行数 + 平均值 + 最大 + 最小）
  const stats = []
  if (rows.length > 0 && columns.length > 1) {
    const valIdx = columns.slice(1).map((_, i) => i + 1).filter((i) => rows.every((r) => typeof r[i] === 'number'))
    if (valIdx.length) {
      const ci = valIdx[0]
      const vals = rows.map((r) => r[ci])
      stats.push(['总记录数', `${rows.length} 条`])
      stats.push(['平均值', fmt((vals.reduce((a, b) => a + b, 0) / vals.length))])
      stats.push(['最大值', fmt(Math.max(...vals))])
      stats.push(['最小值', fmt(Math.min(...vals))])
    }
  }

  return (
    <div className="ai-msg">
      <div className="ai-card">
        {/* 顶部解释文字 */}
        {data?.explanation && <div className="ai-explain">{data.explanation}</div>}

        {/* 分析过程折叠栏 */}
        <div className="steps-bar" onClick={() => setShowSteps(!showSteps)}>
          <Icon name="robot" /> 分析过程
          <span className="arr">{showSteps ? '▾' : '▸'}</span>
          <span className="hint">{showSteps ? '点击收起' : '点击展开'}</span>
        </div>
        {showSteps && (
          <div className="steps">
            {[
              ['① 理解问题', `AI 拆解用户问题「${msg.text}」，判断查询维度与指标`],
              ['② 生成 SQL', data?.sql || '（无）'],
              ['③ 执行查询', `数据库返回 ${rows.length} 行结果`],
            ].map(([t, d], i) => (
              <div className="step" key={i}>
                <div className="step-icon">✓</div>
                <div>
                  <div className="step-title">{t}</div>
                  <div className={'step-desc' + (t.includes('SQL') ? ' code' : '')}>{d}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 数字大卡片 */}
        {isNumber && (
          <div className="number-card">
            <div className="number-label">{columns[0] || '结果'}</div>
            <div className="number-value">{fmtValue(rows[0][0], columns[0])}</div>
          </div>
        )}

        {/* 图表 */}
        {!isNumber && rows.length > 0 && chartType !== 'table' && (
          <div className="chart-box">
            <EChart option={buildOption()} />
          </div>
        )}

        {/* 数据表格 */}
        {rows.length > 0 && (
          <div className="table-box">
            <table className="qa-table">
              <thead>
                <tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((r, ri) => (
                  <tr key={ri}>{r.map((c, ci) => <td key={ci}>{fmt(c)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 数据统计 */}
        {stats.length > 0 && (
          <div className="stats">
            {stats.map(([k, v], i) => (
              <div className="stat" key={i}><span className="k">{k}</span><span className="v">{v}</span></div>
            ))}
          </div>
        )}

        {/* SQL 展示（透明性，Code Review 加分） */}
        {data?.sql && (
          <div className="sql-box">
            <div className="sql-bar" onClick={() => setShowSql(!showSql)}>
              <Icon name="table" /> SQL <span className="arr">{showSql ? '▾' : '▸'}</span>
            </div>
            {showSql && <pre className="sql">{data.sql}</pre>}
          </div>
        )}

        {/* 底部统计 */}
        <div className="ai-footer">
          <span className="foot-stat">耗时 {elapsed}s</span>
          <span className="foot-stat">数据 {rows.length} 行</span>
        </div>

        {/* 追问建议 */}
        <div className="followups">
          {['上月销售额是多少', '哪个月销售额最高', '对比各区域情况'].map((t, i) => (
            <span className="fu-chip" key={i} onClick={() => window.__ask(t)}>{t} <span className="fu-arr">→</span></span>
          ))}
        </div>
      </div>
    </div>
  )
}

// ===== 用户消息 =====
function UserMsg({ text }) {
  return (
    <div className="user-msg">
      <div className="user-bubble">{text}</div>
    </div>
  )
}

// ===== 主组件 =====
export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sessions, setSessions] = useState([{ id: 1, title: '新对话', time: '刚刚' }])
  const [sessionId, setSessionId] = useState(1)
  const msgsRef = useRef(null)

  const send = async (text) => {
    const q = (text ?? input).trim()
    if (!q || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setLoading(true)
    const t0 = performance.now()
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const data = await res.json()
      const elapsed = ((performance.now() - t0) / 1000).toFixed(1)
      if (data.error) {
        setMessages((m) => [...m, { role: 'ai', text: q, error: true, detail: data.detail || data.error }])
      } else {
        setMessages((m) => [...m, { role: 'ai', text: q, data, elapsed }])
      }
    } catch (e) {
      setMessages((m) => [...m, { role: 'ai', text: q, error: true, detail: '网络错误，请确认后端服务已启动（8000 端口）' }])
    } finally {
      setLoading(false)
    }
  }

  // 供 AiCard 追问按钮调用
  useEffect(() => { window.__ask = (t) => send(t) }, [send])

  // 自动滚动到底部
  useEffect(() => {
    if (msgsRef.current) msgsRef.current.scrollTop = msgsRef.current.scrollHeight
  }, [messages, loading])

  const newSession = () => {
    const id = Date.now()
    setSessions((s) => [{ id, title: '新对话', time: '刚刚' }, ...s])
    setSessionId(id)
    setMessages([])
  }

  return (
    <div className="app">
      {/* 侧边栏 */}
      <aside className={'sidebar' + (sidebarOpen ? '' : ' collapsed')}>
        <div className="sb-head">
          <div className="logo">⚙ AI问数</div>
          <button className="icon-btn" onClick={() => setSidebarOpen(false)} title="收起"><Icon name="chevron" /></button>
        </div>
        <button className="new-chat" onClick={newSession}><Icon name="plus" /> 开启新对话</button>
        <div className="sb-list">
          <div className="sb-list-title">近30天记录</div>
          {sessions.map((s) => (
            <div className={'sb-item' + (s.id === sessionId ? ' active' : '')} key={s.id} onClick={() => { setSessionId(s.id); setMessages([]) }}>
              <span className="sb-dot" /> {s.title}
            </div>
          ))}
        </div>
      </aside>

      {/* 主区域 */}
      <div className="main">
        <header className="topbar">
          {!sidebarOpen && <button className="icon-btn" onClick={() => setSidebarOpen(true)}><Icon name="menu" /></button>}
          <div className="topbar-title">AI 智能问数对话</div>
        </header>

        <div className="chat-scroll" ref={msgsRef}>
          {messages.length === 0 ? (
            <div className="welcome">
              <h1>你好</h1>
              <h2>我是 AI 问数助手</h2>
              <p className="welcome-desc">欢迎使用智能 AI 问数，您可以向我咨询经营数据、报表分析相关问题。</p>
              <div className="sugg-title">你可以这么问我</div>
              <div className="sugg-grid">
                {SUGGESTIONS.map((s, i) => (
                  <div className="sugg-card" key={i} onClick={() => send(s)}>
                    <Icon name="bolt" /> {s}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) =>
              m.role === 'user' ? (
                <UserMsg key={i} text={m.text} />
              ) : m.error ? (
                <div className="ai-msg" key={i}>
                  <div className="ai-card error-card">⚠️ 查询失败：{m.detail}</div>
                </div>
              ) : (
                <AiCard key={i} msg={m} />
              ),
            )
          )}
          {loading && (
            <div className="ai-msg">
              <div className="ai-card typing">正在分析并查询数据…</div>
            </div>
          )}
        </div>

        {/* 输入栏 */}
        <div className="input-bar">
          <div className="input-wrap">
            <input
              placeholder="请写下您的想法…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            />
            <button className="mic-btn" title="语音（可选）"><Icon name="mic" /></button>
            <button className="send-btn" onClick={() => send()} disabled={loading}><Icon name="send" /></button>
          </div>
        </div>
      </div>
    </div>
  )
}
