import { createTheme } from '@mui/material/styles';

// SISTEMA DE DISEÑO CORREGIDO - Consistencia y Performance
const theme = createTheme({
  palette: {
    mode: 'light',
    
    // COLORES BASE OFICIALES - Centralizados
    background: {
      default: '#F5F3F0',    // --background-main
      paper: '#FFFFFF'       // --background-card
    },
    
    text: {
      primary: '#0F0F0F',    // --text-primary
      secondary: '#6B7280',  // Gris consistente
      disabled: '#9CA3AF'    // Gris disabled
    },
    
    // COLORES DESTACADOS OFICIALES
    primary: {
      main: '#005A99',       // --accent-blue
      light: '#1976D2',      
      dark: '#003D6B',       
      contrastText: '#FFFFFF'
    },
    
    secondary: {
      main: '#D3264C',       // --accent-red
      light: '#E94560',      
      dark: '#A91E41',       
      contrastText: '#FFFFFF'
    },
    
    warning: {
      main: '#FFAD05',       // --accent-yellow
      light: '#FFC947',
      dark: '#D97706'
    },
    
    success: {
      main: '#059669',       
      light: '#10B981',
      dark: '#047857'
    },
    
    error: {
      main: '#D3264C',       // Usa secondary para consistencia
      light: '#E94560', 
      dark: '#A91E41'
    },
    
    info: {
      main: '#005A99',       // Usa primary para consistencia
      light: '#1976D2',
      dark: '#003D6B'
    },
    
    // SISTEMA UNIFICADO DE BORDES Y DIVISORES
    divider: '#E5E7EB'
  },
  
  // TIPOGRAFÍA OPTIMIZADA - Jerarquía correcta mantenida
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Inter"',
      '"Segoe UI"',
      'Roboto',
      'Arial',
      'sans-serif'
    ].join(','),
    
    // Dashboard title
    h3: {
      fontWeight: 700,
      fontSize: '1.75rem',
      lineHeight: 1.2,
      letterSpacing: '-0.025em',
      color: '#0F0F0F'
    },
    
    // HECHO - Contenido principal (MÁS IMPORTANTE)
    h4: {
      fontWeight: 700,
      fontSize: '1.5rem',
      lineHeight: 1.3,
      letterSpacing: '-0.02em',
      color: '#0F0F0F'
    },
    
    // Titular del artículo (contexto)
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
      letterSpacing: '-0.015em',
      color: '#0F0F0F'
    },
    
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
      lineHeight: 1.4,
      color: '#0F0F0F'
    },
    
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      fontWeight: 400,
      color: '#0F0F0F'
    },
    
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      fontWeight: 500,
      color: '#6B7280'
    },
    
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      fontWeight: 500,
      letterSpacing: '0.025em',
      color: '#6B7280'
    }
  },
  
  // SPACING SYSTEM UNIFICADO (8px base)
  spacing: 8,
  
  // BORDES CONSISTENTES
  shape: {
    borderRadius: 8
  },
  
  // COMPONENTES CON MICROINTERACCIONES MODERADAS
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          fontSize: '0.875rem',
          transition: 'all 0.2s ease-in-out',
          letterSpacing: '0.025em'
        },
        contained: {
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.15)'
          }
        }
      }
    },
    
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid #E5E7EB',
          background: '#FFFFFF',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: '#005A99',
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 12px rgba(0, 90, 153, 0.15)'
          }
        }
      }
    },
    
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500,
          fontSize: '0.75rem',
          transition: 'all 0.15s ease-in-out'
        },
        outlined: {
          borderColor: '#E5E7EB',
          borderWidth: '1px'
        }
      }
    },
    
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#FFFFFF',
          borderColor: '#E5E7EB'
        }
      }
    },
    
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#E5E7EB'
        }
      }
    },
    
    MuiSlider: {
      styleOverrides: {
        root: {
          height: 6,
          '& .MuiSlider-thumb': {
            height: 20,
            width: 20,
            backgroundColor: '#005A99',
            border: '3px solid #FFFFFF',
            boxShadow: '0 2px 8px rgba(0, 90, 153, 0.3)',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: '0 0 0 8px rgba(0, 90, 153, 0.16)'
            }
          },
          '& .MuiSlider-track': {
            backgroundColor: '#005A99',
            border: 'none',
            height: 6
          },
          '& .MuiSlider-rail': {
            backgroundColor: '#E5E7EB',
            height: 6
          }
        }
      }
    }
  }
});

export default theme;
export { theme };
