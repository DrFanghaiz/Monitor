using System.Text;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Repositories;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class WebStatusPageEndpoints
{
    public static void MapWebStatusPages(this WebApplication app)
    {
        app.MapGet("/favicon.ico", () => Results.Content(
            @"<svg xmlns=""http://www.w3.org/2000/svg"" viewBox=""0 0 32 32"">" +
            @"<defs><linearGradient id=""g"" x1=""6"" y1=""3"" x2=""26"" y2=""30""><stop stop-color=""#5c8dff""/><stop offset=""1"" stop-color=""#0d4ed8""/></linearGradient></defs>" +
            @"<rect x=""2"" y=""2"" width=""28"" height=""28"" rx=""7"" fill=""url(#g)""/>" +
            @"<rect x=""8.5"" y=""9"" width=""15"" height=""10"" rx=""2.2"" fill=""none"" stroke=""#f8fbff"" stroke-width=""2.5""/>" +
            @"<path d=""M16 19v4M12.5 24h7"" stroke=""#f8fbff"" stroke-width=""2.5"" stroke-linecap=""round""/>" +
            @"<circle cx=""23.5"" cy=""9"" r=""4.5"" fill=""#eafdf5""/>" +
            @"<circle cx=""23.5"" cy=""9"" r=""2.7"" fill=""#14a76c""/>" +
            @"</svg>", "image/svg+xml"));

        app.MapGet("/api/remote/sessions/public", (IRemoteSessionRepository repo) =>
        {
            var sessions = repo.GetRecentRemoteSessions(5)
                .Select(s => new
                {
                    s.RemoteType,
                    s.StartTime,
                    s.EndTime,
                    duration_seconds = IsActive(s) ? ComputeElapsed(s.StartTime) : s.DurationSeconds,
                    operator_name = string.IsNullOrEmpty(s.OperatorName) ? "未登记" : s.OperatorName
                });
            return Results.Ok(new { sessions });
        });

        app.MapGet("/", (StatusService status, IRemoteSessionRepository repo) =>
            Results.Content(BuildPage(status.GetFullStatus(), repo.GetRecentRemoteSessions(5)),
                "text/html; charset=utf-8"));

        app.MapGet("/status", (StatusService status, IRemoteSessionRepository repo) =>
            Results.Content(BuildPage(status.GetFullStatus(), repo.GetRecentRemoteSessions(5)),
                "text/html; charset=utf-8"));
    }

    private static string BuildPage(Models.AppStatus s, List<Models.RemoteSession> sessions)
    {
        var rc = s.RemoteControl;
        var (_, statusLabel, tipText, statusClass) = GetDisplay(s);
        var toolDisplay = rc.IsRemote
            ? EscapeHtml(rc.RemoteType ?? "-")
            : (rc.RunningTools is { Count: > 0 } ? EscapeHtml(string.Join("、", rc.RunningTools)) + "（后台）" : "-");
        var opDisplay = rc.IsRemote
            ? (string.IsNullOrEmpty(rc.OperatorName) ? "未登记" : EscapeHtml(rc.OperatorName))
            : "-";
        var startDisplay = rc.IsRemote && !string.IsNullOrEmpty(rc.StartTime) ? rc.StartTime : "-";
        var elapsedDisplay = rc.IsRemote ? rc.ElapsedFormatted : "-";
        var sessionsHtml = BuildSessionsRows(sessions);

        var c = s.Compute;
        var cStatusText = c.IsBusy ? "正在计算" : (c.Status == "error" ? "异常" : (c.Status == "unknown" ? "未知" : "空闲"));
        var cCpu = c.CpuUsagePercent.ToString("F0") + "%";
        var cMem = c.MemoryUsagePercent.ToString("F0") + "%";
        var cCount = c.ProcessCount.ToString();
        var cMsg = EscapeHtml(c.Message ?? "");
        var cProcsHtml = BuildProcessRows(c.Processes);

        return @"
<!DOCTYPE html>
<html lang=""zh-CN"">
<head>
<meta charset=""utf-8"">
<meta name=""viewport"" content=""width=device-width,initial-scale=1"">
<title>Monitor · 公用机状态</title>
<style>
:root{--bg:#f3f5f9;--card:#fff;--s2:#f6f8fc;--line:#e5eaf1;--text:#0f172a;--text2:#46536a;--muted:#737f93;--green:#0f9d76;--green-s:rgba(15,157,118,.10);--red:#df4a63;--red-s:rgba(223,74,99,.10);--amber:#b57712;--amber-s:rgba(181,119,18,.12);--blue:#4f6bed;--blue-s:rgba(79,107,237,.10);--shadow:0 12px 30px rgba(15,23,42,.10)}
@media (prefers-color-scheme:dark){:root{--bg:#0b0f16;--card:#131a25;--s2:#0f151e;--line:#1e2836;--text:#e8eef7;--text2:#9fadc0;--muted:#6d7b8e;--green:#2fce9f;--green-s:rgba(47,206,159,.13);--red:#ff6b81;--red-s:rgba(255,107,129,.14);--amber:#e2a640;--amber-s:rgba(226,166,64,.15);--blue:#8098ff;--blue-s:rgba(128,152,255,.15);--shadow:0 14px 36px rgba(0,0,0,.55)}}
*{box-sizing:border-box}html{color-scheme:light dark}body{margin:0;background:var(--bg);color:var(--text);font-family:""Segoe UI"",""Microsoft YaHei"",system-ui,sans-serif;font-size:14px;padding:24px}
.page{width:min(720px,100%);margin:0 auto}.head{padding:14px 0 18px}.head h1{margin:0;font-size:24px;letter-spacing:-.3px}.head p{margin:6px 0 0;color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:26px;margin-bottom:16px}
.status{text-align:center;background:linear-gradient(120deg,var(--st-s),transparent 64%);--st:var(--green);--st-s:var(--green-s)}.dot{width:16px;height:16px;border-radius:50%;margin:0 auto 14px;background:var(--st);box-shadow:0 0 0 7px var(--st-s)}
.status.state-idle{--st:var(--green);--st-s:var(--green-s)}.status.state-occupied,.status.state-error{--st:var(--red);--st-s:var(--red-s)}.status.state-unknown{--st:var(--amber);--st-s:var(--amber-s)}.status.state-inuse{--st:var(--blue);--st-s:var(--blue-s)}.status.state-busy{--st:var(--amber);--st-s:var(--amber-s)}
.label{font-size:32px;font-weight:800;letter-spacing:-.5px;color:var(--st)}.tip{margin-top:9px;color:var(--text2);font-size:15px;line-height:1.5}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid var(--line);margin-top:24px;text-align:left}.fact{padding:14px 4px;border-bottom:1px solid var(--line)}.fact span{display:block;color:var(--muted);font-size:12px;margin-bottom:4px}.fact strong{font-size:16px;font-weight:650;color:var(--text)}
.reg{display:none}.reg h2,.sessions h2,.compute h2{font-size:15px;margin:0 0 14px;font-weight:650}.reg-row{display:flex;gap:10px;flex-wrap:wrap}.reg input{height:40px;border:1px solid var(--line);border-radius:9px;background:var(--s2);color:var(--text);padding:0 12px;font-size:14px}.reg button{height:40px;border:none;border-radius:9px;background:var(--blue);color:#fff;padding:0 20px;font-size:14px;font-weight:700}.msg{margin-top:10px;color:var(--muted);font-size:13px}
.compute-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}.cstat{background:var(--s2);border:1px solid var(--line);border-radius:12px;padding:12px;text-align:center}.cstat span{display:block;color:var(--muted);font-size:11px;margin-bottom:4px}.cstat strong{font-size:18px;font-variant-numeric:tabular-nums}.cprocs table{font-size:13px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted);font-weight:600;font-size:12px}.empty{text-align:center;color:var(--muted);padding:16px;display:none}.err{display:none;color:var(--red);background:var(--red-s);border:1px solid var(--red);border-radius:12px;padding:12px;margin-bottom:14px;text-align:center;font-size:13px}.foot{text-align:center;color:var(--muted);font-size:12px;padding:8px 0 22px}
@media(max-width:520px){body{padding:16px}.card{padding:22px}.facts{grid-template-columns:1fr}.compute-summary{grid-template-columns:repeat(2,1fr)}.label{font-size:26px}th:nth-child(3),td:nth-child(3){display:none}}
</style>
</head>
<body>
<main class=""page"">
<header class=""head""><h1>Monitor</h1><p>公用机远程占用状态</p></header>
<div class=""err"" id=""err"">无法获取状态</div>
<section class=""card status " + statusClass + @""" id=""statusCard"">
<div class=""dot""></div><div class=""label"" id=""label"">" + statusLabel + @"</div><div class=""tip"" id=""tip"">" + tipText + @"</div>
<div class=""facts"">
<div class=""fact""><span>远程工具</span><strong id=""tool"">" + toolDisplay + @"</strong></div>
<div class=""fact""><span>操作人</span><strong id=""operator"">" + opDisplay + @"</strong></div>
<div class=""fact""><span>开始时间</span><strong id=""start"">" + startDisplay + @"</strong></div>
<div class=""fact""><span>已占用时长</span><strong id=""elapsed"">" + elapsedDisplay + @"</strong></div>
</div>
</section>
<section class=""card compute"" id=""computeCard"">
<h2 style=""font-size:17px;margin:0 0 14px"">计算任务</h2>
<div class=""compute-summary"">
<div class=""cstat""><span>状态</span><strong id=""cstatus"">" + cStatusText + @"</strong></div>
<div class=""cstat""><span>CPU</span><strong id=""ccpu"">" + cCpu + @"</strong></div>
<div class=""cstat""><span>内存</span><strong id=""cmem"">" + cMem + @"</strong></div>
<div class=""cstat""><span>任务数</span><strong id=""ccount"">" + cCount + @"</strong></div>
</div>
<div class=""cprocs"" id=""cprocs"">" + cProcsHtml + @"</div>
<div class=""msg"" id=""cmsg"">" + cMsg + @"</div>
</section>
<section class=""card reg"" id=""regCard""><h2>登记操作人</h2><div class=""reg-row""><input id=""name"" placeholder=""姓名"" maxlength=""30"" autocomplete=""off""><input id=""key"" placeholder=""登记码"" autocomplete=""off""><button id=""regBtn"">登记</button></div><div class=""msg"" id=""regMsg""></div></section>
<section class=""card sessions""><h2>最近远程记录</h2><div class=""empty"" id=""empty"">暂无远程记录</div><div style=""overflow-x:auto""><table><thead><tr><th>操作人</th><th>工具</th><th>开始</th><th>结束</th><th>时长</th></tr></thead><tbody id=""rows"">" + sessionsHtml + @"</tbody></table></div></section>
<div class=""foot"">Monitor · 公用机管理系统</div>
</main>
<script>
let regAvailable=false;
const $=id=>document.getElementById(id);
const text=(id,v)=>{const e=$(id);if(e)e.textContent=v||'-';};
function fmt(sec){sec=sec||0;const h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');}
const esc=v=>String(v==null?'':v).replace(/[&<>""]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','""':'&quot;'}[c]));
function cprocesses(c){const box=$('cprocs');if(!box)return;const list=c.processes||[];if(!list.length){box.innerHTML='';return;}let h='<table><thead><tr><th>进程</th><th>PID</th><th>CPU</th><th>内存</th><th>已运行</th></tr></thead><tbody>';list.forEach(p=>{h+='<tr><td>'+esc(p.name)+'</td><td>'+p.pid+'</td><td>'+(p.cpu_percent||0).toFixed(1)+'%</td><td>'+(p.working_set_mb||0).toFixed(0)+' MB</td><td>'+(p.elapsed_formatted||'-')+'</td></tr>';});h+='</tbody></table>';box.innerHTML=h;}
function display(s){const c=s.compute||{},rc=s.remote_control||{};if(rc.status==='error')return['state-error','检测异常','请联系管理员'];if(c.is_busy)return['state-busy','正在计算','有计算任务在运行，请勿关机或关闭程序'];if(rc.status==='disabled')return['state-unknown','检测已关闭','远程检测已在设置中关闭，无法判断占用'];if(rc.status==='initializing'||rc.status==='unknown')return['state-occupied','疑似占用 · 检测中','远程检测尚未就绪，暂按占用处理'];if(rc.is_remote){let tip=rc.conflict?('检测到 '+rc.active_tool_count+' 个远程工具同时在线，可能多人同时控制，请先协调再连接'):(rc.operator_name?'请勿重复连接，避免控制冲突':'有人正在远程使用且未登记操作人，请先确认');return['state-occupied','疑似远程占用',tip];}if(s.computer_status==='in_use')return['state-inuse','本机使用中','连接前请先确认'];return['state-idle','可连接','当前未检测到远程占用'];}
function updateReg(rc){const card=$('regCard');if(!card)return;card.style.display=regAvailable&&rc.is_remote&&!rc.operator_name?'block':'none';}
function refreshAvailability(){fetch('/api/remote/operator/register/available').then(r=>r.json()).then(d=>{regAvailable=!!d.available;}).catch(()=>{regAvailable=false;});}
function refreshSessions(){fetch('/api/remote/sessions/public').then(r=>r.json()).then(d=>{const rows=$('rows'),empty=$('empty'),list=d.sessions||[];while(rows.firstChild)rows.removeChild(rows.firstChild);empty.style.display=list.length?'none':'block';list.slice(0,5).forEach(s=>{const tr=document.createElement('tr');[s.operator_name||'未登记',s.remote_type||'-',s.start_time||'-',s.end_time||'进行中',fmt(s.duration_seconds)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td);});rows.appendChild(tr);});}).catch(()=>{});}
function refresh(){fetch('/api/status').then(r=>r.json()).then(s=>{const rc=s.remote_control||{},d=display(s),card=$('statusCard');card.className='card status '+d[0];text('label',d[1]);text('tip',d[2]);text('tool',rc.remote_type||'-');text('operator',rc.is_remote?(rc.operator_name||'未登记'):'-');text('start',rc.is_remote&&rc.start_time?rc.start_time:'-');text('elapsed',rc.is_remote?rc.elapsed_formatted:'-');const c=s.compute||{};text('cstatus',c.is_busy?'正在计算':(c.status==='error'?'异常':(c.status==='unknown'?'未知':'空闲')));text('ccpu',(c.cpu_usage_percent||0).toFixed(0)+'%');text('cmem',(c.memory_usage_percent||0).toFixed(0)+'%');text('ccount',String(c.process_count||0));text('cmsg',c.message||'');cprocesses(c);$('err').style.display='none';updateReg(rc);}).catch(()=>{$('err').style.display='block';});refreshAvailability();refreshSessions();}
function register(){const name=$('name').value.trim(),key=$('key').value.trim(),msg=$('regMsg'),btn=$('regBtn');if(!name){msg.textContent='请输入姓名';return;}if(!key){msg.textContent='请输入登记码';return;}btn.disabled=true;fetch('/api/remote/operator/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({operator_name:name,registration_key:key})}).then(r=>r.json().then(d=>({ok:r.ok,d}))).then(x=>{msg.textContent=x.ok?'已登记':(x.d.detail||'登记失败');refresh();}).catch(()=>{msg.textContent='网络错误';}).finally(()=>{btn.disabled=false;});}
$('regBtn').addEventListener('click',register);refresh();setInterval(refresh,5000);
</script>
</body>
</html>";
    }

    private static string BuildSessionsRows(List<Models.RemoteSession> sessions)
    {
        var sb = new StringBuilder();
        foreach (var sess in sessions.Take(5))
        {
            var op = string.IsNullOrEmpty(sess.OperatorName) ? "未登记" : EscapeHtml(sess.OperatorName);
            var end = IsActive(sess) ? "进行中" : (sess.EndTime ?? "-");
            var dur = TimerService.FormatDuration(IsActive(sess) ? ComputeElapsed(sess.StartTime) : sess.DurationSeconds);
            sb.Append("<tr><td>").Append(op).Append("</td><td>").Append(EscapeHtml(sess.RemoteType))
                .Append("</td><td>").Append(EscapeHtml(sess.StartTime)).Append("</td><td>").Append(EscapeHtml(end))
                .Append("</td><td>").Append(dur).Append("</td></tr>");
        }
        return sb.ToString();
    }

    private static (string color, string label, string tip, string cssClass) GetDisplay(Models.AppStatus s)
    {
        var rc = s.RemoteControl;
        if (rc.Status == "error") return ("#e6536f", "检测异常", "请联系管理员", "state-error");
        if (s.Compute.IsBusy) return ("#b7791f", "正在计算", "有计算任务在运行，请勿关机或关闭程序", "state-busy");
        if (rc.Status == "disabled") return ("#8793a7", "检测已关闭", "远程检测已在设置中关闭，无法判断占用", "state-unknown");
        if (rc.Status is "initializing" or "unknown") return ("#e6536f", "疑似占用 · 检测中", "远程检测尚未就绪，暂按占用处理", "state-occupied");
        if (rc.IsRemote)
        {
            var tip = rc.Conflict
                ? $"检测到 {rc.ActiveToolCount} 个远程工具同时在线，可能多人同时控制，请先协调再连接"
                : (string.IsNullOrEmpty(rc.OperatorName) ? "有人正在远程使用且未登记操作人，请先确认" : "请勿重复连接，避免控制冲突");
            return ("#e6536f", "疑似远程占用", tip, "state-occupied");
        }
        if (s.ComputerStatus == "in_use") return ("#3478f6", "本机使用中", "连接前请先确认", "state-inuse");
        return ("#15996b", "可连接", "当前未检测到远程占用", "state-idle");
    }

    private static string BuildProcessRows(List<Models.JobProcessInfo> processes)
    {
        if (processes == null || processes.Count == 0) return "";
        var sb = new StringBuilder();
        sb.Append("<table><thead><tr><th>进程</th><th>PID</th><th>CPU</th><th>内存</th><th>已运行</th></tr></thead><tbody>");
        foreach (var p in processes)
        {
            sb.Append("<tr><td>").Append(EscapeHtml(p.Name)).Append("</td><td>").Append(p.Pid)
              .Append("</td><td>").Append(p.CpuPercent.ToString("F1")).Append("%</td><td>")
              .Append(p.WorkingSetMb.ToString("F0")).Append(" MB</td><td>")
              .Append(EscapeHtml(p.ElapsedFormatted)).Append("</td></tr>");
        }
        sb.Append("</tbody></table>");
        return sb.ToString();
    }

    private static bool IsActive(Models.RemoteSession s)
        => s.IsActive || string.IsNullOrEmpty(s.EndTime);

    private static int ComputeElapsed(string startTime)
        => DateTime.TryParse(startTime, out var start) ? (int)(DateTime.Now - start).TotalSeconds : 0;

    private static string EscapeHtml(string s)
        => s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
            .Replace("\"", "&quot;").Replace("'", "&#39;");
}
