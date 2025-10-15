import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorTime: null
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      errorTime: new Date().toISOString()
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console
    console.error('❌ Error caught by ErrorBoundary:', error);
    console.error('📍 Error info:', errorInfo);

    this.setState({
      error,
      errorInfo
    });

    // TODO: Send to error tracking service (e.g., Sentry)
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorTime: null
    });
  };

  render() {
    if (this.state.hasError) {
      const isDevelopment = process.env.NODE_ENV === 'development';
      const darkMode = this.props.darkMode || false;

      const bgColor = darkMode ? 'bg-gray-900' : 'bg-gray-50';
      const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
      const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';
      const secondaryColor = darkMode ? 'text-gray-400' : 'text-gray-600';
      const borderColor = darkMode ? 'border-gray-700' : 'border-gray-300';

      return (
        <div className={`min-h-screen ${bgColor} flex items-center justify-center p-4`}>
          <div className={`max-w-2xl w-full ${cardBg} rounded-sm shadow-xl border-2 ${borderColor} p-8`}>
            {/* Header */}
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h1 className={`text-3xl font-bold ${textColor} mb-2`}>
                문제가 발생했습니다
              </h1>
              <p className={`${secondaryColor}`}>
                예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 다시 시도해주세요.
              </p>
            </div>

            {/* Error Details (Development Only) */}
            {isDevelopment && this.state.error && (
              <div className="mb-6">
                <details className={`${darkMode ? 'bg-gray-900' : 'bg-gray-100'} p-4 rounded-sm`}>
                  <summary className={`font-semibold ${textColor} cursor-pointer mb-2`}>
                    🔍 개발자 정보 (클릭하여 펼치기)
                  </summary>

                  <div className={`text-sm ${secondaryColor} space-y-2 mt-2`}>
                    <div>
                      <strong>발생 시간:</strong> {this.state.errorTime}
                    </div>
                    <div>
                      <strong>에러 메시지:</strong>
                      <pre className="mt-1 p-2 bg-red-100 text-red-800 rounded overflow-x-auto">
                        {this.state.error.toString()}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div>
                        <strong>스택 트레이스:</strong>
                        <pre className="mt-1 p-2 bg-red-100 text-red-800 rounded overflow-x-auto text-xs">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={this.handleReset}
                className="px-6 py-3 bg-blue-600 text-white rounded-sm font-semibold hover:bg-blue-700 transition-colors"
              >
                🔄 다시 시도
              </button>
              <button
                onClick={() => window.location.reload()}
                className={`px-6 py-3 ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'}
                  ${textColor} rounded-sm font-semibold transition-colors`}
              >
                🏠 페이지 새로고침
              </button>
            </div>

            {/* Support Info */}
            <div className={`mt-6 text-center text-sm ${secondaryColor}`}>
              <p>문제가 계속되면 브라우저 콘솔(F12)을 확인하거나 관리자에게 문의하세요.</p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
