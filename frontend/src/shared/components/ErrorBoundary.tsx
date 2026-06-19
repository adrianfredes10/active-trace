import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/shared/components/ui/Button";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-4 text-center">
          <p className="font-display text-2xl font-semibold text-text-primary">
            Algo salió mal
          </p>
          <p className="mt-2 max-w-sm text-sm text-text-secondary">
            Ocurrió un error inesperado. Recargá la página o volvé al inicio.
          </p>
          <div className="mt-6 flex gap-2">
            <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
              Recargar
            </Button>
            <Link
              to="/"
              className="inline-flex h-10 items-center justify-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white no-underline hover:bg-ink-700"
            >
              Ir al inicio
            </Link>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
