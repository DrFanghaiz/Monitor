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
        // Minimal SVG favicon to eliminate 404
        app.MapGet("/favicon.ico", () => Results.Content(
            @"<svg xmlns=""http://www.w3.org/2000/svg"" viewBox=""0 0 32 32"">" +
            @"<rect width=""32"" height=""32"" rx=""6"" fill=""#3b82f6""/>" +
            @"<text x=""16"" y=""23"" text-anchor=""middle"" font-size=""20"" font-family=""sans-serif"" fill=""#fff"">M</text>" +
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
        {
            return Results.Content(BuildPage(status.GetFullStatus(), repo.GetRecentRemoteSessions(5)),
                "text/html; charset=utf-8");
        });

        app.MapGet("/status", (StatusService status, IRemoteSessionRepository repo) =>
        {
            return Results.Content(BuildPage(status.GetFullStatus(), repo.GetRecentRemoteSessions(5)),
                "text/html; charset=utf-8");
        });
    }

    private static string BuildPage(Models.AppStatus s, List<Models.RemoteSession> sessions)
    {
        var rc = s.RemoteControl;
        var (statusColor, statusLabel, tipText) = GetDisplay(s);

        var toolDisplay = EscapeHtml(rc.RemoteType ?? "—");
        var opDisplay = rc.IsRemote
            ? (string.IsNullOrEmpty(rc.OperatorName) ? "操作人未登记" : EscapeHtml(rc.OperatorName))
            : "—";
        var startDisplay = rc.IsRemote && !string.IsNullOrEmpty(rc.StartTime) ? rc.StartTime : "—";
        var elapsedDisplay = rc.IsRemote ? rc.ElapsedFormatted : "—";
        var lastSeenDisplay = rc.LastSeenAt ?? s.Timestamp;
        var signalsDisplay = rc.MatchedSignals?.Count > 0 ? string.Join(", ", rc.MatchedSignals) : "—";
        var messageDisplay = EscapeHtml(rc.Message ?? "—");

        var sb = new StringBuilder();
        foreach (var sess in sessions.Take(5))
        {
            var op = string.IsNullOrEmpty(sess.OperatorName) ? "未登记" : EscapeHtml(sess.OperatorName);
            var end = IsActive(sess) ? "进行中" : (sess.EndTime ?? "—");
            var dur = TimerService.FormatDuration(IsActive(sess) ? ComputeElapsed(sess.StartTime) : sess.DurationSeconds);
            sb.Append("<tr><td>").Append(op).Append("</td><td>").Append(EscapeHtml(sess.RemoteType))
              .Append("</td><td>").Append(sess.StartTime).Append("</td><td>").Append(end)
              .Append("</td><td>").Append(dur).Append("</td></tr>");
        }
        var sessionsHtml = sb.ToString();

        var html = @"<!DOCTYPE html>
<html lang=""zh-CN"">
<head>
<meta charset=""utf-8"">
<meta name=""viewport"" content=""width=device-width,initial-scale=1"">
<title>Monitor · 机器状态</title>
<style>
  :root{--bg:#f5f6f8;--card:#ffffff;--border:#e5e7eb;--text:#1a1a2e;--sub:#6b7280;--muted:#9ca3af;--green:#15996b;--red:#d95050;--amber:#b7791f;--blue:#3b82f6;--shadow:0 1px 3px rgba(0,0,0,.06);--radius:12px}
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{font-family:""Segoe UI"",""Microsoft YaHei"",""PingFang SC"",system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;justify-content:center;padding:20px}
  .page{max-width:560px;width:100%}
  .header{text-align:center;padding:24px 0 12px}
  .header h1{font-size:18px;font-weight:600;letter-spacing:-.3px}
  .header p{font-size:13px;color:var(--sub);margin-top:2px}
  .status-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:28px 24px;box-shadow:var(--shadow);text-align:center;margin-bottom:16px}
  .status-dot{display:inline-block;width:14px;height:14px;border-radius:50%;margin-bottom:8px}
  .status-label{font-size:22px;font-weight:600;margin-bottom:4px}
  .status-tip{font-size:14px;color:var(--sub);margin-bottom:16px}
  .info-grid{display:grid;grid-template-columns:1fr 1fr;gap:0;text-align:left;border-top:1px solid var(--border);padding-top:16px}
  .info-item{padding:8px 0;border-bottom:1px solid var(--border)}
  .info-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}
  .info-value{font-size:14px}
  .sessions-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;box-shadow:var(--shadow);margin-bottom:16px}
  .sessions-title{font-size:14px;font-weight:600;margin-bottom:12px}
  .sessions-empty{text-align:center;color:var(--muted);font-size:13px;padding:16px 0}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{padding:8px 6px;text-align:left;border-bottom:1px solid var(--border)}
  th{color:var(--muted);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  td{color:var(--text)}
  .footer{text-align:center;font-size:11px;color:var(--muted);padding:8px 0 24px}
  .error-banner{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px;text-align:center;font-size:13px;color:var(--red);margin-bottom:16px;display:none}
  .reg-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;box-shadow:var(--shadow);margin-bottom:16px;display:none}
  .reg-title{font-size:14px;font-weight:600;margin-bottom:12px}
  .reg-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  .reg-input{border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:14px;outline:none;width:140px;background:var(--bg);color:var(--text)}
  .reg-input:focus{border-color:var(--blue)}
  .reg-btn{border:none;border-radius:8px;padding:8px 18px;font-size:14px;font-weight:500;cursor:pointer;background:var(--blue);color:#fff}
  .reg-btn:disabled{opacity:.4;cursor:default}
  .reg-msg{margin-top:8px;font-size:13px}
  @media (max-width:480px){
    .info-grid{grid-template-columns:1fr}
    .info-item{border-bottom:1px solid var(--border)}
    .info-item:last-child{border-bottom:none}
    th,td{font-size:11px;padding:6px 4px}
  }
</style>
</head>
<body>
<div class=""page"">
  <div class=""header""><h1>Monitor</h1><p>公用机远程占用状态</p></div>
  <div class=""error-banner"" id=""eb"">无法获取状态</div>
  <div class=""status-card"">
    <div class=""status-dot"" id=""sd""></div>
    <div class=""status-label"" id=""sl"">" + statusLabel + @"</div>
    <div class=""status-tip"" id=""st"">" + tipText + @"</div>
    <div class=""info-grid"">
      <div class=""info-item""><div class=""info-label"">远程工具</div><div class=""info-value"" id=""v0"">" + toolDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">操作人</div><div class=""info-value"" id=""v1"">" + opDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">开始时间</div><div class=""info-value"" id=""v2"">" + startDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">已占用时长</div><div class=""info-value"" id=""v3"">" + elapsedDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">检测信号</div><div class=""info-value"" id=""v4"">" + signalsDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">最后检测</div><div class=""info-value"" id=""v5"">" + lastSeenDisplay + @"</div></div>
      <div class=""info-item""><div class=""info-label"">检测信息</div><div class=""info-value"" id=""v6"" style=""font-size:12px"">" + messageDisplay + @"</div></div>
      <div class=""info-item"" style=""grid-column:1/-1;border-bottom:none;padding-top:4px"">
        <div class=""info-value"" id=""v7"" style=""font-size:11px;color:var(--muted)"">" + s.Timestamp + @"</div>
      </div>
    </div>
  </div>
  <div class=""reg-card"" id=""rc"">
    <div class=""reg-title"">登记操作人</div>
    <div class=""reg-row"">
      <input class=""reg-input"" id=""ri1"" placeholder=""姓名"" maxlength=""30"" autocomplete=""off"">
      <input class=""reg-input"" id=""ri2"" placeholder=""登记码"" autocomplete=""off"">
      <button class=""reg-btn"" id=""rb"">登记</button>
    </div>
    <div class=""reg-msg"" id=""rm"" style=""color:var(--sub)""></div>
  </div>
  <div class=""sessions-card"">
    <div class=""sessions-title"">最近远程记录</div>
    <div class=""sessions-empty"" id=""se"" style=""display:none"">暂无远程记录</div>
    <div style=""overflow-x:auto""><table><thead><tr><th>操作人</th><th>工具</th><th>开始</th><th>结束</th><th>时长</th></tr></thead>
    <tbody id=""stb"">" + sessionsHtml + @"</tbody></table></div>
  </div>
  <div class=""footer"">Monitor · 公用机管理系统</div>
</div>
<script>
(function(){
var colors={occupied:'#d95050',error:'#d95050',unknown:'#b7791f',in_use:'#3b82f6',idle:'#15996b'};
function G(id){return document.getElementById(id);}
function T(el,txt){if(el)el.textContent=txt;}
function E(){var e=G('eb');if(e)e.style.display='block';}

function getDisplay(s){
  var rc=s.remote_control, cs=s.computer_status||'idle', st=rc.status||'idle';
  // error/unknown from remote status first
  if(st==='error') return['#d95050','检测异常','检测服务异常，请联系管理员'];
  if(st==='unknown') return['#b7791f','状态未知','检测尚未完成或未开启'];
  // occupied by remote
  if(rc.is_remote) return['#d95050','疑似远程占用','请勿重复连接，避免控制冲突'];
  // in_use: local timer running but no remote
  if(cs==='in_use') return['#3b82f6','本机使用中','当前有本机使用记录，连接前请确认不会打断他人'];
  // idle
  return['#15996b','可连接','当前未检测到远程占用'];
}

function fmtDur(sec){var h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60),s=sec%60;return ('0'+h).slice(-2)+':'+('0'+m).slice(-2)+':'+('0'+s).slice(-2);}

var _regAvailable=false;
function refreshRegistrationAvailability(){
  fetch('/api/remote/operator/register/available').then(function(r){return r.json()}).then(function(d){
    _regAvailable=d.available||false;
  }).catch(function(){_regAvailable=false;});
}

function updateRegistrationForm(rc){
  var card=G('rc'); if(!card)return;
  if(!_regAvailable){card.style.display='none';return;}
  if(!rc.is_remote){card.style.display='none';return;}
  if(rc.operator_name){card.style.display='none';return;}
  card.style.display='block';
}

function doRegister(){
  var name=G('ri1'), key=G('ri2'), msg=G('rm'), btn=G('rb');
  if(!name||!key||!msg||!btn)return;
  var n=name.value.trim(), k=key.value.trim();
  if(!n){msg.textContent='请输入姓名';msg.style.color='var(--red)';return;}
  if(n.length<2||n.length>30){msg.textContent='姓名长度 2-30 个字符';msg.style.color='var(--red)';return;}
  if(!k){msg.textContent='请输入登记码';msg.style.color='var(--red)';return;}
  btn.disabled=true; msg.textContent='提交中...'; msg.style.color='var(--sub)';
  fetch('/api/remote/operator/register',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({operator_name:n,registration_key:k})
  }).then(function(r){return r.json().then(function(d){return{ok:r.ok,data:d}});}).then(function(r){
    if(r.ok&&r.data.success){msg.textContent='登记成功: '+r.data.operator_name;msg.style.color='var(--green)';refreshAll();}
    else{msg.textContent=(r.data.detail||'失败');msg.style.color='var(--red)';}
  }).catch(function(){msg.textContent='网络错误';msg.style.color='var(--red)';}).finally(function(){btn.disabled=false;});
}

function refreshSessions(){
  fetch('/api/remote/sessions/public').then(function(r){return r.json()}).then(function(d){
    var list=d.sessions||[], tb=G('stb'), empty=G('se');
    if(!tb)return;
    while(tb.firstChild)tb.removeChild(tb.firstChild);
    if(!list.length){
      if(empty)empty.style.display='block';
      return;
    }
    if(empty)empty.style.display='none';
    for(var i=0;i<Math.min(list.length,5);i++){
      var s=list[i];
      var tr=document.createElement('tr');
      var td0=document.createElement('td');td0.textContent=(s.operator_name||'未登记')+'';tr.appendChild(td0);
      var td1=document.createElement('td');td1.textContent=(s.remote_type||'')+'';tr.appendChild(td1);
      var td2=document.createElement('td');td2.textContent=(s.start_time||'')+'';tr.appendChild(td2);
      var td3=document.createElement('td');td3.textContent=(s.end_time||'进行中')+'';tr.appendChild(td3);
      var td4=document.createElement('td');td4.textContent=fmtDur(s.duration_seconds||0);tr.appendChild(td4);
      tb.appendChild(tr);
    }
  }).catch(function(){});
}

function refreshAll(){
  fetch('/api/status').then(function(r){return r.json()}).then(function(s){
    var d=getDisplay(s), rc=s.remote_control;
    var dot=G('sd');
    dot.style.background=d[0]; dot.style.boxShadow='0 0 0 6px '+d[0]+'22';
    T(G('sl'),d[1]); T(G('st'),d[2]);
    T(G('v0'),rc.remote_type||'—');
    T(G('v1'),rc.is_remote?(rc.operator_name||'操作人未登记'):'—');
    T(G('v2'),rc.is_remote&&rc.start_time?rc.start_time:'—');
    T(G('v3'),rc.is_remote?rc.elapsed_formatted:'—');
    T(G('v4'),rc.matched_signals&&rc.matched_signals.length?rc.matched_signals.join(', '):'—');
    T(G('v5'),rc.last_seen_at||s.timestamp||'—');
    T(G('v6'),rc.message||'—');
    T(G('v7'),s.timestamp||'');
    G('eb').style.display='none';
    updateRegistrationForm(rc);
  }).catch(E);
  refreshRegistrationAvailability();
  refreshSessions();
}

var btn=G('rb');if(btn)btn.addEventListener('click',doRegister);
refreshAll();
setInterval(refreshAll,5000);
})();
</script>
</body>
</html>";

        return html;
    }

    private static (string color, string label, string tip) GetDisplay(Models.AppStatus s)
    {
        var rc = s.RemoteControl;
        var st = rc.Status;
        if (st == "error") return ("#d95050", "检测异常", "检测服务异常，请联系管理员");
        if (st == "unknown") return ("#b7791f", "状态未知", "检测尚未完成或未开启");
        if (rc.IsRemote) return ("#d95050", "疑似远程占用", "请勿重复连接，避免控制冲突");
        if (s.ComputerStatus == "in_use") return ("#3b82f6", "本机使用中", "当前有本机使用记录，连接前请确认不会打断他人");
        return ("#15996b", "可连接", "当前未检测到远程占用");
    }

    private static bool IsActive(Models.RemoteSession s)
        => s.IsActive || string.IsNullOrEmpty(s.EndTime);

    private static int ComputeElapsed(string startTime)
    {
        if (DateTime.TryParse(startTime, out var start))
            return (int)(DateTime.Now - start).TotalSeconds;
        return 0;
    }

    private static string EscapeHtml(string s)
    {
        return s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
                .Replace("\"", "&quot;").Replace("'", "&#39;");
    }
}
