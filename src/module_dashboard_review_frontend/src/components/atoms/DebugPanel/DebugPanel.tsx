// Debug Panel component for development
// Panel de debugging para desarrollo

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Collapse,
  Chip,
  Stack,
  Divider,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  BugReportRounded,
  ExpandMoreRounded,
  ExpandLessRounded,
  RefreshRounded,
  MemoryRounded,
  NetworkCheckRounded,
  ApiRounded,
  SpeedRounded,
  VisibilityRounded
} from '@mui/icons-material';
import { env } from '@/utils/env';
import { useDebugNetwork, useDebugMemory } from '@/utils/debug';

export interface DebugPanelProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  defaultOpen?: boolean;
}

/**
 * Debug Panel for development environment
 * Only renders in development mode
 */
export const DebugPanel: React.FC<DebugPanelProps> = ({
  position = 'top-right',
  defaultOpen = false
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [activeTab, setActiveTab] = useState(0);
  const [showDetails, setShowDetails] = useState(false);
  const [debugData, setDebugData] = useState<any>({});

  const networkInfo = useDebugNetwork();
  const memoryInfo = useDebugMemory('DebugPanel', 5000);

  // Don't render in production
  if (!env.isDevelopment()) {
    return null;
  }

  // Get position styles
  const getPositionStyles = () => {
    const base = {
      position: 'fixed' as const,
      zIndex: 9999,
      maxWidth: '400px',
      minWidth: '300px'
    };

    switch (position) {
      case 'top-left':
        return { ...base, top: 16, left: 16 };
      case 'top-right':
        return { ...base, top: 16, right: 16 };
      case 'bottom-left':
        return { ...base, bottom: 16, left: 16 };
      case 'bottom-right':
        return { ...base, bottom: 16, right: 16 };
      default:
        return { ...base, top: 16, right: 16 };
    }
  };

  // Refresh debug data from window
  const refreshDebugData = () => {
    if (typeof window !== 'undefined' && (window as any).__DEBUG__) {
      setDebugData({ ...(window as any).__DEBUG__ });
    }
  };

  useEffect(() => {
    refreshDebugData();
    const interval = setInterval(refreshDebugData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Paper
      elevation={8}
      sx={{
        ...getPositionStyles(),
        bgcolor: 'background.paper',
        border: '2px solid',
        borderColor: isOpen ? 'primary.main' : 'divider',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          cursor: 'pointer'
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BugReportRounded fontSize="small" />
          <Typography variant="caption" fontWeight="bold">
            Debug Panel
          </Typography>
          <Chip
            label="DEV"
            size="small"
            sx={{ 
              bgcolor: 'warning.main', 
              color: 'warning.contrastText',
              height: 20,
              fontSize: '0.7rem'
            }}
          />
        </Box>
        <IconButton size="small" sx={{ color: 'inherit' }}>
          {isOpen ? <ExpandLessRounded /> : <ExpandMoreRounded />}
        </IconButton>
      </Box>

      {/* Content */}
      <Collapse in={isOpen}>
        <Box sx={{ maxHeight: '70vh', overflow: 'auto' }}>
          {/* Quick Stats */}
          <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip
                icon={<ApiRounded />}
                label={`Env: ${env.environment}`}
                size="small"
                color="primary"
              />
              <Chip
                icon={<NetworkCheckRounded />}
                label={networkInfo?.online ? 'Online' : 'Offline'}
                size="small"
                color={networkInfo?.online ? 'success' : 'error'}
              />
              {memoryInfo && (
                <Chip
                  icon={<MemoryRounded />}
                  label={`${memoryInfo.used}MB`}
                  size="small"
                  color="info"
                />
              )}
            </Stack>
          </Box>

          {/* Tabs */}
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="System" />
            <Tab label="API Calls" />
            <Tab label="State" />
            <Tab label="Performance" />
          </Tabs>

          {/* Tab Panels */}
          <Box sx={{ p: 2 }}>
            {/* System Tab */}
            {activeTab === 0 && (
              <Stack spacing={2}>
                {/* Environment Info */}
                <Card variant="outlined">
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Environment
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="caption">
                        API URL: {env.apiUrl}
                      </Typography>
                      <Typography variant="caption">
                        Debug Mode: {env.debug ? 'ON' : 'OFF'}
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>

                {/* Network Info */}
                {networkInfo && (
                  <Card variant="outlined">
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Network Status
                      </Typography>
                      <Stack spacing={1}>
                        <Typography variant="caption">
                          Status: {networkInfo.online ? '🟢 Online' : '🔴 Offline'}
                        </Typography>
                        {networkInfo.connection && (
                          <>
                            <Typography variant="caption">
                              Type: {networkInfo.connection.effectiveType}
                            </Typography>
                            <Typography variant="caption">
                              Speed: {networkInfo.connection.downlink} Mbps
                            </Typography>
                          </>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                )}

                {/* Memory Info */}
                {memoryInfo && (
                  <Card variant="outlined">
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Memory Usage
                      </Typography>
                      <Stack spacing={1}>
                        <Typography variant="caption">
                          Used: {memoryInfo.used} MB
                        </Typography>
                        <Typography variant="caption">
                          Total: {memoryInfo.total} MB
                        </Typography>
                        <Typography variant="caption">
                          Limit: {memoryInfo.limit} MB
                        </Typography>
                      </Stack>
                    </CardContent>
                  </Card>
                )}
              </Stack>
            )}

            {/* API Calls Tab */}
            {activeTab === 1 && (
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">
                    Recent API Calls
                  </Typography>
                  <IconButton size="small" onClick={refreshDebugData}>
                    <RefreshRounded />
                  </IconButton>
                </Box>
                
                {Object.keys(debugData).filter(key => key.startsWith('apiCalls_')).length > 0 ? (
                  Object.entries(debugData)
                    .filter(([key]) => key.startsWith('apiCalls_'))
                    .map(([key, calls]: [string, any]) => (
                      <Card key={key} variant="outlined">
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Typography variant="caption" fontWeight="bold">
                            {key.replace('apiCalls_', '')}
                          </Typography>
                          {Array.isArray(calls) && calls.slice(0, 3).map((call, index) => (
                            <Box key={index} sx={{ mt: 1 }}>
                              <Typography variant="caption" display="block">
                                {call.method} {call.url}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(call.timestamp).toLocaleTimeString()}
                              </Typography>
                            </Box>
                          ))}
                        </CardContent>
                      </Card>
                    ))
                ) : (
                  <Alert severity="info" sx={{ fontSize: '0.8rem' }}>
                    No API calls tracked yet
                  </Alert>
                )}
              </Stack>
            )}

            {/* State Tab */}
            {activeTab === 2 && (
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">
                    Component State
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={showDetails}
                        onChange={(e) => setShowDetails(e.target.checked)}
                      />
                    }
                    label={<Typography variant="caption">Details</Typography>}
                  />
                </Box>

                {Object.keys(debugData).filter(key => key.startsWith('debug_')).length > 0 ? (
                  Object.entries(debugData)
                    .filter(([key]) => key.startsWith('debug_'))
                    .map(([key, data]: [string, any]) => (
                      <Card key={key} variant="outlined">
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Typography variant="caption" fontWeight="bold">
                            {key.replace('debug_', '')}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Renders: {data?.renderCount || 0}
                          </Typography>
                          {showDetails && data && (
                            <Box sx={{ mt: 1, fontSize: '0.7rem', maxHeight: 100, overflow: 'auto' }}>
                              <pre>{JSON.stringify(data, null, 2)}</pre>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    ))
                ) : (
                  <Alert severity="info" sx={{ fontSize: '0.8rem' }}>
                    No component state tracked yet
                  </Alert>
                )}
              </Stack>
            )}

            {/* Performance Tab */}
            {activeTab === 3 && (
              <Stack spacing={2}>
                <Typography variant="subtitle2">
                  Performance Metrics
                </Typography>
                
                <Card variant="outlined">
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography variant="caption" fontWeight="bold" gutterBottom>
                      Render Performance
                    </Typography>
                    {Object.entries(debugData)
                      .filter(([key]) => key.startsWith('renderCount_'))
                      .map(([key, count]: [string, any]) => (
                        <Typography key={key} variant="caption" display="block">
                          {key.replace('renderCount_', '')}: {count} renders
                        </Typography>
                      ))}
                  </CardContent>
                </Card>

                {memoryInfo && (
                  <Card variant="outlined">
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="caption" fontWeight="bold" gutterBottom>
                        Memory Trend
                      </Typography>
                      <Box sx={{ 
                        height: 40, 
                        bgcolor: 'grey.100', 
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <Typography variant="caption">
                          {((memoryInfo.used / memoryInfo.limit) * 100).toFixed(1)}% used
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                )}
              </Stack>
            )}
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default DebugPanel;
