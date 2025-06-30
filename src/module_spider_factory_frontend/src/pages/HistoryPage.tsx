import React from 'react';
import { Container, Typography, CircularProgress, Alert, IconButton } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Download as DownloadIcon, Code as CodeIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { GeneratedSpider } from '../types';

// Según SECCIÓN 6.1 - Página de historial de spiders generados
const HistoryPage = () => {
  // Obtener historial del backend con React Query
  const { data: spiderHistory, isLoading, error } = useQuery({
    queryKey: ['spider-history'],
    queryFn: async () => {
      try {
        // Primero intentar obtener del backend
        return await spiderFactoryService.getHistory();
      } catch (error) {
        // Si falla, usar historial local como fallback
        const localHistory = localStorage.getItem('spider-history');
        return localHistory ? JSON.parse(localHistory) : [];
      }
    },
    staleTime: 5 * 60 * 1000 // 5 minutos
  });

  const downloadSpider = (spider: GeneratedSpider) => {
    const blob = new Blob([spider.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${spider.name}.py`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const viewCode = (spider: GeneratedSpider) => {
    // Navegar a vista de código o abrir modal
    navigate(`/spider-factory/code/${spider.id}`);
  };

  if (isLoading) return <CircularProgress />;
  if (error) return <Alert severity="error">Error cargando historial</Alert>;
  
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Historial de Spiders Generados
      </Typography>
      
      <DataGrid
        rows={spiderHistory || []}
        columns={[
          { field: 'name', headerName: 'Nombre', width: 200 },
          { 
            field: 'generatedAt', 
            headerName: 'Fecha', 
            width: 150,
            valueFormatter: (params) => 
              new Date(params.value).toLocaleDateString()
          },
          { field: 'medio', headerName: 'Medio', width: 150 },
          { field: 'seccion', headerName: 'Sección', width: 120 },
          { 
            field: 'actions', 
            headerName: 'Acciones', 
            width: 150,
            renderCell: (params) => (
              <>
                <IconButton 
                  onClick={() => downloadSpider(params.row)}
                  title="Descargar spider"
                >
                  <DownloadIcon />
                </IconButton>
                <IconButton 
                  onClick={() => viewCode(params.row)}
                  title="Ver código"
                >
                  <CodeIcon />
                </IconButton>
              </>
            )
          }
        ]}
        pageSize={10}
        rowsPerPageOptions={[10, 25, 50]}
        autoHeight
        disableSelectionOnClick
      />
    </Container>
  );
};

export default HistoryPage;