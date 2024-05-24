import React, { ErrorInfo, ReactNode } from "react";

import { AuthError } from "../errors";

interface ErrorBoundaryState {
    hasError: boolean;
}

interface ErrorBoundaryProps {
    children: ReactNode;
    setLoggedPlayer: (player: null) => void;
}

export class ConnectionErrorBoundary extends React.Component<
    ErrorBoundaryProps,
    ErrorBoundaryState
> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
    }

    componentDidCatch(error: Error, info: ErrorInfo): void {
        // this.ref.current?.append(error.toString());

        // If the error is an AuthError, call the logOut function
        if (error instanceof AuthError) {
            this.props.setLoggedPlayer(null);
        }
    }

    render(): ReactNode {
        return <>{this.props.children}</>;
    }
}
