import { useState, useEffect } from "react";
import { Bell, BellOff, Mail, Check, X, CreditCard, Users, Save, Plus, Trash2 } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;
const BOT_URL = "http://localhost:9000";

export default function Settings() {
  const [email, setEmail] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [profileMappings, setProfileMappings] = useState({});
  const [newProfile, setNewProfile] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [mappingSaving, setMappingSaving] = useState(false);

  const fetchProfileMappings = async () => {
    try {
      const res = await fetch(`${BOT_URL}/api/profile-mapping`);
      if (res.ok) {
        const data = await res.json();
        setProfileMappings(data);
      }
    } catch (err) {
      // Bot not running
    }
  };

  const saveProfileMapping = async (profile, username) => {
    setMappingSaving(true);
    try {
      await fetch(`${BOT_URL}/api/profile-mapping/${profile}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.replace("@", "") })
      });
      await fetchProfileMappings();
      setMessage({ type: "success", text: `Saved @${username.replace("@", "")} for ${profile}` });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to save. Is the bot running?" });
    }
    setMappingSaving(false);
  };

  const deleteProfileMapping = async (profile) => {
    try {
      await fetch(`${BOT_URL}/api/profile-mapping/${profile}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "" })
      });
      await fetchProfileMappings();
    } catch (err) {
      setMessage({ type: "error", text: "Failed to delete" });
    }
  };

  const addNewMapping = async () => {
    if (!newProfile || !newUsername) return;
    await saveProfileMapping(newProfile, newUsername);
    setNewProfile("");
    setNewUsername("");
  };

  const fetchSubs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/notifications/subscriptions`);
      const data = await res.json();
      setSubscriptions(data.subscriptions || []);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchSubs(); fetchProfileMappings(); }, []);

  const handleSubscribe = async () => {
    if (!email || !email.includes("@")) { setMessage({ type: "error", text: "Enter a valid email" }); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/notifications/subscribe`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, frequency })
      });
      const data = await res.json();
      setMessage({ type: "success", text: data.message || "Subscribed!" });
      setEmail(""); fetchSubs();
    } catch (err) { setMessage({ type: "error", text: "Failed to subscribe" }); }
    setLoading(false);
  };

  const handleUnsubscribe = async (emailToRemove) => {
    try {
      await fetch(`${API_URL}/api/notifications/unsubscribe`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailToRemove })
      });
      fetchSubs();
    } catch (err) { console.error(err); }
  };

  const handleSendSummary = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/notifications/send-summary`, { method: "POST" });
      const data = await res.json();
      if (data.ok) setMessage({ type: "success", text: `Sent to ${data.sent} subscriber(s)` });
      else setMessage({ type: "error", text: data.detail || data.message || "Failed" });
    } catch (err) { setMessage({ type: "error", text: "Failed to send summary" }); }
    setLoading(false);
  };

  return (
    <div data-testid="settings-page" className="space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>

      {message && (
        <div className={`p-3 rounded-lg border text-sm ${message.type === "success" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : "bg-red-500/10 border-red-500/30 text-red-400"}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="float-right opacity-60 hover:opacity-100"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Email Notifications */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center"><Bell className="w-5 h-5 text-violet-400" /></div>
          <div><h3 className="font-semibold">Email Notifications</h3><p className="text-sm text-zinc-500">Get daily activity summaries via email</p></div>
        </div>
        <div className="flex gap-3 mb-4 flex-wrap">
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="team@company.com"
            className="flex-1 min-w-[200px] px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:border-violet-500" data-testid="email-input" />
          <select value={frequency} onChange={(e) => setFrequency(e.target.value)}
            className="px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none" data-testid="frequency-select">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
          <button onClick={handleSubscribe} disabled={loading}
            className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm font-medium transition-all disabled:opacity-50 flex items-center gap-2" data-testid="subscribe-btn">
            <Mail className="w-4 h-4" /> Subscribe
          </button>
        </div>

        {/* Current Subscribers */}
        <div className="border-t border-zinc-800 pt-4 mt-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-zinc-400">Active Subscribers ({subscriptions.length})</h4>
            {subscriptions.length > 0 && (
              <button onClick={handleSendSummary} disabled={loading}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-xs font-medium transition-all disabled:opacity-50" data-testid="send-summary-btn">
                Send Summary Now
              </button>
            )}
          </div>
          {subscriptions.length === 0 ? (
            <p className="text-sm text-zinc-500"><BellOff className="w-4 h-4 inline mr-1" />No subscribers yet</p>
          ) : (
            <div className="space-y-2">
              {subscriptions.map(sub => (
                <div key={sub.email} className="flex items-center justify-between bg-zinc-800/50 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm">{sub.email}</span>
                    <span className="text-xs text-zinc-500 px-2 py-0.5 rounded bg-zinc-700">{sub.frequency}</span>
                  </div>
                  <button onClick={() => handleUnsubscribe(sub.email)} className="text-zinc-500 hover:text-red-400 transition-colors" data-testid={`unsub-${sub.email}`}>
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Profile Mapping */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center"><Users className="w-5 h-5 text-rose-400" /></div>
          <div><h3 className="font-semibold">Profile Mapping</h3><p className="text-sm text-zinc-500">Map your profile names (tt1, tt2...) to TikTok usernames for repost links</p></div>
        </div>

        {/* Add New Mapping */}
        <div className="flex gap-3 mb-4 flex-wrap">
          <input type="text" value={newProfile} onChange={(e) => setNewProfile(e.target.value)} placeholder="Profile (e.g., tt1)"
            className="w-32 px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:border-rose-500" />
          <input type="text" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} placeholder="TikTok username"
            className="flex-1 min-w-[150px] px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:border-rose-500" />
          <button onClick={addNewMapping} disabled={mappingSaving || !newProfile || !newUsername}
            className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 rounded-lg text-sm font-medium transition-all disabled:opacity-50 flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add
          </button>
        </div>

        {/* Existing Mappings */}
        <div className="border-t border-zinc-800 pt-4 mt-4">
          <h4 className="text-sm font-medium text-zinc-400 mb-3">Saved Mappings ({Object.keys(profileMappings).length})</h4>
          {Object.keys(profileMappings).length === 0 ? (
            <p className="text-sm text-zinc-500">No mappings yet. Add profile mappings to show repost links for past reposts.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(profileMappings).sort((a,b) => {
                const numA = parseInt(a[0].replace(/\D/g, '')) || 999;
                const numB = parseInt(b[0].replace(/\D/g, '')) || 999;
                return numA - numB;
              }).map(([profile, username]) => (
                <div key={profile} className="flex items-center justify-between bg-zinc-800/50 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded bg-zinc-700 text-zinc-300 text-xs font-mono">{profile}</span>
                    <span className="text-zinc-400">&rarr;</span>
                    <a href={`https://www.tiktok.com/@${username}`} target="_blank" rel="noopener noreferrer" className="text-rose-400 hover:text-rose-300 text-sm">@{username}</a>
                  </div>
                  <button onClick={() => deleteProfileMapping(profile)} className="text-zinc-500 hover:text-red-400 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        <p className="text-xs text-zinc-500 mt-4">Note: Make sure the local bot is running at localhost:9000 for mappings to save.</p>
      </div>

      {/* Billing */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center"><CreditCard className="w-5 h-5 text-emerald-400" /></div>
          <div><h3 className="font-semibold">Billing</h3><p className="text-sm text-zinc-500">Manage your subscription</p></div>
        </div>
        <div className="bg-zinc-800/50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div><span className="text-sm text-zinc-400">Current Plan:</span> <span className="ml-2 font-semibold text-emerald-400">Free</span></div>
            <button onClick={() => window.scrollTo(0, 0)} className="px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm font-medium transition-all" data-testid="upgrade-btn">
              Upgrade Plan
            </button>
          </div>
        </div>
      </div>

      {/* Setup Instructions */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <h3 className="font-semibold mb-3">Email Setup Instructions</h3>
        <p className="text-sm text-zinc-400 mb-3">To enable email notifications, you need a Resend API key:</p>
        <ol className="space-y-2 text-sm text-zinc-400">
          <li className="flex gap-2"><span className="text-violet-400 font-bold">1.</span>Sign up at <a href="https://resend.com" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">resend.com</a></li>
          <li className="flex gap-2"><span className="text-violet-400 font-bold">2.</span>Create an API key from Dashboard &rarr; API Keys</li>
          <li className="flex gap-2"><span className="text-violet-400 font-bold">3.</span>Add <code className="bg-zinc-800 px-2 py-0.5 rounded text-xs">RESEND_API_KEY=re_your_key</code> to <code className="bg-zinc-800 px-2 py-0.5 rounded text-xs">backend/.env</code></li>
          <li className="flex gap-2"><span className="text-violet-400 font-bold">4.</span>Restart the backend and you're ready to send summaries</li>
        </ol>
      </div>
    </div>
  );
}
