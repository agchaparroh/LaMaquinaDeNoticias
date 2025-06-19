import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  return (
    <Container maxWidth="sm">
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        textAlign="center"
        gap={3}
      >
        <Typography variant="h1" color="primary" fontSize="6rem" fontWeight="bold">
          404
        </Typography>
        
        <Typography variant="h4" color="text.primary" gutterBottom>
          Página no encontrada
        </Typography>
        
        <Typography variant="body1" color="text.secondary" maxWidth={400}>
          La página que buscas no existe o ha sido movida. Regresa al dashboard para continuar.
        </Typography>
        
        <Button
          variant="contained"
          size="large"
          onClick={handleGoHome}
          sx={{ mt: 2 }}
        >
          Ir al Dashboard
        </Button>
      </Box>
    </Container>
  );
};
