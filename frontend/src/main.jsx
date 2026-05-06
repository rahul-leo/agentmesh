import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || (window.location.hostname.includes("vercel.app") ? "" : "http://127.0.0.1:8000");

const initialForm = {
  repository: "",
  branch: "main",
  environment: "local",
  requirement: "",
  failure_log: "",
  changed_files: "",
};

const agentSteps = ["Debug", "Fix", "Auto-Fix", "Test", "Build", "Deploy", "Monitor", "Verdict"];
const quickLogs = [
  "Convert HTML/CSS/JS files into a polished responsive website",
  "Turn Python scripts into a FastAPI-backed web app",
  "Build a dashboard from the repo data files and deploy it",
];

const initialLaunch = {
  githubRepo: "",
  vercelProject: "",
  deployTarget: "vercel",
  visibility: "public",
};

function normalizeGitHubRepo(value) {
  const input = (value || "").trim().replace(/\/$/, "");
  if (input.includes("/blob/")) return input.split("/blob/")[0];
  if (input.includes("/tree/")) return input.split("/tree/")[0];
  return input;
}

function repoNameFromUrl(value) {
  const repo = normalizeGitHubRepo(value);
  const parts = repo.replace(/\.git$/, "").split("/").filter(Boolean);
  return parts.at(-1) || "agentmesh-demo";
}

const icons = {
  bot: (
    <>
      <path d="M12 8V4H8" />
      <rect width="16" height="12" x="4" y="8" rx="2" />
      <path d="M2 14h2" />
      <path d="M20 14h2" />
      <path d="M15 13v2" />
      <path d="M9 13v2" />
    </>
  ),
  branch: (
    <>
      <path d="M15 6a9 9 0 0 0-9 9V3" />
      <circle cx="18" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
    </>
  ),
  database: (
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14a9 3 0 0 0 18 0V5" />
      <path d="M3 12a9 3 0 0 0 18 0" />
    </>
  ),
  file: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
      <path d="M12 18v-6" />
      <path d="m9 15 3-3 3 3" />
    </>
  ),
  message: (
    <>
      <path d="M22 17a2 2 0 0 1-2 2H7l-5 3V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z" />
      <path d="M7 9h10" />
      <path d="M7 13h7" />
    </>
  ),
  refresh: (
    <>
      <path d="M21 12a9 9 0 0 1-15.4 6.4L3 16" />
      <path d="M3 21v-5h5" />
      <path d="M3 12A9 9 0 0 1 18.4 5.6L21 8" />
      <path d="M21 3v5h-5" />
    </>
  ),
  shield: (
    <>
      <path d="M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  external: (
    <>
      <path d="M15 3h6v6" />
      <path d="M10 14 21 3" />
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    </>
  ),
  pr: (
    <>
      <path d="M18 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
      <path d="M6 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6z" />
      <path d="M13.2 10.8A5.94 5.94 0 0 1 18 9" />
      <path d="M6 12v3" />
    </>
  ),
  copy: (
    <>
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </>
  ),
  terminal: (
    <>
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" x2="20" y1="19" y2="19" />
    </>
  ),
};

