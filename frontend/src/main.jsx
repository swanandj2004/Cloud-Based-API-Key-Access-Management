import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, ArrowRight, CheckCircle2, Clipboard, Copy, KeyRound,
  LayoutDashboard, LogOut, Menu, Plus, RefreshCw, Shield,
  Trash2, User, Users, X, AlertCircle
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const ADMIN_ROLE = 8;

async function api(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = { ...(options.body ? {"Content-Type": "application/json"} : {}), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let data = null;
  try { data = await res.json(); } catch {}

  if (!res.ok) {
    const message = data?.detail || data?.message || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

function decodeJwt(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [session, setSession] = useState(() => decodeJwt(localStorage.getItem("access_token") || ""));
  const [page, setPage] = useState("dashboard");

  const login = (accessToken) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setSession(decodeJwt(accessToken));
    setPage("dashboard");
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setSession(null);
  };

  if (!token || !session) return <Login onLogin={login} />;

  const isAdmin = Number(session.role) === ADMIN_ROLE;

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} isAdmin={isAdmin} logout={logout} />
      <main className="main-content">
        <Topbar session={session} />
        {page === "dashboard" && <Dashboard session={session} isAdmin={isAdmin} />}
        {page === "keys" && <KeysPage session={session} isAdmin={isAdmin} />}
        {page === "users" && isAdmin && <UsersPage />}
        {page === "roles" && isAdmin && <RolesPage />}
      </main>
    </div>
  );
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api("/user/login", {
        method: "POST",
        body: JSON.stringify({ form_username: username, form_password: password })
      });
      if (!data?.access_token) throw new Error(data?.message || "Login failed");
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-mark"><KeyRound size={25}/></div>
        <span>KeyVault</span>
      </div>
      <form className="login-card" onSubmit={submit}>
        <div className="eyebrow">SECURE ACCESS</div>
        <h1>Welcome back</h1>
        <p className="muted">Sign in to manage your API keys and access permissions.</p>
        {error && <Notice type="error" text={error} />}
        <label>Username</label>
        <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter username" autoComplete="username" required />
        <label>Password</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" autoComplete="current-password" required />
        <button className="primary-button full" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"} <ArrowRight size={17}/>
        </button>
      </form>
      <div className="login-footer">Cloud-Based API Key Access Management</div>
    </div>
  );
}

function Sidebar({ page, setPage, isAdmin, logout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark"><KeyRound size={20}/></div>
        <div><strong>KeyVault</strong><small>Access Management</small></div>
      </div>
      <nav>
        <NavItem icon={<LayoutDashboard size={18}/>} label="Dashboard" active={page === "dashboard"} onClick={() => setPage("dashboard")} />
        <NavItem icon={<KeyRound size={18}/>} label="API Keys" active={page === "keys"} onClick={() => setPage("keys")} />
        {isAdmin && <><div className="nav-section">ADMINISTRATION</div>
          <NavItem icon={<Users size={18}/>} label="Users" active={page === "users"} onClick={() => setPage("users")} />
          <NavItem icon={<Shield size={18}/>} label="Roles" active={page === "roles"} onClick={() => setPage("roles")} />
        </>}
      </nav>
      <button className="logout-button" onClick={logout}><LogOut size={18}/> Sign out</button>
    </aside>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>{icon}<span>{label}</span></button>;
}

function Topbar({ session }) {
  return (
    <header className="topbar">
      <div>
        <div className="page-kicker">CONTROL CENTER</div>
        <h2>API Access Management</h2>
      </div>
      <div className="profile">
        <div className="avatar">{String(session.username || "?")[0].toUpperCase()}</div>
        <div><strong>{session.username}</strong><span>{Number(session.role) === ADMIN_ROLE ? "Administrator" : "User"}</span></div>
      </div>
    </header>
  );
}

function Dashboard({ session, isAdmin }) {
  const [stats, setStats] = useState({ keys: 0, users: 0, roles: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        if (isAdmin) {
          const [keys, users, roles] = await Promise.all([
            api("/get/all/keys"), api("/get/all/users"), api("/get/all/roles")
          ]);
          if (mounted) setStats({ keys: keys?.length || 0, users: users?.length || 0, roles: roles?.length || 0 });
        } else {
          const keys = await api(`/get/user/keys/${session.id}`);
          if (mounted) setStats({ keys: keys?.length || 0, users: 1, roles: 0 });
        }
      } catch {} finally { if (mounted) setLoading(false); }
    })();
    return () => { mounted = false; };
  }, [isAdmin, session.id]);

  const cards = isAdmin
    ? [["API Keys", stats.keys, KeyRound], ["Users", stats.users, Users], ["Roles", stats.roles, Shield]]
    : [["My API Keys", stats.keys, KeyRound]];

  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">OVERVIEW</div>
          <h1>{isAdmin ? "Admin dashboard" : "Your access dashboard"}</h1>
          <p>Monitor API access and manage credentials from one place.</p>
        </div>
        <div className="hero-icon"><Activity size={32}/></div>
      </section>
      <div className="stats-grid">
        {cards.map(([label, value, Icon]) => <div className="stat-card" key={label}>
          <div className="stat-icon"><Icon size={20}/></div><div className="stat-value">{loading ? "—" : value}</div><div className="stat-label">{label}</div>
        </div>)}
      </div>
      <div className="info-panel">
        <Shield size={20}/>
        <div><strong>Session security</strong><p>Your session uses a JWT issued by the FastAPI backend. The token expires after the configured 30-minute lifetime.</p></div>
      </div>
    </>
  );
}

