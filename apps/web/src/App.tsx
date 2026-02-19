import React, { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "./api/client";
import { StatusBadge } from "./components/StatusBadge";

type Dataset = { id: number; name: string; source_path: string; created_at: string; meta: any; };
type Step = { id: number; name: string; status: string; started_at?: string; finished_at?: string; message?: string; };
type Run = { id: number; dataset_id: number; model_type: string; status: string; created_at: string; started_at?: string; finished_at?: string; metrics: any; artifacts: any; error?: string; steps?: Step[]; };

function fmt(ts?: string) {
  if (!ts) return "-";
  try { return new Date(ts).toLocaleString(); } catch { return ts; }
}

export default function App() {
  const [tab, setTab] = useState<"dashboard"|"datasets"|"runs">("dashboard");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [logTail, setLogTail] = useState<string>("");

  const [dsName, setDsName] = useState("sample");
  const [dsPath, setDsPath] = useState("/data/inbound/sample_timeseries.csv");

  async function refresh() {
    const [d, r] = await Promise.all([
      apiGet<Dataset[]>("/datasets"),
      apiGet<Run[]>("/runs"),
    ]);
    setDatasets(d);
    setRuns(r);
    if (selectedRun) {
      const full = await apiGet<Run>(`/runs/${selectedRun.id}`);
      setSelectedRun(full);
      const logs = await apiGet<{tail:string}>(`/runs/${selectedRun.id}/logs?lines=400`);
      setLogTail(logs.tail || "");
    }
  }

  useEffect(() => { refresh().catch(console.error); }, [tab]);

  // polling on dashboard/runs
  useEffect(() => {
    const t = setInterval(() => refresh().catch(()=>{}), 3000);
    return () => clearInterval(t);
  }, [selectedRun?.id, tab]);

  const recentRuns = useMemo(() => runs.slice(0, 6), [runs]);

  async function createDataset() {
    await apiPost("/datasets", { name: dsName, source_path: dsPath, meta: { note: "created from UI" } });
    await refresh();
    setTab("datasets");
  }

  async function createRun(dataset_id: number) {
    const run = await apiPost<Run>("/runs", { dataset_id, model_type: "baseline_sklearn" });
    setTab("runs");
    setSelectedRun(run);
    await refresh();
  }

  return (
    <div className="container">
      <div className="nav">
        <div className="brand">Exam AI Pipeline Admin</div>
        <button className="btn" onClick={() => setTab("dashboard")} disabled={tab==="dashboard"}>Dashboard</button>
        <button className="btn" onClick={() => setTab("datasets")} disabled={tab==="datasets"}>Datasets</button>
        <button className="btn" onClick={() => setTab("runs")} disabled={tab==="runs"}>Runs</button>
        <div className="spacer" />
        <a className="badge" href="/api/docs" target="_blank">Swagger</a>
      </div>

      {tab === "dashboard" && (
        <>
          <div className="h1">최근 실행</div>
          <div className="grid">
            {recentRuns.map(r => (
              <div key={r.id} className="card" onClick={async () => {
                const full = await apiGet<Run>(`/runs/${r.id}`);
                setSelectedRun(full);
                setTab("runs");
              }} style={{ cursor:"pointer" }}>
                <div className="row" style={{ justifyContent:"space-between" }}>
                  <div><b>Run #{r.id}</b> <span className="muted">dataset {r.dataset_id}</span></div>
                  <StatusBadge status={r.status} />
                </div>
                <div className="muted" style={{ marginTop: 6 }}>
                  created {fmt(r.created_at)} · model {r.model_type}
                </div>
                <div className="row" style={{ marginTop: 10, gap: 8, flexWrap:"wrap" }}>
                  {"accuracy" in (r.metrics||{}) && <span className="badge">acc {(r.metrics.accuracy*100).toFixed(2)}%</span>}
                  {"f1" in (r.metrics||{}) && <span className="badge">f1 {(r.metrics.f1*100).toFixed(2)}%</span>}
                </div>
              </div>
            ))}
            {recentRuns.length === 0 && <div className="card">실행 이력이 없습니다.</div>}
          </div>
        </>
      )}

      {tab === "datasets" && (
        <>
          <div className="h1">데이터셋</div>

          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="muted">name</div>
                <input className="input" value={dsName} onChange={e => setDsName(e.target.value)} />
              </div>
              <div style={{ flex: 2 }}>
                <div className="muted">source_path (container path)</div>
                <input className="input" value={dsPath} onChange={e => setDsPath(e.target.value)} />
              </div>
              <div style={{ alignSelf:"end" }}>
                <button className="btn" onClick={createDataset}>Create</button>
              </div>
            </div>
            <div className="muted" style={{ marginTop: 10 }}>
              MVP는 파일 업로드 대신, 온프레미스 공유폴더를 컨테이너에 마운트한 후 그 경로를 등록하는 방식입니다.
            </div>
          </div>

          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Source path</th><th>Created</th><th></th>
                </tr>
              </thead>
              <tbody>
                {datasets.map(d => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td>{d.name}</td>
                    <td className="muted">{d.source_path}</td>
                    <td className="muted">{fmt(d.created_at)}</td>
                    <td><button className="btn" onClick={() => createRun(d.id)}>Run</button></td>
                  </tr>
                ))}
                {datasets.length === 0 && (
                  <tr><td colSpan={5} className="muted">데이터셋이 없습니다. 위 폼으로 생성하세요.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "runs" && (
        <>
          <div className="h1">실행 이력</div>
          <div className="grid">
            <div className="card">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th><th>Status</th><th>Dataset</th><th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(r => (
                    <tr key={r.id} style={{ cursor:"pointer" }} onClick={async () => {
                      const full = await apiGet<Run>(`/runs/${r.id}`);
                      setSelectedRun(full);
                      const logs = await apiGet<{tail:string}>(`/runs/${r.id}/logs?lines=400`);
                      setLogTail(logs.tail || "");
                    }}>
                      <td>#{r.id}</td>
                      <td><StatusBadge status={r.status} /></td>
                      <td className="muted">{r.dataset_id}</td>
                      <td className="muted">{fmt(r.created_at)}</td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr><td colSpan={4} className="muted">실행 이력이 없습니다.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="card">
              {!selectedRun && <div className="muted">왼쪽에서 Run을 선택하세요.</div>}
              {selectedRun && (
                <>
                  <div className="row" style={{ justifyContent:"space-between" }}>
                    <div>
                      <b>Run #{selectedRun.id}</b> <span className="muted">dataset {selectedRun.dataset_id}</span>
                      <div className="muted">created {fmt(selectedRun.created_at)} · started {fmt(selectedRun.started_at)} · finished {fmt(selectedRun.finished_at)}</div>
                    </div>
                    <StatusBadge status={selectedRun.status} />
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <div className="muted">Steps</div>
                    <table className="table">
                      <thead><tr><th>Name</th><th>Status</th><th>Message</th></tr></thead>
                      <tbody>
                        {(selectedRun.steps || []).map(s => (
                          <tr key={s.id}>
                            <td>{s.name}</td>
                            <td><StatusBadge status={s.status} /></td>
                            <td className="muted">{s.message || "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <div className="muted">Metrics</div>
                    <pre>{JSON.stringify(selectedRun.metrics || {}, null, 2)}</pre>
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <div className="muted">Log tail</div>
                    <pre>{logTail || "(no logs)"}</pre>
                  </div>

                  {selectedRun.error && (
                    <div style={{ marginTop: 12 }}>
                      <div className="muted">Error</div>
                      <pre>{selectedRun.error}</pre>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