function Icon({ name, size = 22, className = "" }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width={size}
    >
      {icons[name]}
    </svg>
  );
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedFile, setUploadedFile] = useState("");
  const [launch, setLaunch] = useState(initialLaunch);
  const [clock, setClock] = useState(new Date());
  const [chatFocused, setChatFocused] = useState(false);
  const [draggingLog, setDraggingLog] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!chatRef.current) return;
    chatRef.current.style.height = "auto";
    chatRef.current.style.height = `${Math.min(chatRef.current.scrollHeight, 320)}px`;
  }, [form.requirement]);

  function updateField(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  function updateLaunch(event) {
    setLaunch({ ...launch, [event.target.name]: event.target.value });
  }

  async function readLogFile(file) {
    setUploadedFile(file.name);
    const text = await file.text();
    setForm((current) => ({ ...current, requirement: text }));
  }

  async function uploadLog(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    await readLogFile(file);
  }

  function dropLog(event) {
    event.preventDefault();
    setDraggingLog(false);
    const file = event.dataTransfer.files?.[0];
    if (file) readLogFile(file);
  }

  function useQuickLog(text) {
    setForm((current) => ({ ...current, requirement: text }));
    chatRef.current?.focus();
  }

  async function loadHistory() {
    setRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/api/runs?limit=5`);
      if (!response.ok) return;
      const data = await response.json();
      setHistory(data.runs || []);
    } catch {
      setHistory([]);
    } finally {
      setTimeout(() => setRefreshing(false), 600);
    }
  }

  async function runAgents(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const payload = {
      repository: form.repository,
      branch: form.branch,
      environment: form.environment,
      requirement: form.requirement,
      failure_log: form.failure_log,
      changed_files: form.changed_files
        .split(/\r?\n|,/)
        .map((item) => item.trim())
        .filter(Boolean),
    };

    try {
      const response = await fetch(`${API_BASE}/api/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();
      setResult(data);
      await loadHistory();
    } catch {
      setError("Backend is not reachable. Start FastAPI on http://127.0.0.1:8000 first.");
    } finally {
      setLoading(false);
    }
  }

  const cards = result?.results || [];
  const liveStatus = error ? "backend offline" : loading ? "agents running" : "ready";
  const changedFileCount = form.changed_files.split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean).length;
  const requirementWordCount = form.requirement.trim() ? form.requirement.trim().split(/\s+/).length : 0;
  const deployResult = result?.results?.find((item) => item.agent === "deploy-agent");
  const repoForDeploy = normalizeGitHubRepo(launch.githubRepo || form.repository);
  const projectForDeploy = launch.vercelProject.trim() || repoNameFromUrl(repoForDeploy);
  const vercelImportLink = `https://vercel.com/new/clone?repository-url=${encodeURIComponent(repoForDeploy)}&project-name=${encodeURIComponent(projectForDeploy)}`;
  const streamlitDeployLink = "https://share.streamlit.io/deploy";
  const fallbackVercelCommand = [
    "$env:VERCEL_TOKEN = \"<your-vercel-token>\"",
    `.\\scripts\\auto_deploy.ps1 -GitHubRepo "${repoForDeploy}" -VercelProjectName "${projectForDeploy}" -GitHubVisibility ${launch.visibility}`,
  ].join("\n");
  const isStreamlitTarget = launch.deployTarget === "streamlit";
  const fallbackStreamlitCommand = [
    "1. Push your code to a GitHub repository.",
    "2. Visit https://share.streamlit.io/deploy",
    "3. Select your repository and branch.",
    "4. Set 'Main file path' to 'main.py' or your Streamlit entry point.",
    "5. Click 'Deploy!'",
  ].join("\n");
  const launchCommand = isStreamlitTarget
    ? deployResult?.metadata?.streamlit_launch_command || fallbackStreamlitCommand
    : deployResult?.metadata?.public_launch_command || fallbackVercelCommand;
  const liveDeploymentLink = isStreamlitTarget
    ? deployResult?.metadata?.is_streamlit_live ? deployResult.metadata.streamlit_deployment_url : ""
    : deployResult?.metadata?.is_live ? deployResult.metadata.deployment_url : "";
  const launchSetupLink = isStreamlitTarget
    ? deployResult?.metadata?.streamlit_deploy_url || streamlitDeployLink
    : deployResult?.metadata?.one_click_url || vercelImportLink;

  return (
    <main className="mx-auto w-[min(1120px,calc(100%_-_32px))] pb-12 pt-4 sm:pt-7">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="inline-flex w-fit items-center gap-2 rounded-full border border-ink/10 bg-white/55 px-4 py-2 text-sm font-bold text-ink shadow-sm backdrop-blur-xl">
          <span className={`h-2.5 w-2.5 rounded-full ${error ? "bg-[#d94a38]" : loading ? "bg-[#d69a18]" : "bg-leaf"} live-dot`} />
          {liveStatus}
        </div>
        <div className="flex items-center gap-4">
          <button
            className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/60 px-4 py-2 text-sm font-bold text-ink transition hover:bg-white"
            onClick={loadHistory}
            type="button"
          >
            <Icon name="refresh" size={16} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>
          <div className="text-sm font-bold text-muted">{clock.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</div>
        </div>
      </div>

      <section className="grid min-h-[430px] items-start gap-8 lg:grid-cols-[0.86fr_1.14fr]">
        <div className="min-w-0 pt-1">
          <h1 className="hero-title max-w-[440px] font-serif text-[clamp(3rem,6.2vw,5.35rem)] font-bold leading-[0.9] tracking-normal text-ink">
            <span>Give</span>
            <span>AgentMesh</span>
            <span>a repo.</span>
            <span>It turns</span>
            <span>code into</span>
            <span>a live</span>
            <span>product.</span>
          </h1>
          <p className="hero-copy mt-6 max-w-[440px] text-[1.02rem] leading-7 text-muted">
            Paste a GitHub link, list the repo files, and describe what you want built. AgentMesh debugs, fixes, tests, converts the code into the requested app, deploys it on Vercel, and monitors the result.
          </p>
          <div className="mt-6 flex max-w-[440px] flex-wrap gap-2">
            {agentSteps.map((step, index) => (
              <div
                className={`rounded-full border border-ink/10 bg-white/45 px-3 py-2 text-center text-xs font-bold text-ink shadow-sm backdrop-blur transition ${
                  loading ? "float-soft" : ""
                } ${step === "Auto-Fix" ? "border-leaf bg-lime/30" : ""}`}
                key={step}
                style={{ animationDelay: `${index * 120}ms` }}
              >
                {step}
              </div>
            ))}
          </div>
        </div>

        <form
          className="ambient-card mt-4 rounded-[34px] border border-ink/10 bg-[#fffcf1e6] p-5 shadow-[0_24px_70px_rgba(20,33,31,0.12)] backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_85px_rgba(20,33,31,0.16)] md:mt-8 md:p-7"
          onSubmit={runAgents}
        >
          <div className="flex items-start gap-3">
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-[14px] bg-ink text-white">
              <Icon name="message" size={22} />
            </div>
            <div>
              <h2 className="text-2xl font-bold leading-none text-ink">Ask AgentMesh</h2>
              <p className="mt-2 text-sm leading-5 text-muted">
                Share the repository, target files, and requirement. Optional logs help the debug agent repair existing failures.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Field label="GitHub repository or file link">
              <input className={controlClass} name="repository" onChange={updateField} value={form.repository} />
            </Field>
            <Field label="Branch">
              <input className={controlClass} name="branch" onChange={updateField} value={form.branch} />
            </Field>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-[0.7fr_1.3fr]">
            <Field label="Environment">
              <select className={controlClass} name="environment" onChange={updateField} value={form.environment}>
                <option value="local">local</option>
                <option value="staging">staging</option>
                <option value="production">production</option>
              </select>
            </Field>
            <Field label="Repo files to convert">
              <input className={controlClass} name="changed_files" onChange={updateField} value={form.changed_files} />
            </Field>
          </div>

          <div className="mt-4">
            <Field label="Optional debug notes or failing log">
              <textarea
                className={`${controlClass} min-h-[92px] resize-y leading-6`}
                name="failure_log"
                onChange={updateField}
                placeholder="Paste errors here only if the repo already has a bug, build failure, or broken deployment."
                value={form.failure_log}
              />
            </Field>
          </div>

          <div className="mt-4">
            <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="block text-xs font-bold uppercase tracking-[0.1em] text-muted">Requirement</span>
              <span className="text-xs font-bold text-muted">
                {requirementWordCount} words - {form.requirement.length} chars - {changedFileCount} files
              </span>
            </div>
            <div
              className={`chat-shell ${chatFocused ? "chat-shell-active" : ""} ${draggingLog ? "chat-shell-drag" : ""}`}
              onDragLeave={() => setDraggingLog(false)}
              onDragOver={(event) => {
                event.preventDefault();
                setDraggingLog(true);
              }}
              onDrop={dropLog}
            >
              <textarea
                className="chat-textarea"
                name="requirement"
                onBlur={() => setChatFocused(false)}
                onChange={updateField}
                onFocus={() => setChatFocused(true)}
                placeholder="Describe what the repo should become: app, website, API, dashboard, game, portfolio..."
                ref={chatRef}
                value={form.requirement}
              />
              <div className="pointer-events-none absolute bottom-3 right-4 text-xs font-bold text-muted/70">
                {draggingLog ? "drop log file" : chatFocused ? "typing..." : "ready"}
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {quickLogs.map((item) => (
                <button
                  className="rounded-full border border-ink/10 bg-white/55 px-3 py-2 text-xs font-bold text-ink transition hover:-translate-y-0.5 hover:bg-white"
                  key={item}
                  onClick={() => useQuickLog(item)}
                  type="button"
                >
                  {item.split(" ").slice(0, 4).join(" ")}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-full border border-ink/10 bg-white/70 px-4 py-3 text-sm font-bold text-ink shadow-sm transition hover:bg-white">
              <Icon name="file" size={18} />
              Upload requirement file
              <input className="hidden" type="file" accept=".txt,.log,.md,.json,.py,.js,.jsx,.ts,.tsx" onChange={uploadLog} />
            </label>
            {uploadedFile && <p className="text-sm font-bold text-leaf">Loaded: {uploadedFile}</p>}
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              className="relative overflow-hidden rounded-full bg-ink px-6 py-4 text-sm font-bold text-white shadow-[0_18px_38px_rgba(20,33,31,0.24)] transition hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-70"
              disabled={loading}
              type="submit"
            >
              {loading && <span className="progress-line absolute inset-y-0 left-0 w-full opacity-40" />}
              {loading ? "Running agents..." : "Run agent mesh"}
            </button>
            <button
              className="rounded-full border border-ink/10 bg-white/55 px-6 py-4 text-sm font-bold text-ink transition hover:bg-white"
              onClick={() => setForm((current) => ({ ...current, requirement: "" }))}
              type="button"
            >
              Clear requirement
            </button>
          </div>
          {error && <p className="mt-4 font-bold text-[#a03224]">{error}</p>}
          
          {loading && (
            <div className="mt-6 rounded-2xl bg-black/90 p-4 font-mono text-[11px] leading-5 text-[#00ff41] shadow-inner">
              <div className="flex items-center gap-2 border-b border-[#00ff41]/20 pb-2 mb-2">
                <Icon name="terminal" size={14} />
                <span>AGENT_MESH_COORDINATOR v1.0.4</span>
              </div>
              <div className="space-y-1">
                <p>&gt; [SYSTEM] Initializing Gemini 3 Flash reasoning engine...</p>
                <p className="animate-pulse">&gt; [DEBUG_AGENT] Finding blockers before conversion...</p>
                <p>&gt; [FIX_AGENT] Preparing implementation plan...</p>
                <p>&gt; [AUTO_FIX] Preparing GitHub PR workflow...</p>
                <p>&gt; [BUILD_AGENT] Converting tested code into the deployable app...</p>
                <p>&gt; [VERDICT_AGENT] Synthesizing final autonomous report...</p>
              </div>
            </div>
          )}
        </form>
      </section>

      <div className="mt-3">
        <div className="bot-breathe grid h-16 w-16 place-items-center rounded-[22px] border-2 border-ink/10 bg-lime text-ink">
          <Icon name="bot" size={38} />
        </div>
      </div>

      <section className="mt-2 grid gap-[18px] md:grid-cols-3">
        <Metric icon="branch" label="Branch" value={result?.task?.branch || "main"} />
        <Metric icon="shield" label="Risk" value={result?.risk?.risk_label || "waiting"} />
        <Metric 
          icon="external" 
          label="Live Deployment" 
          value={liveDeploymentLink ? "View Live" : deployResult ? "Launch Setup" : "waiting"} 
          link={liveDeploymentLink || (deployResult ? launchSetupLink : "")}
        />
        <Metric icon="database" label="Stored" value={result ? (result.persisted ? "saved" : "not saved") : "waiting"} />
      </section>

      <section className="mt-[18px] grid gap-[18px] md:grid-cols-2">
        {cards.length === 0 ? (
          <article className="col-span-full rounded-[24px] border border-ink/10 bg-[#fffcf1d9] p-5 text-sm text-muted shadow-[0_18px_50px_rgba(20,33,31,0.08)] backdrop-blur-xl">
            Launch a run to see each agent report back.
          </article>
        ) : (
          cards.map((card) => <AgentCard card={card} key={card.agent} />)
        )}
      </section>

      {result && (
        <section className="mt-[18px] animate-in fade-in slide-in-from-bottom-4 duration-700 rounded-[26px] border border-ink/10 bg-[#eef9ffd9] p-5 shadow-[0_18px_50px_rgba(20,33,31,0.08)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-leaf">Public launch</p>
              <h2 className="mt-1 text-2xl font-bold text-ink">Deploy with Vercel or Streamlit</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <a
                className="inline-flex w-fit items-center gap-2 rounded-full bg-ink px-4 py-3 text-sm font-bold text-white no-underline transition hover:-translate-y-0.5"
                href={deployResult?.metadata?.one_click_url || vercelImportLink}
                rel="noreferrer"
                target="_blank"
              >
                <Icon name="external" size={16} />
                Open in Vercel
              </a>
              <a
                className="inline-flex w-fit items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-3 text-sm font-bold text-ink no-underline transition hover:-translate-y-0.5 hover:bg-white"
                href={deployResult?.metadata?.streamlit_deploy_url || streamlitDeployLink}
                rel="noreferrer"
                target="_blank"
              >
                <Icon name="external" size={16} />
                Open in Streamlit
              </a>
            </div>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-[1.2fr_0.8fr_0.6fr_0.6fr]">
            <Field label="GitHub repository">
              <input className={controlClass} name="githubRepo" onChange={updateLaunch} placeholder="https://github.com/user/repo" value={launch.githubRepo} />
            </Field>
            <Field label="Project name">
              <input className={controlClass} name="vercelProject" onChange={updateLaunch} placeholder="my-awesome-project" value={launch.vercelProject} />
            </Field>
            <Field label="Deploy target">
              <select className={controlClass} name="deployTarget" onChange={updateLaunch} value={launch.deployTarget}>
                <option value="vercel">Vercel</option>
                <option value="streamlit">Streamlit</option>
              </select>
            </Field>
            <Field label="GitHub visibility">
              <select className={controlClass} name="visibility" onChange={updateLaunch} value={launch.visibility}>
                <option value="public">public</option>
                <option value="private">private</option>
                <option value="internal">internal</option>
              </select>
            </Field>
          </div>

          <div className="mt-5 rounded-[18px] border border-ink/10 bg-white/65 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-bold text-ink">
                <Icon name="terminal" size={16} />
                Automated command
              </div>
              <CopyButton text={launchCommand} />
            </div>
            <pre className="m-0 overflow-x-auto whitespace-pre-wrap rounded-[12px] bg-ink p-4 text-xs leading-6 text-white"><code>{launchCommand}</code></pre>
            {repoForDeploy !== launch.githubRepo.trim() && launch.githubRepo.trim() && (
              <p className="mt-3 text-xs font-bold text-muted">Using repository root: {repoForDeploy}</p>
            )}
          </div>
        </section>
      )}

      <section className="mt-[18px] rounded-[26px] border border-ink/10 bg-[#fffcf1d9] p-5 shadow-[0_18px_50px_rgba(20,33,31,0.08)] backdrop-blur-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-leaf">Streamlit Cloud</p>
            <h2 className="mt-1 text-2xl font-bold text-ink">Recent stored runs</h2>
          </div>
          <button
            className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/60 px-4 py-3 text-sm font-bold text-ink transition hover:bg-white"
            onClick={loadHistory}
            type="button"
          >
            <Icon name="refresh" size={16} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
        {history.length === 0 ? (
          <div className="mt-5 rounded-[22px] border-2 border-dashed border-ink/10 bg-white/35 p-8 text-center">
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-ink/5 text-ink/30">
              <Icon name="bot" size={24} />
            </div>
            <h3 className="mt-4 text-sm font-bold text-ink">Ready for your first run</h3>
            <p className="mt-2 text-xs leading-5 text-muted">
              Your autonomous debugging history will appear here once you start a run. 
              Fill in the form above and click "Run Agent Mesh" to begin.
            </p>
          </div>
        ) : (
          history.map((run) => (
            <div className="mt-3 flex items-center justify-between rounded-[18px] border border-ink/10 bg-white/45 p-4" key={run._id || run.run_id}>
              <strong>{run.task?.repository || "unknown repository"}</strong>
              <span className="rounded-full bg-lime/60 px-3 py-1 text-xs font-bold uppercase">{run.status}</span>
            </div>
          ))
        )}
      </section>
    </main>
  );
}

const controlClass =
  "w-full rounded-[16px] border border-ink/10 bg-white/70 px-4 py-3 text-sm text-ink outline-none transition placeholder:text-muted/60 focus:border-leaf focus:bg-white focus:ring-4 focus:ring-lime/30";

function Field({ children, className = "", label }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-2 block text-xs font-bold uppercase tracking-[0.1em] text-muted">{label}</span>
      {children}
    </label>
  );
}

function Metric({ icon, label, value, link }) {
  const content = (
    <article className="rounded-[24px] border border-ink/10 bg-[#fffcf1d9] p-5 shadow-[0_18px_50px_rgba(20,33,31,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:bg-white/80">
      <Icon name={icon} size={20} className="text-ink" />
      <span className="mt-3 block text-sm text-muted">{label}</span>
      <strong className="mt-2 block text-2xl font-bold text-ink">{value}</strong>
    </article>
  );

  if (link) {
    return <a href={link} target="_blank" rel="noreferrer" className="no-underline">{content}</a>;
  }
  return content;
}

function CopyButton({ text }) {
  const [copied, setCopied] = React.useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      onClick={handleCopy}
      type="button"
      title="Copy to clipboard"
      className="ml-2 inline-flex items-center gap-1 rounded-md border border-ink/10 bg-white/60 px-2 py-0.5 text-xs font-bold text-ink transition hover:bg-white"
    >
      <Icon name="copy" size={12} />
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function AgentCard({ card }) {
  const isAutoFix = card.agent === "autofix-agent";
  const isVerdict = card.agent === "verdict-agent";
  const findings = card.findings || [];
  const displayFindings = (isAutoFix || isVerdict) ? findings : findings.slice(0, 5);

  return (
    <article className={`rounded-[24px] border p-5 shadow-[0_18px_50px_rgba(20,33,31,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:bg-white/80 ${
      isVerdict
        ? "border-[#d69e2e]/50 bg-[#fff9dbd9] col-span-full ring-4 ring-[#d69e2e]/10"
        : isAutoFix
          ? "border-leaf/40 bg-[#f0fff4d9] col-span-full"
          : "border-ink/10 bg-[#fffcf1d9]"
    }`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isAutoFix && <Icon name="pr" size={20} className="text-leaf" />}
          {isVerdict && <Icon name="shield" size={20} className="text-[#d69e2e]" />}
          <h2 className={`text-xl font-bold ${isVerdict ? "text-[#8a6200]" : "text-ink"}`}>{card.agent}</h2>
          {isAutoFix && <span className="rounded-full border border-leaf/30 bg-lime/40 px-2 py-0.5 text-xs font-bold text-leaf">Auto PR</span>}
          {isVerdict && <span className="rounded-full border border-[#d69e2e]/30 bg-[#fff1c7] px-2 py-0.5 text-xs font-bold text-[#8a6200]">Final Verdict</span>}
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${statusClass(card.status)}`}>{card.status}</span>
      </div>
      <p className={`mt-4 leading-7 ${isVerdict ? "text-[#5a4300] font-medium" : "text-muted"}`}>{card.summary}</p>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-muted">
        {displayFindings.map((finding, index) => {
          const isCmd = finding.detail && (
            finding.detail.startsWith("git ") ||
            finding.detail.startsWith("gh ") ||
            finding.detail.startsWith("vercel") ||
            finding.detail.startsWith("python") ||
            finding.detail.startsWith("npm") ||
            finding.detail.startsWith("pip") ||
            finding.detail.startsWith("$env:") ||
            finding.detail.includes("\\scripts\\")
          );
          const isUrl = finding.detail && finding.detail.startsWith("http");
          return (
            <li key={`${card.agent}-${index}`} className={`rounded-[12px] border px-4 py-2 ${
              isVerdict ? "border-[#d69e2e]/10 bg-white/70" : "border-ink/5 bg-white/50"
            }`}>
              <span className={`font-bold ${isVerdict ? "text-[#8a6200]" : "text-ink"}`}>{finding.title}: </span>
              {isUrl ? (
                <span className="inline-flex items-center gap-2">
                  <a className="font-bold text-leaf underline" href={finding.detail} target="_blank" rel="noreferrer">Open link</a>
                  <CopyButton text={finding.detail} />
                </span>
              ) : isCmd ? (
                <span className="inline-flex items-center gap-1">
                  <code className="rounded bg-ink/10 px-2 py-0.5 font-mono text-xs text-ink">{finding.detail}</code>
                  <CopyButton text={finding.detail} />
                </span>
              ) : (
                <span>{finding.detail}</span>
              )}
            </li>
          );
        })}
      </ul>
      {!isAutoFix && !isVerdict && findings.length > 5 && (
        <p className="mt-3 text-xs font-bold text-muted">+{findings.length - 5} more findings…</p>
      )}

    </article>
  );
}

function statusClass(status) {
  if (status === "failed") return "bg-[#ffe5dd] text-[#a03224]";
  if (status === "passed") return "bg-[#dff5e9] text-leaf";
  return "bg-[#fff1c7] text-[#8a6200]";
}

createRoot(document.getElementById("root")).render(<App />);

