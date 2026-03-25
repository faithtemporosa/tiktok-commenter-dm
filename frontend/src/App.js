import { useState, useEffect, useCallback, useRef } from "react";
import "./App.css";
import { supabase } from "./lib/supabase";
import Analytics from "./pages/Analytics";
import Landing from "./pages/Landing";
import Settings from "./pages/Settings";
import {
  MessageCircle, TrendingUp, Calendar, RefreshCw, ExternalLink, Sparkles, BarChart3, Clock,
  Upload, Download, Terminal, Play, Pause, Send, Video, CalendarClock, Settings as SettingsIcon,
  Home, ChevronLeft, Users
} from "lucide-react";

const REFRESH_INTERVAL = 10000;

// Helper to format UTC timestamp to local time
const formatLocalTime = (utcTimestamp) => {
  if (!utcTimestamp) return '';
  const date = new Date(utcTimestamp);
  return date.toLocaleString();
};

function Dashboard({ onNavigate }) {
  const [activeTab, setActiveTab] = useState("comments");
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [totalReports, setTotalReports] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [logs, setLogs] = useState([]);
  const [automationStatus, setAutomationStatus] = useState(null);
  const [logsUpdatedAt, setLogsUpdatedAt] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [dmReports, setDmReports] = useState([]);
  const [dmTotal, setDmTotal] = useState(0);
  const [postReports, setPostReports] = useState([]);
  const [postTotal, setPostTotal] = useState(0);
  const [profileMappings, setProfileMappings] = useState({});
  const [accounts, setAccounts] = useState([]);
  const [accountsTotal, setAccountsTotal] = useState(0);
  const fileInputRef = useRef(null);
  const logsContainerRef = useRef(null);

  // Fetch profile mappings from local bot
  const fetchProfileMappings = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:9000/api/profile-mapping');
      if (res.ok) {
        const data = await res.json();
        setProfileMappings(data);
      }
    } catch (err) {
      // Bot not running, ignore
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const { count: totalCount } = await supabase.from('comment_reports').select('*', { count: 'exact', head: true });
      // Use local midnight for "today" calculation
      const now = new Date();
      const localMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
      const todayISO = localMidnight.toISOString();
      const { count: todayCount } = await supabase.from('comment_reports').select('*', { count: 'exact', head: true }).gte('timestamp', todayISO);
      const weekAgo = new Date(localMidnight); weekAgo.setDate(weekAgo.getDate() - 7);
      const { count: weekCount } = await supabase.from('comment_reports').select('*', { count: 'exact', head: true }).gte('timestamp', weekAgo.toISOString());
      const monthAgo = new Date(localMidnight); monthAgo.setMonth(monthAgo.getMonth() - 1);
      const { count: monthCount } = await supabase.from('comment_reports').select('*', { count: 'exact', head: true }).gte('timestamp', monthAgo.toISOString());
      const { data: todayBrandData } = await supabase.from('comment_reports').select('sheet').gte('timestamp', todayISO);
      const todayByBrand = {};
      todayBrandData?.forEach(r => { if (r.sheet) todayByBrand[r.sheet] = (todayByBrand[r.sheet] || 0) + 1; });
      const { count: dmCount } = await supabase.from('dm_reports').select('*', { count: 'exact', head: true });
      const { count: dmTodayCount } = await supabase.from('dm_reports').select('*', { count: 'exact', head: true }).gte('timestamp', today.toISOString());
      const { count: postCount } = await supabase.from('post_reports').select('*', { count: 'exact', head: true });
      const { count: postTodayCount } = await supabase.from('post_reports').select('*', { count: 'exact', head: true }).gte('timestamp', today.toISOString());
      setStats({
        total_comments: totalCount || 0, today_comments: todayCount || 0, week_comments: weekCount || 0, month_comments: monthCount || 0,
        today_by_brand: todayByBrand, dm_total: dmCount || 0, dm_today: dmTodayCount || 0, post_total: postCount || 0, post_today: postTodayCount || 0
      });
    } catch (err) { console.error("Stats error:", err); }
  }, []);

  const fetchReports = useCallback(async () => {
    try {
      let query = supabase.from('comment_reports').select('*', { count: 'exact' }).order('timestamp', { ascending: false }).limit(100);
      if (startDate) query = query.gte('timestamp', new Date(startDate).toISOString());
      if (endDate) { const end = new Date(endDate); end.setHours(23, 59, 59, 999); query = query.lte('timestamp', end.toISOString()); }
      if (!startDate && !endDate) {
        if (filter === "today") { const t = new Date(); t.setHours(0,0,0,0); query = query.gte('timestamp', t.toISOString()); }
        else if (filter === "week") { const w = new Date(); w.setDate(w.getDate()-7); query = query.gte('timestamp', w.toISOString()); }
        else if (filter === "month") { const m = new Date(); m.setMonth(m.getMonth()-1); query = query.gte('timestamp', m.toISOString()); }
      }
      const { data, count } = await query;
      setReports(data || []); setTotalReports(count || 0); setLastUpdated(new Date());
    } catch (err) { console.error("Reports error:", err); }
  }, [filter, startDate, endDate]);

  const fetchDmReports = useCallback(async () => {
    try {
      const { data, count } = await supabase.from('dm_reports').select('*', { count: 'exact' }).order('timestamp', { ascending: false }).limit(100);
      setDmReports(data || []); setDmTotal(count || 0);
    } catch (err) { console.error("DM error:", err); }
  }, []);

  const fetchPostReports = useCallback(async () => {
    try {
      const { data, count } = await supabase.from('post_reports').select('*', { count: 'exact' }).order('timestamp', { ascending: false }).limit(100);
      setPostReports(data || []); setPostTotal(count || 0);
    } catch (err) { console.error("Post error:", err); }
  }, []);

  const fetchAccounts = useCallback(async () => {
    try {
      const { data, count } = await supabase.from('tiktok_accounts').select('*', { count: 'exact' }).order('browser_num', { ascending: true });
      setAccounts(data || []); setAccountsTotal(count || 0);
    } catch (err) { console.error("Accounts error:", err); }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const { data } = await supabase.from('live_logs').select('*').eq('id', '00000000-0000-0000-0000-000000000001').maybeSingle();
      if (data) { setLogs(data.logs || []); setAutomationStatus(data.status || null); setLogsUpdatedAt(data.updated_at); }
    } catch (err) { console.error("Logs error:", err); }
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchStats(), fetchReports(), fetchLogs(), fetchDmReports(), fetchPostReports(), fetchProfileMappings(), fetchAccounts()]);
    setLoading(false);
  }, [fetchStats, fetchReports, fetchLogs, fetchDmReports, fetchPostReports, fetchProfileMappings, fetchAccounts]);

  const handleFileImport = async (event) => {
    const file = event.target.files[0]; if (!file) return;
    setImporting(true); setImportResult(null);
    try {
      const text = await file.text(); const data = JSON.parse(text);
      const reportsToInsert = data.reports || data;
      let inserted = 0, skipped = 0;
      for (const report of reportsToInsert) {
        const { error } = await supabase.from('comment_reports').insert({
          timestamp: report.timestamp, profile: report.profile, video_url: report.video_url, video_id: report.video_id, comment: report.comment, sheet: report.sheet
        });
        if (error) { if (error.code === '23505') skipped++; } else inserted++;
      }
      setImportResult({ success: true, message: `Imported ${inserted} comments (${skipped} duplicates skipped)` });
      await fetchAll();
    } catch (err) { setImportResult({ success: false, message: "Failed to import. Make sure it's a valid JSON file." }); }
    finally { setImporting(false); if (fileInputRef.current) fileInputRef.current.value = ""; }
  };

  const handleExport = async () => {
    try {
      let query = supabase.from('comment_reports').select('*').order('timestamp', { ascending: false });
      if (filter === "today") { const t = new Date(); t.setHours(0,0,0,0); query = query.gte('timestamp', t.toISOString()); }
      else if (filter === "week") { const w = new Date(); w.setDate(w.getDate()-7); query = query.gte('timestamp', w.toISOString()); }
      else if (filter === "month") { const m = new Date(); m.setMonth(m.getMonth()-1); query = query.gte('timestamp', m.toISOString()); }
      const { data } = await query;
      const headers = ['timestamp','profile','tiktok_username','comment','search_query','sheet','video_url','video_id'];
      const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${(row[h]||'').toString().replace(/"/g,'""')}"`).join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' }); const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `comments_${new Date().toISOString().split('T')[0]}.csv`; a.click(); URL.revokeObjectURL(url);
    } catch (err) { console.error('Export error:', err); }
  };

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useEffect(() => { fetchReports(); }, [startDate, endDate, fetchReports]);
  useEffect(() => {
    const ch1 = supabase.channel('cr').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'comment_reports' }, () => { fetchStats(); fetchReports(); }).subscribe();
    const ch2 = supabase.channel('ll').on('postgres_changes', { event: '*', schema: 'public', table: 'live_logs' }, () => fetchLogs()).subscribe();
    const ch3 = supabase.channel('dm').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'dm_reports' }, () => { fetchDmReports(); fetchStats(); }).subscribe();
    const ch4 = supabase.channel('pr').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'post_reports' }, () => { fetchPostReports(); fetchStats(); }).subscribe();
    return () => { [ch1,ch2,ch3,ch4].forEach(c => supabase.removeChannel(c)); };
  }, [fetchStats, fetchReports, fetchLogs, fetchDmReports, fetchPostReports]);
  useEffect(() => {
    if (!autoRefresh) return;
    const iv = setInterval(() => { fetchStats(); fetchReports(); fetchLogs(); fetchDmReports(); fetchPostReports(); }, REFRESH_INTERVAL);
    return () => clearInterval(iv);
  }, [autoRefresh, fetchStats, fetchReports, fetchLogs, fetchDmReports, fetchPostReports]);
  useEffect(() => { if (logsContainerRef.current) logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight; }, [logs]);

  const fmt = (ts) => {
    if (!ts) return "-";
    // Ensure UTC timestamp is properly converted to local time
    const date = new Date(ts);
    return date.toLocaleString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  };
  const trunc = (c, m = 50) => !c ? "-" : c.length > m ? c.substring(0, m) + "..." : c;
  const brandColor = (s) => s === "Bump Connect" ? "text-emerald-400 bg-emerald-500/20" : s === "Kollabsy" ? "text-violet-400 bg-violet-500/20" : s === "Bump Syndicate" ? "text-amber-400 bg-amber-500/20" : "text-zinc-400 bg-zinc-500/20";
  const logColor = (m) => m.includes("\u2717") || m.includes("Error") || m.includes("Failed") ? "text-red-400" : m.includes("\u2713") || m.includes("SUCCESS") || m.includes("Completed") ? "text-emerald-400" : m.includes("\u26A0") ? "text-amber-400" : m.includes("\u2192") || m.includes("Starting") ? "text-blue-400" : "text-zinc-400";

  const tabs = [
    { id: "comments", label: "Comments", icon: MessageCircle, count: stats?.total_comments },
    { id: "dms", label: "DMs", icon: Send, count: stats?.dm_total },
    { id: "posts", label: "Posts", icon: Video, count: stats?.post_total },
    { id: "accounts", label: "Accounts", icon: Users, count: accountsTotal },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "logs", label: "Live Logs", icon: Terminal },
    { id: "settings", label: "Settings", icon: SettingsIcon }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => onNavigate("landing")} className="text-zinc-500 hover:text-zinc-300 transition-colors" data-testid="back-to-home"><ChevronLeft className="w-5 h-5" /></button>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-violet-500/20"><MessageCircle className="w-5 h-5 text-white" /></div>
            <div><h1 className="text-lg font-bold" data-testid="app-title">TikTok Dashboard</h1><p className="text-zinc-500 text-xs">Real-time reporting</p></div>
          </div>
          <div className="flex items-center gap-3">
            <input type="file" ref={fileInputRef} onChange={handleFileImport} accept=".json" className="hidden" />
            <button onClick={() => fileInputRef.current?.click()} disabled={importing} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs transition-all disabled:opacity-50" data-testid="import-btn"><Upload className={`w-3.5 h-3.5 ${importing?"animate-pulse":""}`} />{importing?"...":"Import"}</button>
            <button onClick={handleExport} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-xs transition-all" data-testid="export-btn"><Download className="w-3.5 h-3.5" />CSV</button>
            <button onClick={() => setAutoRefresh(!autoRefresh)} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs transition-all ${autoRefresh?"bg-emerald-500/20 text-emerald-400 border border-emerald-500/30":"bg-zinc-800 text-zinc-400 border border-zinc-700"}`} data-testid="auto-refresh-toggle">
              <RefreshCw className={`w-3.5 h-3.5 ${autoRefresh?"animate-spin":""}`} style={{animationDuration:"3s"}} />{autoRefresh?"Live":"Paused"}</button>
            <button onClick={fetchAll} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs transition-all" data-testid="refresh-btn"><RefreshCw className="w-3.5 h-3.5" />Refresh</button>
            {lastUpdated && <span className="text-xs text-zinc-500"><Clock className="w-3 h-3 inline mr-1" />{lastUpdated.toLocaleTimeString()}</span>}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {importResult && (
          <div className={`mb-4 p-3 rounded-xl border text-sm ${importResult.success?"bg-emerald-500/10 border-emerald-500/30 text-emerald-400":"bg-red-500/10 border-red-500/30 text-red-400"}`} data-testid="import-result">
            {importResult.message} <button onClick={() => setImportResult(null)} className="float-right text-xs opacity-70 hover:opacity-100">Dismiss</button>
          </div>
        )}

        {/* Target Config */}
        <div className="bg-gradient-to-r from-violet-900/30 via-fuchsia-900/20 to-violet-900/30 border border-violet-500/30 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-6">
              <div className="text-center"><div className="text-2xl font-bold">{accountsTotal.toLocaleString()}</div><div className="text-xs text-zinc-400">Profiles</div></div>
              <div className="text-center"><div className="text-2xl font-bold">10</div><div className="text-xs text-zinc-400">Videos/Profile</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-emerald-400">{(accountsTotal * 10).toLocaleString()}</div><div className="text-xs text-zinc-400">Daily Target</div></div>
            </div>
            <div className="flex gap-2 text-xs">
              <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400">Bump Connect</span>
              <span className="px-2 py-1 rounded bg-violet-500/20 text-violet-400">Kollabsy</span>
              <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400">Bump Syndicate</span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          {[
            { label: "This Month", value: stats?.month_comments, icon: Calendar, color: "violet" },
            { label: "This Week", value: stats?.week_comments, icon: TrendingUp, color: "blue" },
            { label: "Today", value: stats?.today_comments, icon: Sparkles, color: "emerald" },
            { label: "All Comments", value: stats?.total_comments, icon: MessageCircle, color: "zinc" },
            { label: "DMs Sent", value: stats?.dm_total, icon: Send, color: "cyan" },
            { label: "Posts Made", value: stats?.post_total, icon: Video, color: "rose" }
          ].map((s, i) => (
            <div key={i} className={`bg-gradient-to-br from-${s.color}-900/40 to-${s.color}-900/20 border border-${s.color}-500/30 rounded-xl p-3`} data-testid={`stat-${s.label.toLowerCase().replace(/\s/g,'-')}`}>
              <div className="flex items-center gap-2 mb-1"><s.icon className={`w-4 h-4 text-${s.color}-400`} /><span className="text-xl font-bold">{(s.value || 0).toLocaleString()}</span></div>
              <p className="text-xs text-zinc-500">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-zinc-900 p-1 rounded-xl overflow-x-auto" data-testid="tab-nav">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${activeTab === tab.id?"bg-violet-600 text-white shadow-lg shadow-violet-500/20":"text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"}`}
              data-testid={`tab-${tab.id}`}>
              <tab.icon className="w-3.5 h-3.5" />{tab.label}
              {tab.count !== undefined && <span className={`text-xs px-1.5 py-0.5 rounded-full ${activeTab===tab.id?"bg-white/20":"bg-zinc-800"}`}>{(tab.count||0).toLocaleString()}</span>}
            </button>
          ))}
        </div>

        {/* COMMENTS */}
        {activeTab === "comments" && (
          <div data-testid="comments-tab">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4">
              <div className="flex items-center gap-3 flex-wrap">
                <Calendar className="w-4 h-4 text-zinc-400" /><span className="text-sm text-zinc-400">Date Range:</span>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs" />
                <span className="text-zinc-500">to</span>
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs" />
                <button onClick={() => { setStartDate(""); setEndDate(""); setFilter("all"); }} className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-xs">Clear</button>
              </div>
            </div>
            {stats?.today_by_brand && Object.keys(stats.today_by_brand).length > 0 && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-6">
                <div className="flex items-center gap-2 mb-3"><BarChart3 className="w-4 h-4 text-zinc-400" /><h3 className="text-sm font-semibold">Today's Comments by Brand</h3></div>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(stats.today_by_brand).map(([brand, count]) => (
                    <div key={brand} className={`rounded-lg p-4 ${brandColor(brand)}`}><div className="text-2xl font-bold">{count}</div><div className="text-sm opacity-80">{brand}</div></div>
                  ))}
                </div>
              </div>
            )}
            <div className="mb-3 text-sm text-zinc-500">Showing {reports.length} of {totalReports} comments</div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="reports-table">
                <thead className="bg-zinc-800/50"><tr>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Time</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Profile</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Username</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Comment</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Brand</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Search</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Video</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Proof</th>
                </tr></thead>
                <tbody>
                  {loading ? <tr><td colSpan="8" className="text-center py-12 text-zinc-500"><RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />Loading...</td></tr>
                  : reports.length === 0 ? <tr><td colSpan="8" className="text-center py-12 text-zinc-500">No comments yet</td></tr>
                  : reports.map((r, i) => (
                    <tr key={r.id||i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`report-row-${i}`}>
                      <td className="px-4 py-3 whitespace-nowrap text-zinc-400 text-xs">{fmt(r.timestamp)}</td>
                      <td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs">{r.profile}</span></td>
                      <td className="px-4 py-3">{r.tiktok_username ? <a href={`https://www.tiktok.com/@${r.tiktok_username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs"><ExternalLink className="w-3 h-3" />@{r.tiktok_username}</a> : <span className="text-zinc-600 text-xs">-</span>}</td>
                      <td className="px-4 py-3 max-w-md text-zinc-300 text-xs" title={r.comment}>{trunc(r.comment, 60)}</td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${brandColor(r.sheet)}`}>{r.sheet}</span></td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${r.search_query === 'FYP' ? 'text-amber-400 bg-amber-500/20' : 'text-blue-400 bg-blue-500/20'}`}>{r.search_query || 'FYP'}</span></td>
                      <td className="px-4 py-3"><a href={r.video_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-violet-400 hover:text-violet-300 text-xs"><ExternalLink className="w-3 h-3" />View</a></td>
                      <td className="px-4 py-3">{r.screenshot ? <a href={r.screenshot.startsWith('http') ? r.screenshot : `http://localhost:9000/screenshots/${r.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : r.video_url ? <a href={r.video_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-amber-400 hover:text-amber-300 text-xs">🔗 Video</a> : <span className="text-zinc-600 text-xs">-</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* DMS */}
        {activeTab === "dms" && (
          <div data-testid="dms-tab">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-cyan-400">{(stats?.dm_total||0).toLocaleString()}</div><div className="text-xs text-zinc-500">Total DMs</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-emerald-400">{(stats?.dm_today||0).toLocaleString()}</div><div className="text-xs text-zinc-500">Today</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-violet-400">{new Set(dmReports.map(d=>d.username)).size}</div><div className="text-xs text-zinc-500">Unique Recipients</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-white">{new Set(dmReports.map(d=>d.profile)).size}</div><div className="text-xs text-zinc-500">Profiles Used</div></div>
            </div>
            <div className="mb-3 text-sm text-zinc-500">Showing {dmReports.length} of {dmTotal} DMs</div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="dm-table">
                <thead className="bg-zinc-800/50"><tr><th className="text-left px-4 py-3 font-medium text-zinc-400">Time</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Profile</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Recipient</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Message</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Status</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Proof</th></tr></thead>
                <tbody>{dmReports.length===0?<tr><td colSpan="6" className="text-center py-12 text-zinc-500"><Send className="w-6 h-6 mx-auto mb-2 opacity-50" />No DMs sent yet</td></tr>
                  :dmReports.map((dm,i)=><tr key={dm.id||i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`dm-row-${i}`}><td className="px-4 py-3 text-zinc-400 text-xs">{fmt(dm.timestamp)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs">{dm.profile}</span></td><td className="px-4 py-3"><a href={dm.profile_url || `https://www.tiktok.com/@${dm.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs"><ExternalLink className="w-3 h-3" />@{dm.username}</a></td><td className="px-4 py-3 text-zinc-300 text-xs max-w-md">{trunc(dm.message,60)}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${dm.status==='sent'?'text-emerald-400 bg-emerald-500/20':'text-red-400 bg-red-500/20'}`}>{dm.status}</span></td><td className="px-4 py-3">{dm.screenshot ? <a href={dm.screenshot.startsWith('http') ? dm.screenshot : `http://localhost:9000/screenshots/${dm.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : <span className="text-zinc-600 text-xs">-</span>}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        )}

        {/* POSTS */}
        {activeTab === "posts" && (
          <div data-testid="posts-tab">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-rose-400">{(stats?.post_total||0).toLocaleString()}</div><div className="text-xs text-zinc-500">Total Posts</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-emerald-400">{(stats?.post_today||0).toLocaleString()}</div><div className="text-xs text-zinc-500">Today</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-violet-400">{new Set(postReports.map(p=>p.profile)).size}</div><div className="text-xs text-zinc-500">Profiles</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-amber-400 flex items-center justify-center gap-1"><CalendarClock className="w-5 h-5" /></div><div className="text-xs text-zinc-500">Scheduler Active</div></div>
            </div>
            <div className="mb-3 text-sm text-zinc-500">Showing {postReports.length} of {postTotal} posts</div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="post-table">
                <thead className="bg-zinc-800/50"><tr><th className="text-left px-4 py-3 font-medium text-zinc-400">Time</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Profile</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Repost</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Caption</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Status</th><th className="text-left px-4 py-3 font-medium text-zinc-400">Proof</th></tr></thead>
                <tbody>{postReports.length===0?<tr><td colSpan="6" className="text-center py-12 text-zinc-500"><Video className="w-6 h-6 mx-auto mb-2 opacity-50" />No posts yet</td></tr>
                  :postReports.map((p,i)=>{const mappedUsername = p.tiktok_username || profileMappings[p.profile]; const repostLink = p.repost_url || (mappedUsername && `https://www.tiktok.com/@${mappedUsername}?tab=reposts`); return <tr key={p.id||i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`post-row-${i}`}><td className="px-4 py-3 text-zinc-400 text-xs">{fmt(p.timestamp)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs">{p.profile}</span></td><td className="px-4 py-3">{repostLink?<a href={repostLink} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-rose-400 hover:text-rose-300 text-xs"><ExternalLink className="w-3 h-3" />@{mappedUsername || 'View'}</a>:<span className="text-zinc-500 text-xs">Set in Settings</span>}</td><td className="px-4 py-3 text-zinc-300 text-xs max-w-md">{trunc(p.caption,60)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded text-xs text-emerald-400 bg-emerald-500/20">{p.status}</span></td><td className="px-4 py-3">{p.screenshot ? <a href={p.screenshot.startsWith('http') ? p.screenshot : `http://localhost:9000/screenshots/${p.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : <span className="text-zinc-600 text-xs">-</span>}</td></tr>})}</tbody>
              </table>
            </div>
          </div>
        )}

        {/* ACCOUNTS */}
        {activeTab === "accounts" && (
          <div data-testid="accounts-tab">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-violet-400">{accountsTotal.toLocaleString()}</div><div className="text-xs text-zinc-500">Total Accounts</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-emerald-400">{accounts.filter(a=>a.status==='active').length}</div><div className="text-xs text-zinc-500">Active</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-amber-400">{accounts.filter(a=>a.status==='suspended').length}</div><div className="text-xs text-zinc-500">Suspended</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-cyan-400">{new Set(accounts.map(a=>a.email?.split('@')[1])).size}</div><div className="text-xs text-zinc-500">Email Domains</div></div>
            </div>
            <div className="mb-3 text-sm text-zinc-500">Showing {accounts.length} accounts</div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="accounts-table">
                <thead className="bg-zinc-800/50"><tr>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Browser</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Email</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Password</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Username</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Birthdate</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Created</th>
                </tr></thead>
                <tbody>
                  {accounts.length === 0 ? <tr><td colSpan="7" className="text-center py-12 text-zinc-500"><Users className="w-6 h-6 mx-auto mb-2 opacity-50" />No accounts yet. Run import script to add accounts.</td></tr>
                  : accounts.map((acc, i) => (
                    <tr key={acc.id || i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`account-row-${i}`}>
                      <td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-400 text-xs font-mono">{acc.browser_num}</span></td>
                      <td className="px-4 py-3 text-zinc-300 text-xs font-mono">{acc.email}</td>
                      <td className="px-4 py-3 text-zinc-400 text-xs font-mono">{acc.password}</td>
                      <td className="px-4 py-3">{acc.username ? <a href={`https://www.tiktok.com/@${acc.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs"><ExternalLink className="w-3 h-3" />@{acc.username}</a> : <span className="text-zinc-600 text-xs">-</span>}</td>
                      <td className="px-4 py-3 text-zinc-400 text-xs">{acc.birthdate || '-'}</td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${acc.status==='active'?'text-emerald-400 bg-emerald-500/20':acc.status==='suspended'?'text-red-400 bg-red-500/20':'text-zinc-400 bg-zinc-500/20'}`}>{acc.status}</span></td>
                      <td className="px-4 py-3 text-zinc-500 text-xs">{acc.created_at ? new Date(acc.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ANALYTICS */}
        {activeTab === "analytics" && <Analytics />}

        {/* LOGS */}
        {activeTab === "logs" && (
          <div data-testid="logs-tab">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="bg-zinc-800/50 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3"><Terminal className="w-4 h-4 text-zinc-400" /><h3 className="text-sm font-semibold">Live Automation Logs</h3>
                  {automationStatus?.running?<span className="flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-xs"><Play className="w-3 h-3" />Running</span>
                  :<span className="flex items-center gap-1 px-2 py-1 rounded bg-zinc-700 text-zinc-400 text-xs"><Pause className="w-3 h-3" />Idle</span>}</div>
                <div className="text-xs text-zinc-500">{logsUpdatedAt && `Last: ${new Date(logsUpdatedAt).toLocaleTimeString()}`}</div>
              </div>
              {automationStatus?.running && (
                <div className="px-4 py-2 bg-zinc-800/30 border-b border-zinc-800">
                  <div className="flex items-center gap-4 text-xs"><span className="text-zinc-400">Current: <span className="text-white font-medium">{automationStatus.current_profile||"..."}</span></span><span className="text-zinc-400">Comments: <span className="text-emerald-400 font-medium">{automationStatus.comments_posted||0}</span></span></div>
                  <div className="mt-1.5 h-1 bg-zinc-700 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all" style={{width:`${automationStatus.total?(automationStatus.progress/automationStatus.total)*100:0}%`}} /></div>
                </div>
              )}
              <div ref={logsContainerRef} className="h-96 overflow-y-auto p-4 font-mono text-xs" data-testid="logs-container">
                {logs.length===0?<div className="text-center text-zinc-500 py-8"><Terminal className="w-6 h-6 mx-auto mb-2 opacity-50" />No logs yet</div>
                :logs.map((log,i)=><div key={i} className={`py-0.5 ${logColor(log.message)}`}><span className="text-zinc-600 mr-2">[{log.timestamp}]</span>{log.message}</div>)}
              </div>
            </div>
          </div>
        )}

        {/* SETTINGS */}
        {activeTab === "settings" && <Settings />}

        <div className="mt-6 text-center text-xs text-zinc-600">
          <p>Data syncs every 10s when live | Promoting: Bump Connect | Kollabsy | Bump Syndicate</p>
        </div>
      </main>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("dashboard");
  const [checkoutResult, setCheckoutResult] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (sessionId) {
      setCheckoutResult({ sessionId, checking: true });
      pollPaymentStatus(sessionId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    if (attempts >= 5) { setCheckoutResult({ sessionId, status: "timeout" }); return; }
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/billing/status/${sessionId}`);
      const data = await res.json();
      if (data.payment_status === "paid") { setCheckoutResult({ sessionId, status: "success", plan: data.metadata?.plan_name }); setPage("dashboard"); return; }
      if (data.status === "expired") { setCheckoutResult({ sessionId, status: "expired" }); return; }
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
    } catch (err) { setCheckoutResult({ sessionId, status: "error" }); }
  };

  return (
    <>
      {checkoutResult && checkoutResult.status === "success" && (
        <div className="fixed top-4 right-4 z-[100] bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 px-4 py-3 rounded-xl text-sm shadow-lg" data-testid="payment-success">
          Payment successful! Upgraded to {checkoutResult.plan}
          <button onClick={() => { setCheckoutResult(null); window.history.replaceState({}, '', window.location.pathname); }} className="ml-3 opacity-70 hover:opacity-100">Dismiss</button>
        </div>
      )}
      {page === "landing" ? <Landing onNavigate={setPage} /> : <Dashboard onNavigate={setPage} />}
    </>
  );
}

export default App;
