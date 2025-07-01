import { createTheme } from '@mui/material';
import { esES } from '@mui/material/locale';

// Tema personalizado para hacer la interfaz más amigable
const customTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff'
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
      contrastText: '#ffffff'
    },
    success: {
      main: '#2e7d32',
      light: '#4caf50',
      dark: '#1b5e20'
    },
    warning: {
      main: '#ed6c02',
      light: '#ff9800',
      dark: '#e65100'
    },
    error: {
      main: '#d32f2f',
      light: '#ef5350',
      dark: '#c62828'
    },
    info: {
      main: '#0288d1',
      light: '#03a9f4',
      dark: '#01579b'
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff'
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)'
    }
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.2
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.25rem'
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43
    },
    button: {
      textTransform: 'none',
      fontWeight: 500
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.33
    }
  },
  shape: {
    borderRadius: 8
  },
  spacing: 8,
  components: {
    // Botones más amigables
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }
        },
        contained: {
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
          }
        },
        // large: {
        //   padding: '12px 24px',
        //   fontSize: '1rem'
        // }
      }
    },
    // TextField más amigable
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#1976d2'
            }
          }
        }
      }
    },
    // Paper con mejor sombra
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
        },
        elevation2: {
          boxShadow: '0 4px 20px rgba(0,0,0,0.12)'
        }
      }
    },
    // Chips más amigables
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500
        },
        outlined: {
          borderWidth: 1.5,
          '&:hover': {
            backgroundColor: 'rgba(25, 118, 210, 0.04)'
          }
        }
      }
    },
    // Alert más visible
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '& .MuiAlert-icon': {
            fontSize: '1.25rem'
          }
        },
        standardInfo: {
          backgroundColor: '#e3f2fd',
          color: '#0d47a1'
        },
        standardSuccess: {
          backgroundColor: '#e8f5e8',
          color: '#2e7d32'
        },
        standardWarning: {
          backgroundColor: '#fff3e0',
          color: '#e65100'
        },
        standardError: {
          backgroundColor: '#ffebee',
          color: '#c62828'
        }
      }
    },
    // Tooltip más legible
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          fontSize: '0.75rem',
          maxWidth: 220,
          padding: '8px 12px',
          borderRadius: 6
        },
        arrow: {
          color: 'rgba(0, 0, 0, 0.9)'
        }
      }
    },
    // Stepper más amigable
    MuiStepLabel: {
      styleOverrides: {
        root: {
          '& .MuiStepLabel-label': {
            fontSize: '0.875rem',
            fontWeight: 500
          },
          '& .MuiStepLabel-label.Mui-active': {
            color: '#1976d2',
            fontWeight: 600
          },
          '& .MuiStepLabel-label.Mui-completed': {
            color: '#2e7d32'
          }
        }
      }
    },
    // LinearProgress más suave
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          backgroundColor: 'rgba(25, 118, 210, 0.12)'
        },
        bar: {
          borderRadius: 4
        }
      }
    },
    // IconButton más accesible
    MuiIconButton: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(25, 118, 210, 0.04)'
          }
        }
      }
    },
    // Fab más prominente
    MuiFab: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          '&:hover': {
            boxShadow: '0 6px 16px rgba(0,0,0,0.2)'
          }
        }
      }
    }
  }
}, esES);

export default customTheme;