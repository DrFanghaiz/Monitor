import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSettings, useChangeAdminPassword, useChangeWebPassword, useCreateBackup, useBackups } from '../hooks/useSettings'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { fadeInUp, staggerContainer } from '../theme/motion'

export function Settings() {
  const { data: info } = useSettings()
  const { data: backupData } = useBackups()
  const changeAdmin = useChangeAdminPassword()
  const changeWeb = useChangeWebPassword()
  const createBackup = useCreateBackup()

  const [adminOld, setAdminOld] = useState('')
  const [adminNew, setAdminNew] = useState('')
  const [webPwd, setWebPwd] = useState('')
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null)

  function flash(text: string, ok: boolean) {
    setMsg({ text, ok })
    setTimeout(() => setMsg(null), 3000)
  }

  return (
    <motion.div className="space-y-6 max-w-2xl" variants={staggerContainer} initial="hidden" animate="visible">
      <motion.div variants={fadeInUp}>
        <h1 className="text-2xl font-bold text-primary tracking-tight font-display">系统设置</h1>
      </motion.div>

      {/* Toast */}
      {msg && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className={`px-4 py-3 rounded-xl text-sm font-medium ${msg.ok ? 'bg-accent-green/10 text-accent-green border border-accent-green/20' : 'bg-accent-red/10 text-accent-red border border-accent-red/20'}`}>
          {msg.text}
        </motion.div>
      )}

      {/* Admin password */}
      <motion.div variants={fadeInUp}>
        <Card>
          <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider font-display mb-4">管理员密码</h2>
          <div className="space-y-3 max-w-sm">
            <input type="password" placeholder="当前密码" value={adminOld} onChange={(e) => setAdminOld(e.target.value)}
              className="w-full px-4 py-2.5 rounded-input bg-input border border-border text-primary
                         placeholder:text-muted text-sm outline-none focus:border-accent-cyan transition-colors" />
            <input type="password" placeholder="新密码" value={adminNew} onChange={(e) => setAdminNew(e.target.value)}
              className="w-full px-4 py-2.5 rounded-input bg-input border border-border text-primary
                         placeholder:text-muted text-sm outline-none focus:border-accent-cyan transition-colors" />
            <Button size="sm" disabled={changeAdmin.isPending || !adminNew}
              onClick={() => changeAdmin.mutate({ old_password: adminOld, new_password: adminNew }, {
                onSuccess: () => { flash('密码已修改', true); setAdminOld(''); setAdminNew('') },
                onError: (e) => flash(e.message, false),
              })}>
              确认修改
            </Button>
          </div>
        </Card>
      </motion.div>

      {/* Web password */}
      <motion.div variants={fadeInUp}>
        <Card>
          <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider font-display mb-4">Web 访问密码</h2>
          <div className="space-y-3 max-w-sm">
            <input type="password" placeholder="新密码" value={webPwd} onChange={(e) => setWebPwd(e.target.value)}
              className="w-full px-4 py-2.5 rounded-input bg-input border border-border text-primary
                         placeholder:text-muted text-sm outline-none focus:border-accent-cyan transition-colors" />
            <Button size="sm" disabled={changeWeb.isPending || !webPwd}
              onClick={() => changeWeb.mutate(webPwd, {
                onSuccess: () => { flash('Web 密码已修改', true); setWebPwd('') },
              })}>
              确认修改
            </Button>
          </div>
        </Card>
      </motion.div>

      {/* Backup */}
      <motion.div variants={fadeInUp}>
        <Card>
          <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider font-display mb-4">数据备份</h2>
          <Button variant="ghost" size="sm" onClick={() => createBackup.mutate(undefined, { onSuccess: () => flash('备份已创建', true) })} disabled={createBackup.isPending}>
            {createBackup.isPending ? '备份中…' : '立即备份'}
          </Button>
          {backupData?.backups && backupData.backups.length > 0 && (
            <div className="mt-4 space-y-1">
              {backupData.backups.slice(0, 5).map((b) => (
                <div key={b.name} className="flex items-center justify-between py-1.5 text-sm">
                  <span className="text-primary">{b.name}</span>
                  <span className="text-muted text-xs">{b.created}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </motion.div>

      {/* System info */}
      <motion.div variants={fadeInUp}>
        <Card>
          <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider font-display mb-3">系统信息</h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-1.5 text-sm">
            <span className="text-muted">Web 端口</span><span className="text-primary tabular-nums">{info?.web_server_port ?? '—'}</span>
            <span className="text-muted">隧道模式</span><span className="text-primary">{info?.tunnel_mode ?? '—'}</span>
            <span className="text-muted">自动备份</span><span className={info?.auto_backup ? 'text-accent-green' : 'text-muted'}>{info?.auto_backup ? '已启用' : '已禁用'}</span>
            <span className="text-muted">备份保留</span><span className="text-primary">{info?.backup_retention_days ?? '—'} 天</span>
            <span className="text-muted">远程监控</span><span className={info?.remote_monitor_enabled ? 'text-accent-green' : 'text-muted'}>{info?.remote_monitor_enabled ? '已启用' : '已禁用'}</span>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  )
}
