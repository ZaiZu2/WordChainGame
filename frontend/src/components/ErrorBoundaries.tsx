import React, { createRef, ErrorInfo, ReactNode } from "react";

interface ErrorBoundaryState {
    hasError: boolean;
}

interface ErrorBoundaryProps {
    children: ReactNode;
}

export class ConnectionErrorBoundary extends React.Component<
    ErrorBoundaryProps,
    ErrorBoundaryState
> {
    ref: React.RefObject<HTMLDivElement>;

    constructor(props: ErrorBoundaryProps) {
        super(props);
        // this.state = { hasError: false };
        this.ref = createRef<HTMLDivElement>();
    }

    static getDerivedStateFromError(_: Error): ErrorBoundaryState {
        // Update state so the next render will show the fallback UI.
        return { hasError: true };
    }

    componentDidCatch(error: Error, info: ErrorInfo): void {
        this.ref.current?.append(error.toString());
    }

    render(): ReactNode {
        return (
            <>
                {this.props.children}
                <div className="error" ref={this.ref}></div>
            </>
        );
    }
}