function KeysPage({ session, isAdmin }) {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const data = isAdmin ? await api("/get/all/keys") : await api(`/get/user/keys/${session.id}`);
      setKeys(Array.isArray(data) ? data : []);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [isAdmin, session.id]);

  const deleteKey = async (id) => {
    if (!confirm("Delete this API key?")) return;
    try { await api(`/delete/key/${id}`, { method: "DELETE" }); await load(); }
    catch (e) { setError(e.message); }
  };

  return (
    <>
      <div className="section-heading">
        <div><div className="eyebrow">CREDENTIALS</div><h1>{isAdmin ? "API Keys" : "My API Keys"}</h1><p>View and manage authorized API credentials.</p></div>
        <div className="heading-actions"><button className="secondary-button" onClick={load}><RefreshCw size={16}/> Refresh</button>{isAdmin && <button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={17}/> Create key</button>}</div>
      </div>
      {error && <Notice type="error" text={error}/>}
      <div className="table-card">
        {loading ? <Loading/> : keys.length === 0 ? <Empty icon={<KeyRound size={30}/>} title="No API keys" text="There are no keys available for this account."/> :
          <div className="table-wrap"><table><thead><tr><th>ID</th><th>API KEY</th><th>CREATED</th><th>PERMITTED USERS</th>{isAdmin && <th></th>}</tr></thead>
          <tbody>{keys.map(k => <tr key={k.id ?? k.key}><td className="mono">#{k.id ?? "—"}</td><td><KeyValue value={k.key}/></td><td>{k.created_at || "—"}</td><td>{Array.isArray(k.permitted_users) ? k.permitted_users.join(", ") : "—"}</td>{isAdmin && <td><button className="icon-button danger" title="Delete key" onClick={() => deleteKey(k.id)}><Trash2 size={17}/></button></td>}</tr>)}</tbody></table></div>
        }
      </div>
      {showCreate && <CreateKeyModal onClose={() => setShowCreate(false)} onCreated={load}/>}
    </>
  );
}

function KeyValue({ value }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard.writeText(value || ""); setCopied(true); setTimeout(() => setCopied(false), 1200); };
  return <div className="key-value"><code>{value}</code><button className="copy-button" onClick={copy} title="Copy API key">{copied ? <CheckCircle2 size={16}/> : <Copy size={16}/>}</button></div>;
}

