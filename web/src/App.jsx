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
  { id: "demo-image-hash-v1", label: "Deterministic Image Hash", status: "Local" },
  { id: "insightface-buffalo_s", label: "InsightFace Buffalo-S", status: "ArcFace Mobile" },
  { id: "insightface-buffalo_l", label: "InsightFace Buffalo-L", status: "ArcFace High-Res" },
];

const datasetRows = [
  { name: "NIST LFW Standard", scope: "6,000 balanced pairs evaluation", state: "Completed" },
  { name: "Synthetic Robustness", scope: "Pose, light, blur corruptions test", state: "Completed" },
  { name: "Cross-Age / Quality", scope: "CALFW / XQLFW extreme variations", state: "In Pipeline" },
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
  const [chainState, setChainState] = useState({ status: "idle", detail: "Unchecked" });
  const [apiKey, setApiKey] = usePersistentState("tfc-api-key", "");
  const [health, setHealth] = useState({ status: "unknown", detail: "Unchecked" });
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [subjectId, setSubjectId] = usePersistentState("tfc-subject-id", "subject-pilot-001");
  const [modelVersion, setModelVersion] = useState("demo-image-hash-v1");
  const [threshold, setThreshold] = useState(0.62);
  const [imageBase64, setImageBase64] = useState(SAMPLE_IMAGE_BASE64);
  const [requireLiveness, setRequireLiveness] = useState(false);
  const [livenessReport, setLivenessReport] = useState(null);
  const [result, setResult] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [useWebcam, setUseWebcam] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);
  const [isSubjectEnrolled, setIsSubjectEnrolled] = useState(false);
  const [enrolledImages, setEnrolledImages] = useState(() => {
    try {
      const saved = localStorage.getItem("tfc-enrolled-images");
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error("Failed to load enrolled images", e);
    }
    return {
      "subject-pilot-001": SAMPLE_IMAGE_BASE64,
    };
  });

  useEffect(() => {
    try {
      localStorage.setItem("tfc-enrolled-images", JSON.stringify(enrolledImages));
    } catch (e) {
      console.error("Failed to save enrolled images", e);
    }
  }, [enrolledImages]);

  const api = useMemo(() => createApiClient(apiUrl, apiKey), [apiUrl, apiKey]);
  const payload = useMemo(() => {
    return { image_base64: imageBase64 };
  }, [imageBase64]);

  async function checkIdentity() {
    if (!subjectId.trim()) {
      setIsSubjectEnrolled(false);
      return;
    }
    try {
      const data = await api.get(`/v1/identities/${subjectId}`);
      setIsSubjectEnrolled(data && !data.revoked);
    } catch {
      setIsSubjectEnrolled(false);
    }
  }

  useEffect(() => {
    checkHealth();
    refreshState();
  }, []);

  // Automatically check identity existence and blockchain revocation state whenever the subject ID changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (subjectId.trim()) {
        checkChain();
        checkIdentity();
      } else {
        setIsSubjectEnrolled(false);
      }
    }, 500); // Debounce to avoid spamming calls
    return () => clearTimeout(timer);
  }, [subjectId, rpcUrl, contractAddress, api]);

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
        title: "Camera Failed",
        detail: error.message || "Could not start camera.",
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
    if (!subjectId.trim()) return;
    try {
      const subjectBytes = await toBytes32(subjectId);
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
        detail: revoked ? "Revoked / Blocked" : "Active",
      });
    } catch (error) {
      setChainState({ status: "offline", detail: error.message });
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
        require_liveness: requireLiveness,
        consent: {
          purpose: "authorized gate access",
          scope: ["enrollment", "verification", "audit"],
          operator: "trust-portal-console",
        },
        ...payload,
      });
      setLivenessReport(data.liveness ?? null);
      setResult({
        type: "success",
        title: "Proof Committed",
        detail: resultDetail(shortHash(data.templateCommitment), data.liveness),
      });
      if (imageBase64) {
        setEnrolledImages((prev) => ({
          ...prev,
          [subjectId]: imageBase64,
        }));
      }
      setIsSubjectEnrolled(true);
      await Promise.all([refreshState(), checkChain()]);
    } catch (error) {
      setResult({ type: "error", title: "Enrollment Rejected", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function verify() {
    setBusyAction("verify");
    try {
      // Direct integration: Check blockchain state before verifying
      await Promise.all([checkChain(), checkIdentity()]);

      const data = await api.post("/v1/verify", {
        subject_id: subjectId,
        threshold: Number(threshold),
        require_liveness: requireLiveness,
        ...payload,
      });
      setLivenessReport(data.liveness ?? null);
      setResult({
        type: data.accepted ? "success" : "warn",
        title: data.accepted ? "Identity Verified" : "Verification Failed",
        detail: resultDetail(`${data.score.toFixed(4)} (Threshold: ${data.threshold})`, data.liveness),
      });
      await refreshState();
    } catch (error) {
      setResult({ type: "error", title: "Verification Rejected", detail: error.message });
    } finally {
      setBusyAction("");
    }
  }

  async function revoke() {
    setBusyAction("revoke");
    try {
      const data = await api.post("/v1/revoke", {
        subject_id: subjectId,
        reason: "operator template revocation request",
      });
      setResult({
        type: "warn",
        title: "Proof Anchor Revoked",
        detail: `Anchor event: ${shortHash(data.eventHash)}`,
      });
      setEnrolledImages((prev) => {
        const next = { ...prev };
        delete next[subjectId];
        return next;
      });
      setIsSubjectEnrolled(false);
      await Promise.all([refreshState(), checkChain()]);
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
  const livenessState = livenessLabel(livenessReport);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="header-container">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <div>
              <strong>TrustFaceChain</strong>
              <span>Identity Hub</span>
            </div>
          </div>
          <div className="header-actions">
            <div className={`health health-${health.status}`}>
              <Server size={14} />
              <span>API Node: {health.status}</span>
            </div>
            <button className="icon-button" onClick={refreshState} disabled={busyAction === "refresh"}>
              <RefreshCw size={14} />
              <span>Sync Ledger</span>
            </button>
          </div>
        </div>
      </header>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>TrustFace Console</h1>
          </div>
        </header>

        <section className="status-strip" aria-label="System stats">
          <Metric icon={Database} label="Enrolled Users" value={metrics?.identities ?? "-"} />
          <Metric icon={ShieldCheck} label="Active Keys" value={metrics?.activeIdentities ?? "-"} />
          <Metric icon={Ban} label="Revoked Keys" value={metrics?.revokedIdentities ?? "-"} />
          <Metric icon={Activity} label="Total Logs" value={metrics?.auditEvents ?? "-"} />
        </section>

        <section className="layout-grid" id="operations">
          {/* Main Scanner Section */}
          <section className="panel operation-panel" aria-labelledby="scanner-title">
            <div className="panel-heading">
              <div>
                <h2 id="scanner-title">Biometric Scanner</h2>
              </div>
              <span className="model-pill">{activeModel.status}</span>
            </div>

            <div className="identity-console">
              <div className="sample-stage">
                <div className="stage-toolbar">
                  <span>Dual Biometric Preview</span>
                  <strong>Camera Feed</strong>
                </div>
                <div className="dual-preview">
                  {/* Left Frame: Registered Face (Reference Proof) */}
                  <div className="face-preview">
                    <span className="preview-label">Registered Face</span>
                    {isSubjectEnrolled ? (
                      enrolledImages[subjectId] ? (
                        <img
                          src={`data:image/png;base64,${enrolledImages[subjectId]}`}
                          alt="Registered Reference"
                        />
                      ) : (
                        <div className="text-preview" style={{ border: "none", minHeight: "auto", padding: "16px" }}>
                          <LockKeyhole size={32} style={{ color: "var(--accent)" }} />
                          <strong style={{ fontSize: "0.8rem", color: "var(--muted)", textAlign: "center", marginTop: "8px" }}>
                            Proof Active.<br />Raw image deleted for privacy.
                          </strong>
                        </div>
                      )
                    ) : (
                      <div className="text-preview" style={{ border: "none", minHeight: "auto", padding: "16px" }}>
                        <Ban size={32} style={{ color: "var(--muted)" }} />
                        <strong style={{ fontSize: "0.8rem", color: "var(--muted)", textAlign: "center", marginTop: "8px" }}>
                          Not Enrolled /<br />Unregistered
                        </strong>
                      </div>
                    )}
                  </div>

                  {/* Right Frame: Live Probe / Scanner Feed */}
                  <div className="face-preview">
                    <span className="preview-label">Scanner Feed</span>
                    {useWebcam ? (
                      <video ref={videoRef} autoPlay playsInline className="webcam-video" />
                    ) : imageBase64 && !showImagePlaceholder ? (
                      <img src={imagePreviewSrc} alt="Scanner Probe" />
                    ) : (
                      <div className="biometric-mark" aria-hidden="true">
                        <span />
                        <i />
                        <b />
                      </div>
                    )}
                    <span className="scan-line" aria-hidden="true" />
                  </div>
                </div>
                
                <div className="liveness-card">
                  <ShieldCheck size={14} />
                  <span>Liveness (PAD):</span>
                  <strong className={livenessState.tone === "pass" ? "text-accent" : livenessState.tone === "review" ? "text-amber" : ""}>
                    {livenessState.label}
                  </strong>
                </div>

                <div className="liveness-card" style={{ borderTop: "1px solid var(--line)" }}>
                  <Network size={14} />
                  <span>On-Chain Status:</span>
                  <strong style={{ color: chainState.detail === "Active" ? "var(--accent)" : chainState.detail === "Unchecked" ? "var(--muted)" : "var(--danger)" }}>
                    {chainState.detail}
                  </strong>
                </div>
              </div>
            </div>
          </section>

          {/* Right Section: Parameter Configuration & Setup Panel */}
          <section className="settings-panel">
            <div className="panel">
              <div className="panel-heading">
                <h2>Parameters & Setup</h2>
              </div>
              <div className="control-stack">
                <div className="form-grid">
                  <label>
                    <span>Subject ID</span>
                    <input value={subjectId} onChange={(event) => setSubjectId(event.target.value)} placeholder="e.g. subject-001" />
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
                </div>

                <div className="form-grid">
                  <label style={{ gridColumn: "span 2" }}>
                    <span>Model</span>
                    <select value={modelVersion} onChange={(event) => setModelVersion(event.target.value)}>
                      {models.map((model) => (
                        <option value={model.id} key={model.id}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="toggle-row">
                  <span>Enforce Liveness check</span>
                  <input
                    type="checkbox"
                    checked={requireLiveness}
                    onChange={(event) => setRequireLiveness(event.target.checked)}
                  />
                </label>

                <div className="image-input">
                  <div style={{ display: "flex", gap: "8px" }}>
                    <label className="file-control" style={{ flex: 1 }}>
                      <Upload size={14} />
                      <span>Upload File</span>
                      <input type="file" accept="image/png,image/jpeg" onChange={onImageFile} />
                    </label>
                    {!useWebcam ? (
                      <button type="button" className="icon-button" style={{ flex: 1 }} onClick={startWebcam}>
                        <Camera size={14} />
                        <span>Use Webcam</span>
                      </button>
                    ) : (
                      <>
                        <button type="button" className="icon-button command primary" style={{ flex: 1 }} onClick={captureWebcam}>
                          <Camera size={14} />
                          <span>Capture</span>
                        </button>
                        <button type="button" className="icon-button command danger" style={{ flex: 1 }} onClick={stopWebcam}>
                          <Ban size={14} />
                          <span>Cancel</span>
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div className="action-row">
                  <button className="command primary" onClick={enroll} disabled={Boolean(busyAction)}>
                    <BadgeCheck size={16} />
                    <span>Register Face</span>
                  </button>
                  <button className="command" onClick={verify} disabled={Boolean(busyAction)}>
                    <Gauge size={16} />
                    <span>Verify Face</span>
                  </button>
                  <button className="command danger" onClick={revoke} disabled={Boolean(busyAction)}>
                    <Ban size={16} />
                    <span>Revoke Face</span>
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
        </section>

        <section className="two-column">
          <section className="panel" id="audit" aria-labelledby="audit-title">
            <div className="panel-heading">
              <div>
                <h2 id="audit-title">Ledger Logs</h2>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ledger Event</th>
                    <th>Subject ID</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length ? (
                    events.map((event) => (
                      <tr key={event.eventId}>
                        <td style={{ fontWeight: "700", color: "var(--accent)" }}>{event.eventType}</td>
                        <td style={{ fontFamily: "Geist Mono", fontSize: "0.8rem" }}>{event.subjectId}</td>
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
                <h2 id="readiness-title">Compliance Gates</h2>
              </div>
            </div>
            <div className="readiness-list">
              {datasetRows.map((row) => (
                <div className="readiness-row" key={row.name}>
                  <div>
                    <span style={{ display: "block" }}>{row.name}</span>
                    <strong style={{ fontSize: "0.78rem" }}>{row.scope}</strong>
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
  return `${primary} | Liveness: ${label.label}`;
}

function livenessLabel(liveness) {
  if (!liveness) {
    return { label: "Idle", tone: "idle" };
  }
  if (liveness.passed) {
    return { label: "Passed", tone: "pass" };
  }
  return { label: "Failed", tone: "review" };
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
