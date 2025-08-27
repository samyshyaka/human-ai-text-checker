import React, { useState } from 'react';
import { apiService } from '../services/api';

function ConnectionTest() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const testHealth = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.checkHealth();
      setHealthStatus(result);
    } catch (error) {
      setHealthStatus({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const testSimple = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.testSimple();
      setTestResult(result);
    } catch (error) {
      setTestResult({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="connection-test" style={{ padding: '1rem', margin: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Backend Connection Test</h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <button onClick={testHealth} disabled={isLoading} style={{ marginRight: '1rem' }}>
          Test Health Endpoint
        </button>
        <button onClick={testSimple} disabled={isLoading}>
          Test Simple Endpoint
        </button>
      </div>

      {healthStatus && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          <h4>Health Status:</h4>
          <pre>{JSON.stringify(healthStatus, null, 2)}</pre>
        </div>
      )}

      {testResult && (
        <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          <h4>Simple Test Result:</h4>
          <pre>{JSON.stringify(testResult, null, 2)}</pre>
        </div>
      )}

      {isLoading && <div>Loading...</div>}
    </div>
  );
}

export default ConnectionTest;

