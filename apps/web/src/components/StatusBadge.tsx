import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  let label = status;
  let bg = "#eee";
  if (s === "success") bg = "#d1fae5";
  if (s === "failed") bg = "#fee2e2";
  if (s === "running") bg = "#dbeafe";
  if (s === "queued") bg = "#fef3c7";
  return <span className="badge" style={{ background: bg }}>{label}</span>;
}
