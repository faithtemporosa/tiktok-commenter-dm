import { useState, useEffect, useCallback, useRef } from "react";
import "./App.css";
import { supabase } from "./lib/supabase";
import Analytics from "./pages/Analytics";
import Landing from "./pages/Landing";
import Settings from "./pages/Settings";
import {
  MessageCircle, TrendingUp, Calendar, RefreshCw, ExternalLink, Sparkles, BarChart3, Clock,
  Upload, Download, Terminal, Play, Pause, Send, Video, CalendarClock, Settings as SettingsIcon,
  Home, ChevronLeft, Users, Target, Eye, Heart
} from "lucide-react";

const REFRESH_INTERVAL = 10000;
const BOT_API_URL = process.env.REACT_APP_BOT_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:9000';

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
  const [targetStats, setTargetStats] = useState({ accounts: [], totals: { views: 0, comments: 0, browsers: 0 } });
  const [targetLogs, setTargetLogs] = useState([]);
  const [targetRunning, setTargetRunning] = useState(false);
  const [targetCommentHistory, setTargetCommentHistory] = useState([]);
  const [scriptStatuses, setScriptStatuses] = useState({});
  const [scriptLogs, setScriptLogs] = useState({});
  const [signupStatus, setSignupStatus] = useState(null);
  const [warmupSettings, setWarmupSettings] = useState({ num: 20, videos: 10, start: 1 });
  const fileInputRef = useRef(null);
  const logsContainerRef = useRef(null);
  const targetLogsRef = useRef(null);

  // Fetch profile mappings from local bot
  const fetchProfileMappings = useCallback(async () => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/profile-mapping`);
      if (res.ok) {
        const data = await res.json();
        setProfileMappings(data);
      }
    } catch (err) {
      // Bot not running, ignore
    }
  }, []);

  // Fetch target accounts stats from Supabase
  const fetchTargetStats = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('target_account_stats')
        .select('*')
        .order('total_comments', { ascending: false });

      if (error) throw error;

      const accounts = (data || []).map(row => ({
        name: row.account,
        views: row.total_views || 0,
        comments: row.total_comments || 0,
        browsers_engaged: row.browsers_engaged || 0,
        last_updated: row.last_updated || ''
      }));

      const totals = {
        views: accounts.reduce((sum, a) => sum + a.views, 0),
        comments: accounts.reduce((sum, a) => sum + a.comments, 0),
        browsers: Math.max(...accounts.map(a => a.browsers_engaged), 0)
      };

      setTargetStats({ accounts, totals });
    } catch (err) {
      console.error('Error fetching target stats:', err);
    }
  }, []);

  // Fetch target accounts logs from local bot
  const fetchTargetLogs = useCallback(async () => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/target-accounts/logs?lines=100`);
      if (res.ok) {
        const data = await res.json();
        setTargetLogs(data.logs || []);
        setTargetRunning(data.running || false);
        // Auto-scroll to bottom
        if (targetLogsRef.current) {
          targetLogsRef.current.scrollTop = targetLogsRef.current.scrollHeight;
        }
      }
    } catch (err) {
      // Bot not running, ignore
    }
  }, []);

  // Fetch target comment history from Supabase
  const fetchTargetCommentHistory = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('target_comment_history')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(100);

      if (!error && data) {
        setTargetCommentHistory(data);
      }
    } catch (err) {
      console.error('Error fetching comment history:', err);
    }
  }, []);

  const fetchScriptStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/scripts/status`);
      if (!res.ok) return;
      const data = await res.json();
      const byKey = {};
      (data.scripts || []).forEach(s => { byKey[s.key] = s; });
      setScriptStatuses(byKey);
    } catch (err) {
      // Local bot not running, ignore
    }
  }, []);

  const fetchScriptLog = useCallback(async (key) => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/scripts/${key}/log?lines=100`);
      if (!res.ok) return;
      const data = await res.json();
      setScriptLogs(prev => ({ ...prev, [key]: data.lines || [] }));
    } catch (err) {
      // Local bot not running, ignore
    }
  }, []);

  const startScript = useCallback(async (key, options = {}) => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/scripts/${key}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options)
      });
      await res.json().catch(() => ({}));
      await fetchScriptStatus();
      await fetchScriptLog(key);
    } catch (err) {
      console.error(`Error starting ${key}:`, err);
    }
  }, [fetchScriptStatus, fetchScriptLog]);

  const stopScript = useCallback(async (key) => {
    try {
      await fetch(`${BOT_API_URL}/api/scripts/${key}/stop`, { method: 'POST' });
      await fetchScriptStatus();
      await fetchScriptLog(key);
    } catch (err) {
      console.error(`Error stopping ${key}:`, err);
    }
  }, [fetchScriptStatus, fetchScriptLog]);

  const fetchSignupStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BOT_API_URL}/api/signup/status`);
      if (!res.ok) return;
      setSignupStatus(await res.json());
    } catch (err) {
      // Local bot not running, ignore
    }
  }, []);

  const startSignup = useCallback(async () => {
    try {
      const listRes = await fetch(`${BOT_API_URL}/api/signup/not-logged-in`);
      const list = listRes.ok ? await listRes.json() : { browsers: [] };
      const profiles = (list.browsers || []).map(b => b.profile).filter(Boolean);
      if (profiles.length === 0) {
        setSignupStatus(prev => ({
          ...(prev || {}),
          running: false,
          logs: [...((prev && prev.logs) || []), "No not-logged-in profiles found."]
        }));
        return;
      }
      await fetch(`${BOT_API_URL}/api/signup/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profiles })
      });
      await fetchSignupStatus();
    } catch (err) {
      console.error('Error starting signup:', err);
    }
  }, [fetchSignupStatus]);

  const stopSignup = useCallback(async () => {
    try {
      await fetch(`${BOT_API_URL}/api/signup/stop`, { method: 'POST' });
      await fetchSignupStatus();
    } catch (err) {
      console.error('Error stopping signup:', err);
    }
  }, [fetchSignupStatus]);

  const fetchStats = useCallback(async () => {
    try {
      // Use local midnight for "today" calculation
      const now = new Date();
      const localMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
      // Use date-only format to match bot's timestamp format (YYYY-MM-DD HH:MM:SS)
      const todayISO = now.toISOString().split('T')[0]; // Just the date part: 2026-04-01
      const weekAgo = new Date(localMidnight); weekAgo.setDate(weekAgo.getDate() - 7);
      const weekISO = weekAgo.toISOString().split('T')[0];
      const monthAgo = new Date(localMidnight); monthAgo.setMonth(monthAgo.getMonth() - 1);
      const monthISO = monthAgo.toISOString().split('T')[0];

      // Fetch counts (removed head:true for compatibility)
      const [totalRes, todayRes, weekRes, monthRes, dmRes, dmTodayRes, postRes, postTodayRes, brandRes] = await Promise.all([
        supabase.from('comment_reports').select('id', { count: 'exact' }),
        supabase.from('comment_reports').select('id', { count: 'exact' }).gte('timestamp', todayISO),
        supabase.from('comment_reports').select('id', { count: 'exact' }).gte('timestamp', weekISO),
        supabase.from('comment_reports').select('id', { count: 'exact' }).gte('timestamp', monthISO),
        supabase.from('dm_reports').select('id', { count: 'exact' }),
        supabase.from('dm_reports').select('id', { count: 'exact' }).gte('timestamp', todayISO),
        supabase.from('post_reports').select('id', { count: 'exact' }),
        supabase.from('post_reports').select('id', { count: 'exact' }).gte('timestamp', todayISO),
        supabase.from('comment_reports').select('sheet').gte('timestamp', todayISO)
      ]);

      const todayByBrand = {};
      brandRes.data?.forEach(r => { if (r.sheet) todayByBrand[r.sheet] = (todayByBrand[r.sheet] || 0) + 1; });

      setStats({
        total_comments: totalRes.count || 0, today_comments: todayRes.count || 0, week_comments: weekRes.count || 0, month_comments: monthRes.count || 0,
        today_by_brand: todayByBrand, dm_total: dmRes.count || 0, dm_today: dmTodayRes.count || 0, post_total: postRes.count || 0, post_today: postTodayRes.count || 0
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
      // Fetch from tiktok_account_history (all accounts ever used per browser)
      const { data, count } = await supabase.from('tiktok_account_history').select('*', { count: 'exact' }).order('last_seen', { ascending: false });
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
    await Promise.all([fetchStats(), fetchReports(), fetchLogs(), fetchDmReports(), fetchPostReports(), fetchProfileMappings(), fetchAccounts(), fetchTargetStats(), fetchTargetLogs(), fetchTargetCommentHistory(), fetchScriptStatus(), fetchSignupStatus()]);
    setLoading(false);
  }, [fetchStats, fetchReports, fetchLogs, fetchDmReports, fetchPostReports, fetchProfileMappings, fetchAccounts, fetchTargetStats, fetchTargetLogs, fetchTargetCommentHistory, fetchScriptStatus, fetchSignupStatus]);

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
    const iv = setInterval(() => { fetchStats(); fetchReports(); fetchLogs(); fetchDmReports(); fetchPostReports(); fetchScriptStatus(); fetchSignupStatus(); }, REFRESH_INTERVAL);
    return () => clearInterval(iv);
  }, [autoRefresh, fetchStats, fetchReports, fetchLogs, fetchDmReports, fetchPostReports, fetchScriptStatus, fetchSignupStatus]);
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
  const scriptLogColor = (m) => (m || '').includes('FAILED') || (m || '').includes('Error') || (m || '').includes('\u2717') ? 'text-red-400' : (m || '').includes('\u2713') || (m || '').includes('COMPLETE') || (m || '').includes('Started') ? 'text-emerald-400' : 'text-zinc-400';

  const tabs = [
    { id: "comments", label: "Comments", icon: MessageCircle, count: stats?.total_comments },
    { id: "warmup", label: "Warmup", icon: Sparkles },
    { id: "signup", label: "Signup", icon: Users },
    { id: "proxy", label: "Proxy Fix", icon: RefreshCw },
    { id: "scheduler", label: "Scheduler", icon: CalendarClock },
    { id: "timer", label: "Timer", icon: Clock },
    { id: "targets", label: "Targets", icon: Target, count: targetStats?.accounts?.length },
    { id: "dms", label: "DMs", icon: Send, count: stats?.dm_total },
    { id: "posts", label: "Posts", icon: Video, count: stats?.post_total },
    { id: "accounts", label: "Accounts", icon: Users, count: accountsTotal },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "logs", label: "Live Logs", icon: Terminal },
    { id: "settings", label: "Settings", icon: SettingsIcon }
  ];

  const scriptPanel = ({ keyName, title, icon: Icon, description, children, externalUrl }) => {
    const isSignup = keyName === "signup";
    const status = isSignup ? (signupStatus || {}) : (scriptStatuses[keyName] || {});
    const running = !!status.running;
    const lines = isSignup ? (signupStatus?.logs || []) : (scriptLogs[keyName] || []);
    return (
      <div data-testid={`${keyName}-script-tab`}>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Icon className="w-5 h-5 text-violet-400" />
            <div>
              <div className="font-medium">{title}</div>
              <div className="text-xs text-zinc-500">{description}</div>
            </div>
            <span className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${running ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'}`}>
              {running ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}{running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {children}
            {externalUrl && !isSignup && <a href={externalUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-xs transition-all"><ExternalLink className="w-3.5 h-3.5" />Open</a>}
            {!running ? (
              <button onClick={() => isSignup ? startSignup() : startScript(keyName, keyName === 'warmup' ? warmupSettings : {})} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs transition-all"><Play className="w-3.5 h-3.5" />Start</button>
            ) : (
              <button onClick={() => isSignup ? stopSignup() : stopScript(keyName)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-xs transition-all"><Pause className="w-3.5 h-3.5" />Stop</button>
            )}
            <button onClick={() => isSignup ? fetchSignupStatus() : fetchScriptLog(keyName)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs transition-all"><RefreshCw className="w-3.5 h-3.5" />Log</button>
          </div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="bg-zinc-800/50 px-4 py-3 flex items-center gap-3"><Terminal className="w-4 h-4 text-zinc-400" /><h3 className="text-sm font-semibold">{title} Log</h3></div>
          <div className="h-80 overflow-y-auto p-4 font-mono text-xs">
            {lines.length === 0 ? <div className="text-center text-zinc-500 py-8">No log output yet</div> : lines.map((line, i) => <div key={i} className={`py-0.5 ${scriptLogColor(line)}`}>{line}</div>)}
          </div>
        </div>
      </div>
    );
  };

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
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-6 gap-3 mb-6">
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
                      <td className="px-4 py-3">{r.screenshot ? <a href={r.screenshot.startsWith('http') ? r.screenshot : `${BOT_API_URL}/screenshots/${r.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : r.video_url ? <a href={r.video_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-amber-400 hover:text-amber-300 text-xs">🔗 Video</a> : <span className="text-zinc-600 text-xs">-</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SCRIPT CONTROLS */}
        {activeTab === "warmup" && scriptPanel({
          keyName: "warmup",
          title: "Warm Up Accounts",
          icon: Sparkles,
          description: "Natural browsing warmup for AdsPower profiles",
          children: (
            <div className="flex items-center gap-2 flex-wrap">
              <label className="text-xs text-zinc-500">Browsers</label>
              <input type="number" min="1" max="505" value={warmupSettings.num} onChange={e => setWarmupSettings(v => ({ ...v, num: Number(e.target.value) }))} className="w-20 px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs" />
              <label className="text-xs text-zinc-500">Videos</label>
              <input type="number" min="5" max="20" value={warmupSettings.videos} onChange={e => setWarmupSettings(v => ({ ...v, videos: Number(e.target.value) }))} className="w-20 px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs" />
              <label className="text-xs text-zinc-500">Start tt</label>
              <input type="number" min="1" max="505" value={warmupSettings.start} onChange={e => setWarmupSettings(v => ({ ...v, start: Number(e.target.value) }))} className="w-20 px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs" />
            </div>
          )
        })}

        {activeTab === "signup" && scriptPanel({
          keyName: "signup",
          title: "TikTok Signup Bot",
          icon: Users,
          description: "Runs signup automation through the local bot on port 9000"
        })}

        {activeTab === "proxy" && scriptPanel({
          keyName: "proxy_update",
          title: "Proxy Fix",
          icon: RefreshCw,
          description: "Updates proxies only for browsers listed as not logged in"
        })}

        {activeTab === "scheduler" && scriptPanel({
          keyName: "view_scheduler",
          title: "View Scheduler",
          icon: CalendarClock,
          description: "Scheduled TikTok viewing automation; run in CMD for full interactive menu control"
        })}

        {activeTab === "timer" && scriptPanel({
          keyName: "viewing_timer",
          title: "Viewing Timer",
          icon: Clock,
          description: "Timed viewing sessions; run in CMD for full interactive menu control"
        })}

        {/* TARGETS */}
        {activeTab === "targets" && (
          <div data-testid="targets-tab">
            {/* Control Panel */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Target className="w-5 h-5 text-amber-400" />
                <span className="font-medium">Target Commenter</span>
                {targetRunning ? (
                  <span className="flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-xs"><Play className="w-3 h-3" />Running</span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-1 rounded bg-zinc-700 text-zinc-400 text-xs"><Pause className="w-3 h-3" />Stopped</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {!targetRunning ? (
                  <button
                    onClick={async () => {
                      try {
                        const res = await fetch(`${BOT_API_URL}/api/target-accounts/start`, { method: 'POST' });
                        const data = await res.json();
                        if (data.ok) { fetchTargetLogs(); }
                      } catch (err) { console.error(err); }
                    }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs transition-all"
                  >
                    <Play className="w-3.5 h-3.5" />Start
                  </button>
                ) : (
                  <button
                    onClick={async () => {
                      try {
                        await fetch(`${BOT_API_URL}/api/target-accounts/stop`, { method: 'POST' });
                        fetchTargetLogs();
                      } catch (err) { console.error(err); }
                    }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-xs transition-all"
                  >
                    <Pause className="w-3.5 h-3.5" />Stop
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-amber-400">{targetStats?.accounts?.length || 0}</div>
                <div className="text-xs text-zinc-500">Target Accounts</div>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-cyan-400 flex items-center justify-center gap-1"><Eye className="w-5 h-5" />{(targetStats?.totals?.views || 0).toLocaleString()}</div>
                <div className="text-xs text-zinc-500">Videos Viewed</div>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-emerald-400">{(targetStats?.totals?.comments || 0).toLocaleString()}</div>
                <div className="text-xs text-zinc-500">Total Comments</div>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-violet-400">{(targetStats?.totals?.browsers || 0).toLocaleString()}</div>
                <div className="text-xs text-zinc-500">Browsers Engaged</div>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="bg-zinc-800/50 px-4 py-3 flex items-center gap-3">
                <Target className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-semibold">Target Account Performance</h3>
              </div>
              <table className="w-full text-sm" data-testid="targets-table">
                <thead className="bg-zinc-800/50">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-zinc-400">Account</th>
                    <th className="text-center px-4 py-3 font-medium text-zinc-400">Videos</th>
                    <th className="text-center px-4 py-3 font-medium text-zinc-400">Comments</th>
                    <th className="text-center px-4 py-3 font-medium text-zinc-400">Browsers</th>
                    <th className="text-left px-4 py-3 font-medium text-zinc-400">Last Updated</th>
                    <th className="text-left px-4 py-3 font-medium text-zinc-400">Profile</th>
                  </tr>
                </thead>
                <tbody>
                  {!targetStats?.accounts?.length ? (
                    <tr><td colSpan="6" className="text-center py-12 text-zinc-500">
                      <Target className="w-6 h-6 mx-auto mb-2 opacity-50" />
                      No target accounts data yet. Run the target commenter script to start tracking.
                    </td></tr>
                  ) : targetStats.accounts.map((acc, i) => (
                    <tr key={acc.username || i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`target-row-${i}`}>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-xs font-medium">@{acc.username}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="flex items-center justify-center gap-1 text-cyan-400"><Eye className="w-3 h-3" />{(acc.views || 0).toLocaleString()}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-emerald-400">{(acc.comments || 0).toLocaleString()}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-violet-400">{(acc.browsers || 0).toLocaleString()}</span>
                      </td>
                      <td className="px-4 py-3 text-zinc-400 text-xs">{acc.last_updated || '-'}</td>
                      <td className="px-4 py-3">
                        <a href={`https://www.tiktok.com/@${acc.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-violet-400 hover:text-violet-300 text-xs">
                          <ExternalLink className="w-3 h-3" />View
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Comment History Section */}
            {targetCommentHistory.length > 0 && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden mt-6">
                <div className="bg-zinc-800/50 px-4 py-3 flex items-center gap-3">
                  <MessageCircle className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold">Comment History (Who Commented)</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800">{targetCommentHistory.length}</span>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-800/50 sticky top-0">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium text-zinc-400">Time</th>
                        <th className="text-left px-4 py-2 font-medium text-zinc-400">Browser</th>
                        <th className="text-left px-4 py-2 font-medium text-zinc-400">Account</th>
                        <th className="text-left px-4 py-2 font-medium text-zinc-400">Target</th>
                        <th className="text-center px-4 py-2 font-medium text-zinc-400">Comments</th>
                      </tr>
                    </thead>
                    <tbody>
                      {targetCommentHistory.map((h, i) => (
                        <tr key={h.id || i} className="border-t border-zinc-800 hover:bg-zinc-800/30">
                          <td className="px-4 py-2 text-zinc-400 text-xs">{fmt(h.timestamp)}</td>
                          <td className="px-4 py-2"><span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-400 text-xs font-mono">{h.browser_name}</span></td>
                          <td className="px-4 py-2">
                            <a href={`https://www.tiktok.com/@${h.tiktok_username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs">
                              <ExternalLink className="w-3 h-3" />@{h.tiktok_username}
                            </a>
                          </td>
                          <td className="px-4 py-2"><span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-xs">@{h.target_account}</span></td>
                          <td className="px-4 py-2 text-center text-emerald-400">{h.comments_made}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Live Logs Section */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden mt-6">
              <div className="bg-zinc-800/50 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Terminal className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-semibold">Target Commenter Logs</h3>
                  {targetRunning ? (
                    <span className="flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-xs"><Play className="w-3 h-3" />Running</span>
                  ) : (
                    <span className="flex items-center gap-1 px-2 py-1 rounded bg-zinc-700 text-zinc-400 text-xs"><Pause className="w-3 h-3" />Idle</span>
                  )}
                </div>
              </div>
              <div ref={targetLogsRef} className="h-64 overflow-y-auto p-4 font-mono text-xs" data-testid="target-logs-container">
                {targetLogs.length === 0 ? (
                  <div className="text-center text-zinc-500 py-8">
                    <Terminal className="w-6 h-6 mx-auto mb-2 opacity-50" />
                    No logs yet. Start the target commenter script.
                  </div>
                ) : targetLogs.map((log, i) => (
                  <div key={i} className={`py-0.5 ${
                    log.message.includes('✗') || log.message.includes('Error') || log.message.includes('Failed') ? 'text-red-400' :
                    log.message.includes('✓') || log.message.includes('Commented') ? 'text-emerald-400' :
                    log.message.includes('⚠') ? 'text-amber-400' :
                    log.message.includes('Processing') || log.message.includes('Visiting') ? 'text-blue-400' :
                    'text-zinc-400'
                  }`}>{log.message}</div>
                ))}
              </div>
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
                  :dmReports.map((dm,i)=><tr key={dm.id||i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`dm-row-${i}`}><td className="px-4 py-3 text-zinc-400 text-xs">{fmt(dm.timestamp)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs">{dm.profile}</span></td><td className="px-4 py-3"><a href={dm.profile_url || `https://www.tiktok.com/@${dm.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs"><ExternalLink className="w-3 h-3" />@{dm.username}</a></td><td className="px-4 py-3 text-zinc-300 text-xs max-w-md">{trunc(dm.message,60)}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${dm.status==='sent'?'text-emerald-400 bg-emerald-500/20':'text-red-400 bg-red-500/20'}`}>{dm.status}</span></td><td className="px-4 py-3">{dm.screenshot ? <a href={dm.screenshot.startsWith('http') ? dm.screenshot : `${BOT_API_URL}/screenshots/${dm.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : <span className="text-zinc-600 text-xs">-</span>}</td></tr>)}</tbody>
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
                  :postReports.map((p,i)=>{const mappedUsername = p.tiktok_username || profileMappings[p.profile]; const repostLink = p.repost_url || (mappedUsername && `https://www.tiktok.com/@${mappedUsername}?tab=reposts`); return <tr key={p.id||i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`post-row-${i}`}><td className="px-4 py-3 text-zinc-400 text-xs">{fmt(p.timestamp)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs">{p.profile}</span></td><td className="px-4 py-3">{repostLink?<a href={repostLink} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-rose-400 hover:text-rose-300 text-xs"><ExternalLink className="w-3 h-3" />@{mappedUsername || 'View'}</a>:<span className="text-zinc-500 text-xs">Set in Settings</span>}</td><td className="px-4 py-3 text-zinc-300 text-xs max-w-md">{trunc(p.caption,60)}</td><td className="px-4 py-3"><span className="px-2 py-0.5 rounded text-xs text-emerald-400 bg-emerald-500/20">{p.status}</span></td><td className="px-4 py-3">{p.screenshot ? <a href={p.screenshot.startsWith('http') ? p.screenshot : `${BOT_API_URL}/screenshots/${p.screenshot}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">📸 Screenshot</a> : <span className="text-zinc-600 text-xs">-</span>}</td></tr>})}</tbody>
              </table>
            </div>
          </div>
        )}

        {/* ACCOUNTS */}
        {activeTab === "accounts" && (
          <div data-testid="accounts-tab">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-violet-400">{accountsTotal.toLocaleString()}</div><div className="text-xs text-zinc-500">Total Records</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-emerald-400">{new Set(accounts.map(a=>a.username)).size}</div><div className="text-xs text-zinc-500">Unique Accounts</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-cyan-400">{accounts.filter(a=>a.account_type==='signup').length}</div><div className="text-xs text-zinc-500">Signups</div></div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-amber-400">{new Set(accounts.map(a=>a.browser_num)).size}</div><div className="text-xs text-zinc-500">Browsers Used</div></div>
            </div>
            <div className="mb-3 text-sm text-zinc-500">Showing {accounts.length} account records (sorted by last seen)</div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm" data-testid="accounts-table">
                <thead className="bg-zinc-800/50"><tr>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Browser</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Username</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Email</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-zinc-400">Last Seen</th>
                </tr></thead>
                <tbody>
                  {accounts.length === 0 ? <tr><td colSpan="6" className="text-center py-12 text-zinc-500"><Users className="w-6 h-6 mx-auto mb-2 opacity-50" />No accounts yet. Run the target commenter to start tracking.</td></tr>
                  : accounts.map((acc, i) => (
                    <tr key={acc.id || i} className="border-t border-zinc-800 hover:bg-zinc-800/30" data-testid={`account-row-${i}`}>
                      <td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-400 text-xs font-mono">{acc.browser_name || `tt${acc.browser_num}`}</span></td>
                      <td className="px-4 py-3">{acc.username ? <a href={`https://www.tiktok.com/@${acc.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs"><ExternalLink className="w-3 h-3" />@{acc.username}</a> : <span className="text-zinc-600 text-xs">-</span>}</td>
                      <td className="px-4 py-3 text-zinc-300 text-xs font-mono">{acc.email || '-'}</td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${acc.account_type==='signup'?'text-cyan-400 bg-cyan-500/20':'text-amber-400 bg-amber-500/20'}`}>{acc.account_type || 'login'}</span></td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${acc.status==='active'?'text-emerald-400 bg-emerald-500/20':acc.status==='suspended'?'text-red-400 bg-red-500/20':'text-zinc-400 bg-zinc-500/20'}`}>{acc.status || 'active'}</span></td>
                      <td className="px-4 py-3 text-zinc-400 text-xs">{acc.last_seen ? fmt(acc.last_seen) : '-'}</td>
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
