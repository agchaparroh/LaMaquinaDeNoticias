import { createContext, useContext, useState } from 'react';
import { Snackbar, Alert } from '@mui/material';

// Según SECCIÓN 4.1 - Implementar Context para notificaciones EXACTO
interface Notification {
  id: string;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

interface NotificationContextType {
  showNotification: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void;
}

const NotificationContext = createContext<NotificationContextType>({
  showNotification: () => {}
});

export const NotificationProvider = ({ children }: { children: React.ReactNode }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    const id = Date.now().toString();
    const notification = { id, message, severity };
    setNotifications(prev => [...prev, notification]);
    
    // Auto-remove after 6 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 6000);
  };
  
  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      {notifications.map((notification) => (
        <Snackbar
          key={notification.id}
          open={true}
          onClose={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <Alert 
            onClose={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))} 
            severity={notification.severity}
            variant="filled"
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </NotificationContext.Provider>
  );
};

// Según SECCIÓN 4.2 - Hook useNotification EXACTO
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};