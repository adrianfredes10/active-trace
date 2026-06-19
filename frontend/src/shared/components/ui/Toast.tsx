let container: HTMLDivElement | null = null;

function ensureContainer(): HTMLDivElement {
  if (container && document.body.contains(container)) return container;
  container = document.createElement("div");
  container.className = "fixed bottom-4 right-4 z-[100] flex flex-col gap-2";
  document.body.appendChild(container);
  return container;
}

export function showToast(message: string, type: "success" | "error" = "success"): void {
  const root = ensureContainer();
  const el = document.createElement("div");
  el.className =
    type === "success"
      ? "rounded-lg border border-status-success/30 bg-status-success-soft px-4 py-2 text-sm text-status-success shadow"
      : "rounded-lg border border-status-danger/30 bg-status-danger-soft px-4 py-2 text-sm text-status-danger shadow";
  el.textContent = message;
  root.appendChild(el);
  window.setTimeout(() => el.remove(), 4000);
}
