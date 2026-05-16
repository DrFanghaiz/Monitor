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
        var toolDisplay = EscapeHtml(rc.RemoteType ?? "-");
        var opDisplay = rc.IsRemote
            ? (string.IsNullOrEmpty(rc.OperatorName) ? "未登记" : EscapeHtml(rc.OperatorName))
            : "-";
        var startDisplay = rc.IsRemote && !string.IsNullOrEmpty(rc.StartTime) ? rc.StartTime : "-";
        var elapsedDisplay = rc.IsRemote ? rc.ElapsedFormatted : "-";
        var sessionsHtml = BuildSessionsRows(sessions);

        return @"
<!DOCTYPE html>
<html lang=""zh-CN"">
<head>
<meta charset=""utf-8"">
<meta name=""viewport"" content=""width=device-width,initial-scale=1"">
<title>Monitor · 公用机状态</title>
<style>
:root{--bg:#f6f7fb;--card:#fff;--line:#e5e8ef;--text:#172033;--muted:#8793a7;--green:#15996b;--red:#e6536f;--amber:#b7791f;--blue:#3478f6;--shadow:0 10px 28px rgba(31,42,68,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:""Segoe UI"",""Microsoft YaHei"",system-ui,sans-serif;padding:24px}
.page{width:min(680px,100%);margin:0 auto}.head{padding:14px 0 18px}.head h1{margin:0;font-size:24px}.head p{margin:6px 0 0;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);padding:30px;margin-bottom:18px}
.status{text-align:center}.dot{width:18px;height:18px;border-radius:50%;margin:0 auto 14px}.state-idle .dot{background:var(--green);box-shadow:0 0 0 8px rgba(21,153,107,.12)}.state-occupied .dot,.state-error .dot{background:var(--red);box-shadow:0 0 0 8px rgba(230,83,111,.13)}.state-unknown .dot{background:var(--amber);box-shadow:0 0 0 8px rgba(183,121,31,.13)}.state-inuse .dot{background:var(--blue);box-shadow:0 0 0 8px rgba(52,120,246,.13)}
.label{font-size:30px;font-weight:800;letter-spacing:-.5px}.state-idle .label{color:var(--green)}.state-occupied .label,.state-error .label{color:var(--red)}.state-unknown .label{color:var(--amber)}.state-inuse .label{color:var(--blue)}
.tip{margin-top:8px;color:#526078;font-size:16px}.facts{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid var(--line);margin-top:26px;text-align:left}.fact{padding:16px 4px;border-bottom:1px solid var(--line)}.fact span{display:block;color:var(--muted);font-size:13px;margin-bottom:5px}.fact strong{font-size:17px;font-weight:650}
.reg{display:none}.reg h2,.sessions h2{font-size:17px;margin:0 0 14px}.reg-row{display:flex;gap:10px;flex-wrap:wrap}.reg input{height:42px;border:1px solid var(--line);border-radius:10px;background:#fafbff;padding:0 13px;font-size:15px}.reg button{height:42px;border:none;border-radius:10px;background:var(--blue);color:#fff;padding:0 20px;font-size:15px;font-weight:700}.msg{margin-top:10px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:11px 8px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted);font-weight:600}.empty{text-align:center;color:var(--muted);padding:18px;display:none}.err{display:none;color:var(--red);background:#fff1f3;border:1px solid #ffcbd5;border-radius:12px;padding:12px;margin-bottom:14px;text-align:center}.foot{text-align:center;color:var(--muted);font-size:12px;padding:8px 0 20px}
@media(max-width:520px){body{padding:16px}.card{padding:22px}.facts{grid-template-columns:1fr}.label{font-size:26px}th:nth-child(3),td:nth-child(3){display:none}}
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
<section class=""card reg"" id=""regCard""><h2>登记操作人</h2><div class=""reg-row""><input id=""name"" placeholder=""姓名"" maxlength=""30"" autocomplete=""off""><input id=""key"" placeholder=""登记码"" autocomplete=""off""><button id=""regBtn"">登记</button></div><div class=""msg"" id=""regMsg""></div></section>
<section class=""card sessions""><h2>最近远程记录</h2><div class=""empty"" id=""empty"">暂无远程记录</div><div style=""overflow-x:auto""><table><thead><tr><th>操作人</th><th>工具</th><th>开始</th><th>结束</th><th>时长</th></tr></thead><tbody id=""rows"">" + sessionsHtml + @"</tbody></table></div></section>
<div class=""foot"">Monitor · 公用机管理系统</div>
</main>
<script>
let regAvailable=false;
const $=id=>document.getElementById(id);
const text=(id,v)=>{const e=$(id);if(e)e.textContent=v||'-';};
function fmt(sec){sec=sec||0;const h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');}
function display(s){const rc=s.remote_control||{};if(rc.status==='error')return['state-error','检测异常','请联系管理员'];if(rc.status==='unknown')return['state-unknown','状态未知','请联系管理员'];if(rc.is_remote)return['state-occupied','疑似远程占用','请勿重复连接，避免控制冲突'];if(s.computer_status==='in_use')return['state-inuse','本机使用中','连接前请先确认'];return['state-idle','可连接','当前未检测到远程占用'];}
function updateReg(rc){const card=$('regCard');if(!card)return;card.style.display=regAvailable&&rc.is_remote&&!rc.operator_name?'block':'none';}
function refreshAvailability(){fetch('/api/remote/operator/register/available').then(r=>r.json()).then(d=>{regAvailable=!!d.available;}).catch(()=>{regAvailable=false;});}
function refreshSessions(){fetch('/api/remote/sessions/public').then(r=>r.json()).then(d=>{const rows=$('rows'),empty=$('empty'),list=d.sessions||[];while(rows.firstChild)rows.removeChild(rows.firstChild);empty.style.display=list.length?'none':'block';list.slice(0,5).forEach(s=>{const tr=document.createElement('tr');[s.operator_name||'未登记',s.remote_type||'-',s.start_time||'-',s.end_time||'进行中',fmt(s.duration_seconds)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td);});rows.appendChild(tr);});}).catch(()=>{});}
function refresh(){fetch('/api/status').then(r=>r.json()).then(s=>{const rc=s.remote_control||{},d=display(s),card=$('statusCard');card.className='card status '+d[0];text('label',d[1]);text('tip',d[2]);text('tool',rc.remote_type||'-');text('operator',rc.is_remote?(rc.operator_name||'未登记'):'-');text('start',rc.is_remote&&rc.start_time?rc.start_time:'-');text('elapsed',rc.is_remote?rc.elapsed_formatted:'-');$('err').style.display='none';updateReg(rc);}).catch(()=>{$('err').style.display='block';});refreshAvailability();refreshSessions();}
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
        if (rc.Status == "unknown") return ("#b7791f", "状态未知", "请联系管理员", "state-unknown");
        if (rc.IsRemote) return ("#e6536f", "疑似远程占用", "请勿重复连接，避免控制冲突", "state-occupied");
        if (s.ComputerStatus == "in_use") return ("#3478f6", "本机使用中", "连接前请先确认", "state-inuse");
        return ("#15996b", "可连接", "当前未检测到远程占用", "state-idle");
    }

    private static bool IsActive(Models.RemoteSession s)
        => s.IsActive || string.IsNullOrEmpty(s.EndTime);

    private static int ComputeElapsed(string startTime)
        => DateTime.TryParse(startTime, out var start) ? (int)(DateTime.Now - start).TotalSeconds : 0;

    private static string EscapeHtml(string s)
        => s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
            .Replace("\"", "&quot;").Replace("'", "&#39;");
}
