import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="space-y-3 p-6">
            <h2 className="text-sm font-semibold text-red-900">Something went wrong</h2>
            <p className="text-sm text-red-800">{this.state.error.message}</p>
            <Button variant="secondary" onClick={() => this.setState({ error: null })}>Try again</Button>
          </CardContent>
        </Card>
      );
    }
    return this.props.children;
  }
}
