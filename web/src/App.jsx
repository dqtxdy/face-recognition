import {
  Activity,
  BadgeCheck,
  Ban,
  Binary,
  CircuitBoard,
  Database,
  FileImage,
  FileKey2,
  Fingerprint,
  Gauge,
  KeyRound,
  LockKeyhole,
  Network,
  RefreshCw,
  ScanFace,
  Server,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const QUERY_API_URL = new URLSearchParams(window.location.search).get("apiUrl");
const DEFAULT_API_URL =
  QUERY_API_URL ?? import.meta.env.VITE_TRUSTFACECHAIN_API_URL ?? "http://127.0.0.1:8080";
const SAMPLE_IMAGE_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

const models = [
  { id: "demo-image-hash-v1", label: "Image Hash", status: "Local" },
  { id: "insightface-buffalo_s", label: "Buffalo-S", status: "Fast" },
  { id: "insightface-buffalo_l", label: "Buffalo-L", status: "Strong" },
  { id: "demo-hash-v1", label: "Text Hash", status: "Fallback" },
];

const datasetRows = [
  { name: "Smoke", scope: "20 LFW pairs", state: "Weak" },
  { name: "Defense", scope: "Full LFW 6000", state: "Required" },
  { name: "Target", scope: "LFW + CALFW/CPLFW + XQLFW", state: "Next" },
];

const trustStages = [
  { icon: ScanFace, label: "Capture" },
  { icon: Fingerprint, label: "Embed" },
  { icon: LockKeyhole, label: "Encrypt" },
  { icon: Network, label: "Commit" },
];

function App() {
  const [apiUrl, setApiUrl] = usePersistentState(
    "tfc-api-url",
    DEFAULT_API_URL,
    Boolean(QUERY_API_URL),
  );
  const [apiKey, setApiKey] = usePersistentState("tfc-api-key", "");
  const [health, setHealth] = useState({ status: "unknown", detail: "Not checked" });
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [subjectId, setSubjectId] = useState("subject-pilot-001");
  const [modelVersion, setModelVersion] = useState("demo-image-hash-v1");
  const [threshold, setThreshold] = useState(0.62);
  const [mode, setMode] = useState("image");
  const [biometricText, setBiometricText] = useState("pilot sample");
  const [imageBase64, setImageBase64] = useState(SAMPLE_IMAGE_BASE64);
  const [consentPurpose, setConsentPurpose] = useState("pilot access control");
  const [result, setResult] = useState(null);
  const [busyAction, setBusyAction] = useState("");

  const api = useMemo(() => createApiClient(apiUrl, apiKey), [apiUrl, apiKey]);
  const payload = useMemo(() => {
    if (mode === "image") {
      return { image_base64: imageBase64 };
    }
    return { biometric_input: biometricText };
  }, [biometricText, imageBase64, mode]);

  useEffect(() => {
    checkHealth();
    refreshState();
  }, []);

  async function checkHealth() {
    try {
      const data = await api.get("/health", { publicEndpoint: true });
      setHealth({ status: "online", detail: data.service });
    } catch (error) {
      setHealth({ status: "offline", detail: error.message });
    }
  }

  async function refreshState() {
    setBusyAction("refresh");
    try {
      const [nextMetrics, audit] = await Promise.all([
        api.get("/v1/metrics"),
        api.get("/v1/audit?limit=12"),
      ]);
      setMetrics(nextMetrics);
      setEvents(audit.events ?? []);
    } catch (error) {
      setResult({ type: "error", title: "Refresh failed", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function enroll() {
    setBusyAction("enroll");
    try {
      const data = await api.post("/v1/enroll", {
        subject_id: subjectId,
        model_version: modelVersion,
        allow_reenroll: true,
        consent: {
          purpose: consentPurpose,
          scope: ["enrollment", "verification", "audit"],
          operator: "pilot-console",
        },
        ...payload,
      });
      setResult({
        type: "success",
        title: "Enrolled",
        detail: shortHash(data.templateCommitment),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Enroll failed", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function verify() {
    setBusyAction("verify");
    try {
      const data = await api.post("/v1/verify", {
        subject_id: subjectId,
        threshold: Number(threshold),
        ...payload,
      });
      setResult({
        type: data.accepted ? "success" : "warn",
        title: data.accepted ? "Accepted" : "Rejected",
        detail: `${data.score.toFixed(4)} / ${data.threshold}`,
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Verify failed", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function revoke() {
    setBusyAction("revoke");
    try {
      const data = await api.post("/v1/revoke", {
        subject_id: subjectId,
        reason: "pilot operator revocation",
      });
      setResult({
        type: "warn",
        title: "Revoked",
        detail: shortHash(data.eventHash),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Revocation failed", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function onImageFile(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const dataUrl = await fileToDataUrl(file);
    setImageBase64(dataUrl.split(",", 2)[1] ?? "");
  }

  const activeModel = models.find((model) => model.id === modelVersion) ?? models[0];
  const imagePreviewSrc = imageBase64 ? `data:image/png;base64,${imageBase64}` : "";
  const showImagePlaceholder = imageBase64 === SAMPLE_IMAGE_BASE64;
  const latestEvent = events[0];
  const activeRatio =
    metrics?.identities > 0
      ? Math.round((metrics.activeIdentities / metrics.identities) * 100)
      : 0;

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>TrustFaceChain</strong>
            <span>Pilot</span>
          </div>
        </div>
        <nav className="nav-list">
          <a href="#operations">Ops</a>
          <a href="#audit">Audit</a>
          <a href="#readiness">Gates</a>
        </nav>
        <div className={`health health-${health.status}`}>
          <Server size={16} />
          <span>{health.status}</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Live Pilot</p>
            <h1>Verification Console</h1>
          </div>
          <div className="top-actions">
            <div className="signal-card">
              <span>Trust state</span>
              <strong>{activeRatio}% active</strong>
            </div>
            <button className="icon-button" onClick={refreshState} disabled={busyAction === "refresh"}>
              <RefreshCw size={18} />
              <span>Refresh</span>
            </button>
          </div>
        </header>

        <section className="status-strip" aria-label="System metrics">
          <Metric icon={Database} label="Identities" value={metrics?.identities ?? "-"} />
          <Metric icon={ShieldCheck} label="Active" value={metrics?.activeIdentities ?? "-"} />
          <Metric icon={Ban} label="Revoked" value={metrics?.revokedIdentities ?? "-"} />
          <Metric icon={Activity} label="Events" value={metrics?.auditEvents ?? "-"} />
        </section>

        <section className="mission-strip" aria-label="Trust pipeline">
          {trustStages.map((stage, index) => (
            <div className="trust-stage" key={stage.label}>
              <stage.icon size={18} />
              <span>{stage.label}</span>
              {index < trustStages.length - 1 ? <i aria-hidden="true" /> : null}
            </div>
          ))}
        </section>

        <section className="layout-grid" id="operations">
          <section className="panel operation-panel" aria-labelledby="enroll-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Identity</p>
                <h2 id="enroll-title">Enroll / verify</h2>
              </div>
              <span className="model-pill">{activeModel.status}</span>
            </div>

            <div className="identity-console">
              <div className="sample-stage">
                <div className="stage-toolbar">
                  <span>Sample</span>
                  <strong>{mode}</strong>
                </div>
                {mode === "image" ? (
                  <div className="face-preview">
                    {imageBase64 && !showImagePlaceholder ? (
                      <img src={imagePreviewSrc} alt="" />
                    ) : (
                      <div className="biometric-mark" aria-hidden="true">
                        <span />
                        <i />
                        <b />
                      </div>
                    )}
                    <span className="scan-line" aria-hidden="true" />
                  </div>
                ) : (
                  <div className="text-preview">
                    <KeyRound size={42} />
                    <strong>{biometricText || "empty"}</strong>
                  </div>
                )}
                <div className="hash-strip">
                  <span>{subjectId}</span>
                  <strong>{activeModel.label}</strong>
                </div>
              </div>

              <div className="control-stack">
                <div className="form-grid">
                  <label>
                    <span>Subject ID</span>
                    <input value={subjectId} onChange={(event) => setSubjectId(event.target.value)} />
                  </label>
                  <label>
                    <span>Model</span>
                    <select value={modelVersion} onChange={(event) => setModelVersion(event.target.value)}>
                      {models.map((model) => (
                        <option value={model.id} key={model.id}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Threshold</span>
                    <input
                      type="number"
                      min="-1"
                      max="1"
                      step="0.01"
                      value={threshold}
                      onChange={(event) => setThreshold(event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Purpose</span>
                    <input value={consentPurpose} onChange={(event) => setConsentPurpose(event.target.value)} />
                  </label>
                </div>

                <div className="segmented" role="tablist" aria-label="Biometric payload type">
                  <button className={mode === "image" ? "selected" : ""} onClick={() => setMode("image")}>
                    <FileImage size={16} />
                    <span>Image</span>
                  </button>
                  <button className={mode === "text" ? "selected" : ""} onClick={() => setMode("text")}>
                    <KeyRound size={16} />
                    <span>Text</span>
                  </button>
                </div>

                {mode === "image" ? (
                  <div className="image-input">
                    <label className="file-control">
                      <Upload size={18} />
                      <span>Upload</span>
                      <input type="file" accept="image/png,image/jpeg" onChange={onImageFile} />
                    </label>
                    <textarea
                      aria-label="Base64 image payload"
                      value={imageBase64}
                      onChange={(event) => setImageBase64(event.target.value)}
                      rows={5}
                    />
                  </div>
                ) : (
                  <label className="text-input">
                    <span>Text sample</span>
                    <input value={biometricText} onChange={(event) => setBiometricText(event.target.value)} />
                  </label>
                )}

                <div className="action-row">
                  <button className="command primary" onClick={enroll} disabled={Boolean(busyAction)}>
                    <BadgeCheck size={18} />
                    <span>Enroll</span>
                  </button>
                  <button className="command" onClick={verify} disabled={Boolean(busyAction)}>
                    <Gauge size={18} />
                    <span>Verify</span>
                  </button>
                  <button className="command danger" onClick={revoke} disabled={Boolean(busyAction)}>
                    <Ban size={18} />
                    <span>Revoke</span>
                  </button>
                </div>

                {result ? (
                  <div className={`result result-${result.type}`}>
                    <strong>{result.title}</strong>
                    <span>{result.detail}</span>
                  </div>
                ) : null}
              </div>
            </div>
          </section>

          <section className="panel settings-panel" aria-labelledby="settings-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Connection</p>
                <h2 id="settings-title">API</h2>
              </div>
            </div>
            <label>
              <span>API URL</span>
              <input value={apiUrl} onChange={(event) => setApiUrl(event.target.value)} />
            </label>
            <label>
              <span>API key</span>
              <input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                type="password"
                autoComplete="off"
              />
            </label>
            <button className="command" onClick={checkHealth}>
              <Server size={18} />
              <span>Ping</span>
            </button>
            <div className="assurance-stack">
              <div>
                <FileKey2 size={16} />
                <span>No raw storage</span>
              </div>
              <div>
                <Binary size={16} />
                <span>Commitment only</span>
              </div>
              <div>
                <CircuitBoard size={16} />
                <span>{latestEvent?.eventType ?? "No event"}</span>
              </div>
            </div>
            <div className="model-list">
              {models.map((model) => (
                <button
                  className={model.id === modelVersion ? "model-row active" : "model-row"}
                  key={model.id}
                  onClick={() => setModelVersion(model.id)}
                >
                  <span>{model.label}</span>
                  <strong>{model.status}</strong>
                </button>
              ))}
            </div>
          </section>
        </section>

        <section className="two-column">
          <section className="panel" id="audit" aria-labelledby="audit-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Audit</p>
                <h2 id="audit-title">Events</h2>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Subject</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length ? (
                    events.map((event) => (
                      <tr key={event.eventId}>
                        <td>{event.eventType}</td>
                        <td>{event.subjectId}</td>
                        <td>{formatDate(event.createdAt)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3">No events</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel" id="readiness" aria-labelledby="readiness-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Evidence</p>
                <h2 id="readiness-title">Dataset gates</h2>
              </div>
            </div>
            <div className="readiness-list">
              {datasetRows.map((row) => (
                <div className="readiness-row" key={row.name}>
                  <span>{row.name}</span>
                  <strong>{row.scope}</strong>
                  <em>{row.state}</em>
                </div>
              ))}
            </div>
          </section>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="metric">
      <Icon size={18} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function createApiClient(apiUrl, apiKey) {
  const baseUrl = apiUrl.replace(/\/+$/, "");

  async function request(path, options = {}) {
    const headers = {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(apiKey && !options.publicEndpoint ? { "X-TrustFace-Key": apiKey } : {}),
    };
    const response = await fetch(`${baseUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = {};
    }
    if (!response.ok) {
      const detail = data.detail;
      throw new Error(Array.isArray(detail) ? detail[0]?.msg ?? response.statusText : detail ?? response.statusText);
    }
    return data;
  }

  return {
    get: (path, options) => request(path, options),
    post: (path, body) => request(path, { method: "POST", body }),
  };
}

function usePersistentState(key, initialValue, preferInitialValue = false) {
  const [value, setValue] = useState(() =>
    preferInitialValue ? initialValue : localStorage.getItem(key) ?? initialValue,
  );
  useEffect(() => {
    localStorage.setItem(key, value);
  }, [key, value]);
  return [value, setValue];
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function shortHash(value) {
  if (!value) {
    return "-";
  }
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

export default App;
