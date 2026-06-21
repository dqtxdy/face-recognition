import {
  Activity,
  BadgeCheck,
  Ban,
  Binary,
  Camera,
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
import { useEffect, useMemo, useState, useRef } from "react";

const QUERY_API_URL = new URLSearchParams(window.location.search).get("apiUrl");
const QUERY_RPC_URL = new URLSearchParams(window.location.search).get("rpcUrl");
const QUERY_CONTRACT_ADDRESS = new URLSearchParams(window.location.search).get("contractAddress");
const DEFAULT_API_URL =
  QUERY_API_URL ?? import.meta.env.VITE_TRUSTFACECHAIN_API_URL ?? "http://127.0.0.1:8080";
const DEFAULT_RPC_URL =
  QUERY_RPC_URL ?? import.meta.env.VITE_TRUSTFACECHAIN_RPC_URL ?? "http://127.0.0.1:8545";
const DEFAULT_CONTRACT_ADDRESS =
  QUERY_CONTRACT_ADDRESS ??
  import.meta.env.VITE_TRUSTFACECHAIN_CONTRACT_ADDRESS ??
  "0x5fbdb2315678afecb367f032d93f642f64180aa3";
const SAMPLE_IMAGE_BASE64 = createDemoImageBase64();
const IS_REVOKED_SELECTOR = "0x4294857f";

const models = [
  { id: "demo-image-hash-v1", label: "Deterministic Image Hash", status: "Local / Fast" },
  { id: "insightface-buffalo_s", label: "InsightFace Buffalo-S", status: "ArcFace Mobile" },
  { id: "insightface-buffalo_l", label: "InsightFace Buffalo-L", status: "ArcFace High-Res" },
  { id: "demo-hash-v1", label: "Fallback Text Embedder", status: "Debug Only" },
];

const datasetRows = [
  { name: "NIST LFW Standard", scope: "6,000 balanced pairs evaluation", state: "Completed" },
  { name: "Synthetic Robustness", scope: "Pose, light, blur corruptions test", state: "Completed" },
  { name: "Cross-Age / Quality", scope: "CALFW / XQLFW extreme variations", state: "In Pipeline" },
];

const trustStages = [
  { icon: ScanFace, label: "1. Capture Frame" },
  { icon: Fingerprint, label: "2. Generate Vector" },
  { icon: LockKeyhole, label: "3. Mask Commitment" },
  { icon: Network, label: "4. Consensus Anchor" },
];

function App() {
  const [apiUrl, setApiUrl] = usePersistentState(
    "tfc-api-url",
    DEFAULT_API_URL,
    Boolean(QUERY_API_URL),
  );
  const [rpcUrl, setRpcUrl] = usePersistentState(
    "tfc-rpc-url",
    DEFAULT_RPC_URL,
    Boolean(QUERY_RPC_URL),
  );
  const [contractAddress, setContractAddress] = usePersistentState(
    "tfc-contract-address",
    DEFAULT_CONTRACT_ADDRESS,
    Boolean(QUERY_CONTRACT_ADDRESS),
  );
  const [chainSubject, setChainSubject] = usePersistentState("tfc-chain-subject", "subject-demo-001");
  const [chainState, setChainState] = useState({ status: "idle", detail: "Unchecked" });
  const [apiKey, setApiKey] = usePersistentState("tfc-api-key", "");
  const [health, setHealth] = useState({ status: "unknown", detail: "Unchecked" });
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [subjectId, setSubjectId] = useState("subject-pilot-001");
  const [modelVersion, setModelVersion] = useState("demo-image-hash-v1");
  const [threshold, setThreshold] = useState(0.62);
  const [mode, setMode] = useState("image");
  const [biometricText, setBiometricText] = useState("pilot sample");
  const [imageBase64, setImageBase64] = useState(SAMPLE_IMAGE_BASE64);
  const [consentPurpose, setConsentPurpose] = useState("authorized gate access");
  const [requireLiveness, setRequireLiveness] = useState(false);
  const [livenessReport, setLivenessReport] = useState(null);
  const [result, setResult] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [useWebcam, setUseWebcam] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);

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

  async function startWebcam() {
    setLivenessReport(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
      });
      setStream(mediaStream);
      setUseWebcam(true);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      }, 50);
    } catch (error) {
      setResult({
        type: "error",
        title: "Camera Access Failed",
        detail: error.message || "No camera device found.",
      });
    }
  }

  function stopWebcam() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setUseWebcam(false);
  }

  function captureWebcam() {
    if (videoRef.current) {
      const video = videoRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 320;
      canvas.height = video.videoHeight || 240;
      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/png");
      setImageBase64(dataUrl.split(",", 2)[1] ?? "");
      stopWebcam();
      setResult(null);
    }
  }

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  async function checkHealth() {
    try {
      const data = await api.get("/health", { publicEndpoint: true });
      setHealth({ status: "online", detail: data.service });
    } catch (error) {
      setHealth({ status: "offline", detail: error.message });
    }
  }

  async function checkChain() {
    setBusyAction("chain");
    try {
      const subjectBytes = await toBytes32(chainSubject);
      const data = `${IS_REVOKED_SELECTOR}${subjectBytes.slice(2)}`;
      const response = await fetch(rpcUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "eth_call",
          params: [{ to: contractAddress, data }, "latest"],
        }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        throw new Error(payload.error?.message ?? response.statusText);
      }
      const revoked = BigInt(payload.result || "0x0") !== 0n;
      setChainState({
        status: "online",
        detail: revoked ? "Revoked / Blocked" : "Active / Verified",
      });
    } catch (error) {
      setChainState({ status: "offline", detail: error.message });
    } finally {
      setBusyAction("");
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
      setResult({ type: "error", title: "Sync failed", detail: error.message });
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
        require_liveness: mode === "image" && requireLiveness,
        consent: {
          purpose: consentPurpose,
          scope: ["enrollment", "verification", "audit"],
          operator: "trust-portal-console",
        },
      });
      setLivenessReport(data.liveness ?? null);
      setResult({
        type: "success",
        title: "Proof Committed Successfully",
        detail: resultDetail(shortHash(data.templateCommitment), data.liveness),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Enrollment Rejected", detail: error.message });
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
        require_liveness: mode === "image" && requireLiveness,
        ...payload,
      });
      setLivenessReport(data.liveness ?? null);
      setResult({
        type: data.accepted ? "success" : "warn",
        title: data.accepted ? "Identity Authenticated" : "Authentication Failed",
        detail: resultDetail(`${data.score.toFixed(4)} (Threshold: ${data.threshold})`, data.liveness),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Verification Error", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function revoke() {
    setBusyAction("revoke");
    try {
      const data = await api.post("/v1/revoke", {
        subject_id: subjectId,
        reason: "operator requested template revocation",
      });
      setResult({
        type: "warn",
        title: "Cryptographic Anchor Revoked",
        detail: shortHash(data.eventHash),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Revocation Rejected", detail: error.message });
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
    setLivenessReport(null);
  }

  const activeModel = models.find((model) => model.id === modelVersion) ?? models[0];
  const imagePreviewSrc = imageBase64 ? `data:image/png;base64,${imageBase64}` : "";
  const showImagePlaceholder = imageBase64 === SAMPLE_IMAGE_BASE64;
  const latestEvent = events[0];
  const activeRatio =
    metrics?.identities > 0
      ? Math.round((metrics.activeIdentities / metrics.identities) * 100)
      : 0;
  const livenessState = livenessLabel(livenessReport);

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary Portal Navigation">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>TrustFaceChain</strong>
            <span>Identity Hub</span>
          </div>
        </div>
        <nav className="nav-list">
          <a href="#operations">Identity Scanner</a>
          <a href="#audit">Verification Ledger</a>
          <a href="#readiness">Compliance Gates</a>
        </nav>
        <div className={`health health-${health.status}`}>
          <Server size={16} />
          <span>API Node: {health.status}</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Trust Layer Management Console</p>
            <h1>Decentralized Identity Center</h1>
          </div>
          <div className="top-actions">
            <div className="signal-card">
              <span>Secure Anchor Rate</span>
              <strong>{activeRatio}% Active</strong>
            </div>
            <button className="icon-button" onClick={refreshState} disabled={busyAction === "refresh"}>
              <RefreshCw size={16} />
              <span>Sync Ledger</span>
            </button>
          </div>
        </header>

        <section className="status-strip" aria-label="System Cryptographic metrics">
          <Metric icon={Database} label="Registered Identity Commitments" value={metrics?.identities ?? "-"} />
          <Metric icon={ShieldCheck} label="Active Secure Anchors" value={metrics?.activeIdentities ?? "-"} />
          <Metric icon={Ban} label="Revoked Biometrics" value={metrics?.revokedIdentities ?? "-"} />
          <Metric icon={Activity} label="Ledger Transaction Events" value={metrics?.auditEvents ?? "-"} />
        </section>

        <section className="mission-strip" aria-label="Decentralized Trust Pipeline Process">
          {trustStages.map((stage) => (
            <div className="trust-stage" key={stage.label}>
              <stage.icon size={18} />
              <span>{stage.label}</span>
            </div>
          ))}
        </section>

        <section className="layout-grid" id="operations">
          <section className="panel operation-panel" aria-labelledby="enroll-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Biometric Capture & Verification</p>
                <h2 id="enroll-title">Secure Scanner Gateway</h2>
              </div>
              <span className="model-pill">{activeModel.status}</span>
            </div>

            <div className="identity-console">
              <div className="sample-stage">
                <div className="stage-toolbar">
                  <span>Scanner Feed</span>
                  <strong>{mode} input</strong>
                </div>
                {mode === "image" ? (
                  <div className="face-preview">
                    {useWebcam ? (
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className="webcam-video"
                      />
                    ) : imageBase64 && !showImagePlaceholder ? (
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
                    <KeyRound size={36} />
                    <strong>{biometricText || "empty vector string"}</strong>
                  </div>
                )}
                <div className="hash-strip">
                  <span>Subject: {subjectId}</span>
                </div>
                <div className={`liveness-card liveness-${livenessState.tone}`}>
                  <ShieldCheck size={14} />
                  <span>Liveness (PAD):</span>
                  <strong>{livenessState.label}</strong>
                </div>
              </div>

              <div className="control-stack">
                <div className="form-grid">
                  <label>
                    <span>Subject Identifier</span>
                    <input value={subjectId} onChange={(event) => setSubjectId(event.target.value)} />
                  </label>
                  <label>
                    <span>Verification Threshold</span>
                    <input
                      type="number"
                      min="-1"
                      max="1"
                      step="0.01"
                      value={threshold}
                      onChange={(event) => setThreshold(event.target.value)}
                    />
                  </label>
                </div>

                <div className="form-grid">
                  <label>
                    <span>Algorithmic Model</span>
                    <select value={modelVersion} onChange={(event) => setModelVersion(event.target.value)}>
                      {models.map((model) => (
                        <option value={model.id} key={model.id}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Consent Objective</span>
                    <input value={consentPurpose} onChange={(event) => setConsentPurpose(event.target.value)} />
                  </label>
                </div>

                <div className="segmented" role="tablist" aria-label="Biometric payload source type">
                  <button className={mode === "image" ? "selected" : ""} onClick={() => setMode("image")}>
                    <FileImage size={14} />
                    <span>Face Camera</span>
                  </button>
                  <button
                    className={mode === "text" ? "selected" : ""}
                    onClick={() => {
                      setMode("text");
                      stopWebcam();
                    }}
                  >
                    <KeyRound size={14} />
                    <span>Mock Text Hash</span>
                  </button>
                </div>

                <label className={`toggle-row ${mode !== "image" ? "disabled" : ""}`}>
                  <span>Enforce Passive Liveness Gate</span>
                  <input
                    type="checkbox"
                    checked={requireLiveness}
                    onChange={(event) => setRequireLiveness(event.target.checked)}
                    disabled={mode !== "image"}
                  />
                </label>

                {mode === "image" ? (
                  <div className="image-input">
                    <div style={{ display: "flex", gap: "8px" }}>
                      <label className="file-control">
                        <Upload size={16} />
                        <span>Upload File</span>
                        <input type="file" accept="image/png,image/jpeg" onChange={onImageFile} />
                      </label>
                      {!useWebcam ? (
                        <button type="button" className="icon-button" onClick={startWebcam}>
                          <Camera size={16} />
                          <span>Use Webcam</span>
                        </button>
                      ) : (
                        <>
                          <button type="button" className="icon-button command primary" onClick={captureWebcam}>
                            <Camera size={16} />
                            <span>Capture Frame</span>
                          </button>
                          <button type="button" className="icon-button command danger" onClick={stopWebcam}>
                            <Ban size={16} />
                            <span>Stop Camera</span>
                          </button>
                        </>
                      )}
                    </div>
                    <textarea
                      aria-label="Base64 image payload output"
                      value={imageBase64}
                      onChange={(event) => setImageBase64(event.target.value)}
                      rows={4}
                      placeholder="Base64 vector data displays here..."
                    />
                  </div>
                ) : (
                  <label className="text-input">
                    <span>Mock Input Token</span>
                    <input value={biometricText} onChange={(event) => setBiometricText(event.target.value)} />
                  </label>
                )}

                <div className="action-row">
                  <button className="command primary" onClick={enroll} disabled={Boolean(busyAction)}>
                    <BadgeCheck size={16} />
                    <span>Commit Proof</span>
                  </button>
                  <button className="command" onClick={verify} disabled={Boolean(busyAction)}>
                    <Gauge size={16} />
                    <span>Verify Identity</span>
                  </button>
                  <button className="command danger" onClick={revoke} disabled={Boolean(busyAction)}>
                    <Ban size={16} />
                    <span>Revoke Anchor</span>
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
                <p className="eyebrow">On-Chain Proof Verification</p>
                <h2 id="settings-title">Ledger Anchors</h2>
              </div>
            </div>
            
            <div className="chain-form">
              <label>
                <span>JSON-RPC Node URL</span>
                <input value={rpcUrl} onChange={(event) => setRpcUrl(event.target.value)} />
              </label>
              <label>
                <span>Solidity Contract Address</span>
                <input value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} />
              </label>
              <label>
                <span>Query Target Subject</span>
                <input value={chainSubject} onChange={(event) => setChainSubject(event.target.value)} />
              </label>
              <button className="command primary" onClick={checkChain} disabled={busyAction === "chain"}>
                <Network size={16} />
                <span>Verify On-Chain Status</span>
              </button>
              {chainState.detail !== "Unchecked" ? (
                <div style={{ marginTop: "8px", fontSize: "0.85rem", fontWeight: "600", color: chainState.status === "online" ? "var(--accent)" : "var(--danger)" }}>
                  Contract Status: {chainState.detail}
                </div>
              ) : null}
            </div>

            <div className="assurance-stack">
              <div>
                <FileKey2 size={16} />
                <span>Privacy Rule: Off-Chain Face Embeddings</span>
              </div>
              <div>
                <ShieldCheck size={16} />
                <span>Security Gate: Liveness Detection (PAD)</span>
              </div>
              <div>
                <Binary size={16} />
                <span>Cryptographic Identity Commitments Only</span>
              </div>
              <div>
                <Network size={16} />
                <span>Immutable Revocation Register Online</span>
              </div>
            </div>
          </section>
        </section>

        <section className="two-column">
          <section className="panel" id="audit" aria-labelledby="audit-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Audit Stream</p>
                <h2 id="audit-title">Ledger Transaction History</h2>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ledger Event Action</th>
                    <th>Subject Identifier</th>
                    <th>Node Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length ? (
                    events.map((event) => (
                      <tr key={event.eventId}>
                        <td style={{ fontWeight: "700", color: "var(--accent)" }}>{event.eventType}</td>
                        <td style={{ fontFamily: "Geist Mono", fontSize: "0.85rem" }}>{event.subjectId}</td>
                        <td>{formatDate(event.createdAt)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" style={{ textAlign: "center", color: "var(--muted)" }}>
                        No ledger transactions found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel" id="readiness" aria-labelledby="readiness-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Academic Validation</p>
                <h2 id="readiness-title">Biometric Compliance Gates</h2>
              </div>
            </div>
            <div className="readiness-list">
              {datasetRows.map((row) => (
                <div className="readiness-row" key={row.name}>
                  <div>
                    <span style={{ display: "block" }}>{row.name}</span>
                    <strong>{row.scope}</strong>
                  </div>
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
      <Icon size={20} />
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

function createDemoImageBase64() {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  const image = context.createImageData(128, 128);
  for (let y = 0; y < 128; y += 1) {
    for (let x = 0; x < 128; x += 1) {
      const index = (y * 128 + x) * 4;
      image.data[index] = 70 + ((x * 3 + y * 5) % 120);
      image.data[index + 1] = 80 + ((x * 7 + y * 2) % 100);
      image.data[index + 2] = 90 + ((x * 5 + y * 11) % 90);
      image.data[index + 3] = 255;
    }
  }
  context.putImageData(image, 0, 0);
  return canvas.toDataURL("image/png").split(",", 2)[1] ?? "";
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

function resultDetail(primary, liveness) {
  const label = livenessLabel(liveness);
  if (label.label === "Idle") {
    return primary;
  }
  return `${primary} | Liveness Verification: ${label.label}`;
}

function livenessLabel(liveness) {
  if (!liveness) {
    return { label: "Idle", tone: "idle" };
  }
  if (liveness.passed) {
    return { label: "Passed", tone: "pass" };
  }
  return { label: "Under Review", tone: "review" };
}

async function toBytes32(value) {
  const trimmed = value.trim();
  if (/^0x[0-9a-fA-F]{64}$/.test(trimmed)) {
    return trimmed.toLowerCase();
  }
  const bytes = new TextEncoder().encode(trimmed);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return `0x${Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")}`;
}

function shortHash(value) {
  if (!value) {
    return "-";
  }
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

export default App;
