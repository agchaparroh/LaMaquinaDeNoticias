// Según SECCIÓN 9.4 - Service Worker registration y management utilities
// Utilidades para registrar y gestionar el service worker

export interface ServiceWorkerStatus {
  isSupported: boolean;
  isRegistered: boolean;
  isActive: boolean;
  isWaiting: boolean;
  registration?: ServiceWorkerRegistration;
}

export interface CacheStatus {
  caches: Record<string, { size: number; urls: string[] }>;
  totalCaches: number;
  isOnline: boolean;
}

// Función para registrar el service worker
export async function registerServiceWorker(): Promise<ServiceWorkerStatus> {
  const status: ServiceWorkerStatus = {
    isSupported: 'serviceWorker' in navigator,
    isRegistered: false,
    isActive: false,
    isWaiting: false
  };

  if (!status.isSupported) {
    console.log('Service Worker no es compatible con este navegador');
    return status;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    });

    status.isRegistered = true;
    status.registration = registration;

    console.log('Service Worker registrado exitosamente:', registration.scope);

    // Verificar estado del service worker
    if (registration.active) {
      status.isActive = true;
      console.log('Service Worker está activo');
    }

    if (registration.waiting) {
      status.isWaiting = true;
      console.log('Service Worker esperando activación');
    }

    // Escuchar actualizaciones
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      
      if (newWorker) {
        console.log('Nueva versión del Service Worker encontrada');
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // Nueva versión disponible
            notifyUpdateAvailable();
          }
        });
      }
    });

    // Escuchar mensajes del service worker
    navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage);

    return status;

  } catch (error) {
    console.error('Error al registrar Service Worker:', error);
    return status;
  }
}

// Función para desregistrar el service worker
export async function unregisterServiceWorker(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    
    if (registration) {
      const unregistered = await registration.unregister();
      console.log('Service Worker desregistrado:', unregistered);
      return unregistered;
    }
    
    return false;
  } catch (error) {
    console.error('Error al desregistrar Service Worker:', error);
    return false;
  }
}

// Función para actualizar el service worker
export async function updateServiceWorker(): Promise<void> {
  if (!('serviceWorker' in navigator)) {
    return;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    
    if (registration) {
      await registration.update();
      console.log('Service Worker actualizado');
    }
  } catch (error) {
    console.error('Error al actualizar Service Worker:', error);
  }
}

// Función para activar un service worker en espera
export async function skipWaiting(): Promise<void> {
  if (!('serviceWorker' in navigator)) {
    return;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    
    if (registration?.waiting) {
      // Enviar mensaje para saltar la espera
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      
      // Recargar la página después de que se active
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
      });
    }
  } catch (error) {
    console.error('Error al activar Service Worker:', error);
  }
}

// Función para limpiar todos los caches
export async function clearServiceWorkerCache(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    
    if (registration?.active) {
      return new Promise((resolve) => {
        const messageChannel = new MessageChannel();
        
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.success);
        };
        
        registration.active.postMessage(
          { type: 'CLEAR_CACHE' },
          [messageChannel.port2]
        );
      });
    }
    
    return false;
  } catch (error) {
    console.error('Error al limpiar cache del Service Worker:', error);
    return false;
  }
}

// Función para obtener el estado del cache
export async function getCacheStatus(): Promise<CacheStatus | null> {
  if (!('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    
    if (registration?.active) {
      return new Promise((resolve) => {
        const messageChannel = new MessageChannel();
        
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data);
        };
        
        registration.active.postMessage(
          { type: 'GET_CACHE_STATUS' },
          [messageChannel.port2]
        );
      });
    }
    
    return null;
  } catch (error) {
    console.error('Error al obtener estado del cache:', error);
    return null;
  }
}

// Función para verificar si la app está funcionando offline
export function isOffline(): boolean {
  return !navigator.onLine;
}

// Función para verificar si hay conexión de red
export function isOnline(): boolean {
  return navigator.onLine;
}

// Hook para escuchar cambios de conexión
export function addNetworkListeners(
  onOnline: () => void,
  onOffline: () => void
): () => void {
  
  const handleOnline = () => {
    console.log('Conexión a Internet restaurada');
    onOnline();
  };
  
  const handleOffline = () => {
    console.log('Conexión a Internet perdida');
    onOffline();
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  // Función de cleanup
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}

// Manejador de mensajes del service worker
function handleServiceWorkerMessage(event: MessageEvent) {
  const { type, message } = event.data;
  
  switch (type) {
    case 'UPDATE_AVAILABLE':
      notifyUpdateAvailable();
      break;
      
    case 'CACHE_UPDATED':
      console.log('Cache actualizado por Service Worker');
      break;
      
    default:
      console.log('Mensaje del Service Worker:', event.data);
  }
}

// Función para notificar sobre actualizaciones disponibles
function notifyUpdateAvailable() {
  // Aquí se podría mostrar una notificación o banner
  // En un contexto real, esto se integraría con el sistema de notificaciones
  console.log('Nueva versión disponible. Recarga la página para aplicar.');
  
  // Ejemplo de integración con el sistema de notificaciones
  if (window.dispatchEvent) {
    window.dispatchEvent(new CustomEvent('sw-update-available', {
      detail: { message: 'Nueva versión disponible. Recarga la página para aplicar.' }
    }));
  }
}

// Función para pre-cachear recursos críticos
export async function precacheResources(urls: string[]): Promise<void> {
  if (!('caches' in window)) {
    return;
  }

  try {
    const cache = await caches.open('manual-precache');
    await cache.addAll(urls);
    console.log('Recursos pre-cacheados:', urls);
  } catch (error) {
    console.error('Error al pre-cachear recursos:', error);
  }
}

// Función para verificar si un recurso está en cache
export async function isResourceCached(url: string): Promise<boolean> {
  if (!('caches' in window)) {
    return false;
  }

  try {
    const response = await caches.match(url);
    return !!response;
  } catch (error) {
    console.error('Error al verificar cache:', error);
    return false;
  }
}

// Configuración por defecto para el service worker
export const SERVICE_WORKER_CONFIG = {
  enabled: process.env.NODE_ENV === 'production',
  scope: '/',
  updateViaCache: 'none' as ServiceWorkerUpdateViaCache,
  skipWaitingOnFirstInstall: true
} as const;

// Función para inicializar completamente el service worker
export async function initializeServiceWorker(): Promise<ServiceWorkerStatus> {
  if (!SERVICE_WORKER_CONFIG.enabled) {
    console.log('Service Worker deshabilitado en desarrollo');
    return {
      isSupported: false,
      isRegistered: false,
      isActive: false,
      isWaiting: false
    };
  }

  const status = await registerServiceWorker();
  
  if (status.isRegistered) {
    // Configurar listeners de red
    addNetworkListeners(
      () => {
        console.log('App online - Service Worker activo');
      },
      () => {
        console.log('App offline - Service Worker manejando requests');
      }
    );
    
    // Pre-cachear recursos críticos en producción
    await precacheResources([
      '/static/js/bundle.js',
      '/static/css/main.css',
      '/manifest.json'
    ]);
  }
  
  return status;
}

export default {
  register: registerServiceWorker,
  unregister: unregisterServiceWorker,
  update: updateServiceWorker,
  skipWaiting,
  clearCache: clearServiceWorkerCache,
  getCacheStatus,
  isOffline,
  isOnline,
  addNetworkListeners,
  precacheResources,
  isResourceCached,
  initialize: initializeServiceWorker
};