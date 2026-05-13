import { Button } from '../ui/Button'

type TimerControlsProps = {
  isRunning: boolean
  userName: string
  onStart: (name: string) => void
  onStop: () => void
  loading: boolean
}

export function TimerControls({
  isRunning,
  userName,
  onStart,
  onStop,
  loading,
}: TimerControlsProps) {
  if (!isRunning) {
    return (
      <div className="flex flex-col items-center gap-3 w-full max-w-sm">
        <input
          type="text"
          placeholder="输入姓名开始计时"
          defaultValue={userName}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onStart((e.target as HTMLInputElement).value)
          }}
          className="w-full px-5 py-3.5 rounded-input bg-input border border-border text-primary
                     placeholder:text-muted text-base outline-none
                     focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/30
                     transition-all duration-200"
          id="timer-name-input"
        />
        <Button
          variant="primary"
          size="lg"
          className="w-full"
          disabled={loading}
          onClick={() => {
            const input = document.getElementById('timer-name-input') as HTMLInputElement
            if (input?.value.trim()) onStart(input.value.trim())
          }}
        >
          {loading ? '启动中…' : '开始计时'}
        </Button>
      </div>
    )
  }

  return (
    <Button variant="danger" size="lg" onClick={onStop} disabled={loading}>
      停止计时
    </Button>
  )
}