function CreateKeyModal({ onClose, onCreated }) {
  const [users, setUsers] = useState("");
  const [loading, setLoading] = useState(false);
  const [createdKey, setCreatedKey] = useState("");
  const [error, setError] = useState("");

  async function create() {
    const ids = users.split(",").map(x => Number(x.trim())).filter(x => Number.isInteger(x) && x > 0);
    if (!ids.length) { setError("Enter at least one user ID, for example: 1, 2, 3"); return; }
    setLoading(true); setError("");
    try {
      const data = await api("/create/key", { method: "POST", body: JSON.stringify({ permitted_users: ids }) });
      setCreatedKey(data?.api_key || "");
      await onCreated();
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  return <Modal title="Create API key" onClose={onClose}>
    {!createdKey ? <>
      <p className="muted">The backend generates the API key. Provide the user IDs that should be permitted to access it.</p>
      {error && <Notice type="error" text={error}/>}
      <label>Permitted user IDs</label>
      <input value={users} onChange={e => setUsers(e.target.value)} placeholder="e.g. 1, 2, 3"/>
      <div className="modal-actions"><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" onClick={create} disabled={loading}>{loading ? "Creating..." : "Create key"}</button></div>
    </> : <>
      <Notice type="success" text="API key created successfully."/>
      <label>New API key</label>
      <div className="created-key"><code>{createdKey}</code><KeyValue value={createdKey}/></div>
      <p className="warning-text">Copy this key now and store it securely. Your current backend response must include the plaintext key for this screen to display it.</p>
      <div className="modal-actions"><button className="primary-button" onClick={onClose}>Done</button></div>
    </>}
  </Modal>;
}

function UsersPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const load = async () => { try { setUsers(await api("/get/all/users")); } catch (e) { setError(e.message); } };
  useEffect(() => { load(); }, []);
  return <SimpleTable title="Users" kicker="DIRECTORY" description="Manage accounts registered in the system." icon={<Users size={22}/>} error={error} onRefresh={load}
    headers={["ID", "USERNAME", "ROLE"]} rows={users.map(u => [u.id, u.username, u.role])}/>;
}

function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [error, setError] = useState("");
  const load = async () => { try { setRoles(await api("/get/all/roles")); } catch (e) { setError(e.message); } };
  useEffect(() => { load(); }, []);
  return <SimpleTable title="Roles" kicker="ACCESS CONTROL" description="View the roles configured in the backend." icon={<Shield size={22}/>} error={error} onRefresh={load}
    headers={["ID", "NAME"]} rows={roles.map(r => [r.id, r.name])}/>;
}

function SimpleTable({ title, kicker, description, icon, headers, rows, error, onRefresh }) {
  return <>
    <div className="section-heading"><div><div className="eyebrow">{kicker}</div><h1>{title}</h1><p>{description}</p></div><button className="secondary-button" onClick={onRefresh}><RefreshCw size={16}/> Refresh</button></div>
    {error && <Notice type="error" text={error}/>}
    <div className="table-card">{rows.length ? <div className="table-wrap"><table><thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{r.map((c,j)=><td key={j} className={j===0 ? "mono" : ""}>{String(c ?? "—")}</td>)}</tr>)}</tbody></table></div> : <Empty icon={icon} title={`No ${title.toLowerCase()} found`} text="Nothing is available to display."/ >}</div>
  </>;
}

function Modal({ title, children, onClose }) {
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}><div className="modal"><div className="modal-header"><h2>{title}</h2><button className="icon-button" onClick={onClose}><X size={19}/></button></div>{children}</div></div>;
}
function Notice({ type, text }) { return <div className={`notice ${type}`}><AlertCircle size={17}/><span>{text}</span></div>; }
function Empty({ icon, title, text }) { return <div className="empty">{icon}<h3>{title}</h3><p>{text}</p></div>; }
function Loading() { return <div className="empty"><RefreshCw className="spin" size={28}/><h3>Loading</h3><p>Fetching data from the API...</p></div>; }

createRoot(document.getElementById("root")).render(<App />);
