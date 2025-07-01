import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  useTheme,
  useMediaQuery,
  IconButton,
  Menu,
  MenuItem,
  Chip
} from '@mui/material';
import {
  Article as ArticleIcon,
  BugReport as SpiderIcon,
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  MenuOpen as MenuIcon
} from '@mui/icons-material';

interface AppNavigationProps {
  /** Nombre de la aplicación actual para resaltar */
  currentApp?: 'dashboard' | 'spider-factory';
}

/**
 * Barra de navegación compartida entre todas las interfaces de La Máquina de Noticias
 * Permite navegar fácilmente entre herramientas sin memorizar URLs
 */
export const AppNavigation: React.FC<AppNavigationProps> = ({ currentApp }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileMenuAnchor, setMobileMenuAnchor] = React.useState<null | HTMLElement>(null);

  const navigationItems = [
    {
      key: 'dashboard',
      label: 'Dashboard Editorial',
      icon: <ArticleIcon />,
      href: '/',
      description: 'Revisar hechos noticiosos',
      target: '_self'
    },
    {
      key: 'spider-factory',
      label: 'Spider Factory',
      icon: <SpiderIcon />,
      href: '/spider-factory/',
      description: 'Gestionar spiders',
      target: '_self'
    },
    {
      key: 'scrapydweb',
      label: 'ScrapydWeb',
      icon: <DashboardIcon />,
      href: 'http://localhost:5000',
      description: 'Monitorear spiders',
      target: '_blank'
    },
    {
      key: 'pipeline-api',
      label: 'Pipeline API',
      icon: <SettingsIcon />,
      href: 'http://localhost:8003/docs',
      description: 'Documentación API',
      target: '_blank'
    }
  ];

  const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMobileMenuAnchor(event.currentTarget);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuAnchor(null);
  };

  const handleNavigation = (href: string, target: string) => {
    if (target === '_blank') {
      window.open(href, '_blank', 'noopener,noreferrer');
    } else {
      window.location.href = href;
    }
    handleMobileMenuClose();
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: theme.zIndex.drawer + 1,
        backgroundColor: theme.palette.primary.main,
        boxShadow: theme.shadows[2]
      }}
    >
      <Toolbar>
        {/* Logo y título */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 600,
              fontSize: { xs: '1rem', md: '1.25rem' }
            }}
          >
            🗞️ La Máquina de Noticias
          </Typography>
          
          {/* Indicador de aplicación actual */}
          {currentApp && (
            <Chip
              label={
                currentApp === 'dashboard' 
                  ? 'Editorial' 
                  : 'Spider Factory'
              }
              size="small"
              color="secondary"
              sx={{ 
                ml: 2,
                display: { xs: 'none', sm: 'flex' }
              }}
            />
          )}
        </Box>

        {/* Navegación desktop */}
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            {navigationItems.map((item) => (
              <Button
                key={item.key}
                color="inherit"
                onClick={() => handleNavigation(item.href, item.target)}
                startIcon={item.icon}
                variant={currentApp === item.key ? 'outlined' : 'text'}
                sx={{
                  minWidth: 'auto',
                  px: 2,
                  py: 1,
                  fontSize: '0.875rem',
                  fontWeight: currentApp === item.key ? 600 : 400,
                  backgroundColor: currentApp === item.key 
                    ? 'rgba(255,255,255,0.1)' 
                    : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.15)'
                  }
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        )}

        {/* Navegación mobile */}
        {isMobile && (
          <>
            <IconButton
              color="inherit"
              onClick={handleMobileMenuOpen}
              sx={{ ml: 1 }}
            >
              <MenuIcon />
            </IconButton>
            
            <Menu
              anchorEl={mobileMenuAnchor}
              open={Boolean(mobileMenuAnchor)}
              onClose={handleMobileMenuClose}
              PaperProps={{
                sx: {
                  mt: 1,
                  minWidth: 200
                }
              }}
            >
              {navigationItems.map((item) => (
                <MenuItem
                  key={item.key}
                  onClick={() => handleNavigation(item.href, item.target)}
                  selected={currentApp === item.key}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Box sx={{ mr: 2, display: 'flex' }}>
                      {item.icon}
                    </Box>
                    <Box>
                      <Typography variant="body1">
                        {item.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.description}
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Menu>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default AppNavigation;