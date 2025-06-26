// Debug utilities for development
// Utilidades de debug para desarrollo

import { useState, useEffect } from 'react';

// Tipo para la API de Network Information (experimental)
interface NetworkInformation {
  effectiveType?: '2g' | '3g' | '4g' | 'slow-2g';
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
  type?: 'bluetooth' | 'cellular' | 'ethernet' | 'none' | 'wifi' | 'wimax' | 'other' | 'unknown';
}

declare global {
  interface Navigator {
    connection?: NetworkInformation;
    mozConnection?: NetworkInformation;
    webkitConnection?: NetworkInformation;
  }
}

/**
 * Hook para monitorear el estado de la red
 * @returns Estado actual de las peticiones de red
 */
export const useDebugNetwork = () => {
  const [requests, setRequests] = useState<any[]>([]);
  const [online, setOnline] = useState(navigator.onLine);
  const [connection, setConnection] = useState<NetworkInformation | null>(null);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Detectar Network Information API si está disponible
    const nav = navigator as any;
    const networkConnection = nav.connection || nav.mozConnection || nav.webkitConnection;
    
    if (networkConnection) {
      // Establecer conexión inicial
      setConnection({
        effectiveType: networkConnection.effectiveType,
        downlink: networkConnection.downlink,
        rtt: networkConnection.rtt,
        saveData: networkConnection.saveData,
        type: networkConnection.type
      });

      // Escuchar cambios en la conexión
      const handleConnectionChange = () => {
        setConnection({
          effectiveType: networkConnection.effectiveType,
          downlink: networkConnection.downlink,
          rtt: networkConnection.rtt,
          saveData: networkConnection.saveData,
          type: networkConnection.type
        });
      };

      networkConnection.addEventListener('change', handleConnectionChange);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        networkConnection.removeEventListener('change', handleConnectionChange);
      };
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    requests,
    pendingRequests: 0,
    failedRequests: 0,
    successfulRequests: 0,
    online,
    connection
  };
};


/**
 * Función helper para logging condicional en desarrollo
 */
export const debugLog = (message: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[DEBUG] ${message}`, data);
  }
};

/**
 * Función para medir el rendimiento de operaciones
 */
export const measurePerformance = (label: string, callback: () => void) => {
  if (import.meta.env.DEV) {
    const start = performance.now();
    callback();
    const end = performance.now();
    console.log(`[PERFORMANCE] ${label}: ${(end - start).toFixed(2)}ms`);
  } else {
    callback();
  }
};