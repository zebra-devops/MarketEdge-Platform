'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle, ExternalLink } from 'lucide-react';

interface EnvironmentInfo {
  status: string;
  environment: {
    environment: string;
    use_staging_auth0: boolean;
    node_env: string;
    render_service_type: string;
    render_service_name: string;
    render_git_branch: string;
    render_git_commit: string;
  };
  auth0: {
    domain: string;
    client_id: string;
    audience: string;
  };
  database: {
    connected: boolean;
    error?: string;
  };
  redis: {
    connected: boolean;
    error?: string;
  };
  health: {
    timestamp: string;
    uptime_seconds: number;
    memory_usage_mb: number;
    cpu_usage_percent: number;
  };
  preview_validation: {
    is_preview: boolean;
    branch_name: string;
    staging_auth0: boolean;
    environment_type: string;
  };
}

interface HealthCheck {
  status: string;
  timestamp: string;
  checks: {
    [key: string]: {
      status: string;
      message: string;
    };
  };
  environment: string;
  preview_environment: boolean;
}

export default function DebugPage() {
  const [environmentInfo, setEnvironmentInfo] = useState<EnvironmentInfo | null>(null);
  const [healthCheck, setHealthCheck] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const getApiBaseUrl = () => {
    if (typeof window === 'undefined') return '';

    // Check for environment-specific API URLs
    const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envApiUrl) return envApiUrl;

    // Default fallback based on current hostname
    const hostname = window.location.hostname;
    if (hostname.includes('vercel.app') || hostname.includes('render.com')) {
      // Preview environment - construct API URL
      return `https://${hostname.replace('-frontend', '-backend')}/api/v1`;
    }

    // Local development
    return 'http://localhost:8000/api/v1';
  };

  const fetchEnvironmentInfo = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = getApiBaseUrl();
      console.log('Fetching from API URL:', apiUrl);

      // Fetch environment info
      const envResponse = await fetch(`${apiUrl}/debug/environment`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!envResponse.ok) {
        throw new Error(`Environment API failed: ${envResponse.status} ${envResponse.statusText}`);
      }

      const envData = await envResponse.json();
      setEnvironmentInfo(envData);

      // Fetch detailed health check
      const healthResponse = await fetch(`${apiUrl}/debug/health-detailed`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!healthResponse.ok) {
        console.warn('Health API failed, but continuing with environment data');
      } else {
        const healthData = await healthResponse.json();
        setHealthCheck(healthData);
      }

      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error('Debug API error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const testCors = async () => {
    try {
      const apiUrl = getApiBaseUrl();
      const response = await fetch(`${apiUrl}/debug/cors-test`);

      if (response.ok) {
        const data = await response.json();
        alert(`CORS Test Successful!\n\nMessage: ${data.message}\nEnvironment: ${data.environment}\nPreview: ${data.preview}`);
      } else {
        alert(`CORS Test Failed: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      alert(`CORS Test Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  useEffect(() => {
    fetchEnvironmentInfo();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-red-100 text-red-800';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Preview Environment Debug</h1>
          <p className="text-gray-600 mt-2">
            Validate preview environment configuration and connectivity
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={fetchEnvironmentInfo}
            disabled={loading}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={testCors} variant="outline">
            <ExternalLink className="h-4 w-4 mr-2" />
            Test CORS
          </Button>
        </div>
      </div>

      {lastUpdated && (
        <Alert>
          <AlertDescription>
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Error:</strong> {error}
          </AlertDescription>
        </Alert>
      )}

      {environmentInfo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Preview Environment Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Preview Environment Status
                <Badge className={getStatusBadgeColor(environmentInfo.status)}>
                  {environmentInfo.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="font-medium">Environment Type:</span>
                <span>{environmentInfo.preview_validation.environment_type}</span>

                <span className="font-medium">Is Preview:</span>
                <span className={environmentInfo.preview_validation.is_preview ? 'text-green-600' : 'text-red-600'}>
                  {environmentInfo.preview_validation.is_preview ? 'Yes' : 'No'}
                </span>

                <span className="font-medium">Branch:</span>
                <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                  {environmentInfo.preview_validation.branch_name}
                </span>

                <span className="font-medium">Staging Auth0:</span>
                <span className={environmentInfo.preview_validation.staging_auth0 ? 'text-green-600' : 'text-red-600'}>
                  {environmentInfo.preview_validation.staging_auth0 ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Environment Variables */}
          <Card>
            <CardHeader>
              <CardTitle>Environment Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="font-medium">Environment:</span>
                <span>{environmentInfo.environment.environment}</span>

                <span className="font-medium">Node ENV:</span>
                <span>{environmentInfo.environment.node_env}</span>

                <span className="font-medium">Render Service:</span>
                <span>{environmentInfo.environment.render_service_type}</span>

                <span className="font-medium">Service Name:</span>
                <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                  {environmentInfo.environment.render_service_name}
                </span>

                <span className="font-medium">Git Commit:</span>
                <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                  {environmentInfo.environment.render_git_commit}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Auth0 Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Auth0 Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="font-medium">Domain:</span>
                <span className="font-mono text-xs">{environmentInfo.auth0.domain}</span>

                <span className="font-medium">Client ID:</span>
                <span className="font-mono text-xs">{environmentInfo.auth0.client_id}</span>

                <span className="font-medium">Audience:</span>
                <span className="font-mono text-xs">{environmentInfo.auth0.audience}</span>
              </div>
            </CardContent>
          </Card>

          {/* Database & Redis Status */}
          <Card>
            <CardHeader>
              <CardTitle>Service Connectivity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Database:</span>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(environmentInfo.database.connected ? 'healthy' : 'unhealthy')}
                    <span className="text-sm">
                      {environmentInfo.database.connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>
                {environmentInfo.database.error && (
                  <p className="text-xs text-red-600 ml-4">{environmentInfo.database.error}</p>
                )}

                <div className="flex items-center justify-between">
                  <span className="font-medium">Redis:</span>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(environmentInfo.redis.connected ? 'healthy' : 'unhealthy')}
                    <span className="text-sm">
                      {environmentInfo.redis.connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>
                {environmentInfo.redis.error && (
                  <p className="text-xs text-red-600 ml-4">{environmentInfo.redis.error}</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Health Checks */}
      {healthCheck && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Detailed Health Checks
              <Badge className={getStatusBadgeColor(healthCheck.status)}>
                {healthCheck.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(healthCheck.checks).map(([service, check]) => (
                <div key={service} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <div className="font-medium capitalize">{service}</div>
                    <div className="text-xs text-gray-600">{check.message}</div>
                  </div>
                  {getStatusIcon(check.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Information */}
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium">Current API URL:</span>
              <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                {getApiBaseUrl()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Frontend URL:</span>
              <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                {typeof window !== 'undefined' ? window.location.origin : 'N/A'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}