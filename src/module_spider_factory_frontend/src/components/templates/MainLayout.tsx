import { ReactNode } from 'react'
import { 
  AppBar, 
  Box, 
  Container, 
  Drawer, 
  IconButton, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Toolbar, 
  Typography,
  useTheme,
  useMediaQuery
} from '@mui/material'
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Build as BuildIcon,
  CloudUpload as CloudUploadIcon,
  Pattern as PatternIcon
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { AppNavigation } from '../navigation/AppNavigation'

interface MainLayoutProps {
  children: ReactNode
}

const menuItems = [
  { text: 'Inicio', icon: <HomeIcon />, path: '/' },
  { text: 'Wizard', icon: <BuildIcon />, path: '/wizard' },
  { text: 'Carga Masiva', icon: <CloudUploadIcon />, path: '/bulk' },
  { text: 'Patrones', icon: <PatternIcon />, path: '/patterns' }
]

function MainLayout({ children }: MainLayoutProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const handleNavigation = (path: string) => {
    navigate(path)
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  const drawer = (
    <Box sx={{ width: 250 }}>
      {/* Espaciado para AppNavigation + AppBar local */}
      <Box sx={{ height: 64 + 48 }} /> 
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Barra de navegación global */}
      <AppNavigation currentApp="spider-factory" />
      
      {/* AppBar local para Spider Factory */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - 250px)` },
          ml: { md: `250px` },
          top: 64, // Posiciona debajo de AppNavigation
          zIndex: (theme) => theme.zIndex.drawer - 1,
          backgroundColor: 'secondary.main'
        }}
      >
        <Toolbar variant="dense">
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" noWrap component="div" sx={{ fontSize: '1rem' }}>
            🕷️ {menuItems.find(item => item.path === location.pathname)?.text || 'Spider Factory'}
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { md: 250 }, flexShrink: { md: 0 } }}
      >
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            ModalProps={{
              keepMounted: true,
            }}
            sx={{
              '& .MuiDrawer-paper': { 
                boxSizing: 'border-box', 
                width: 250 
              },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              '& .MuiDrawer-paper': { 
                boxSizing: 'border-box', 
                width: 250 
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - 250px)` },
          mt: { xs: 7, md: 14 } // Espacio para AppNavigation + AppBar local
        }}
      >
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  )
}

export default MainLayout