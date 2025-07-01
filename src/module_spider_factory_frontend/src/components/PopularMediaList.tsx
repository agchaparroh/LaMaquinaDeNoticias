import React from 'react';
import { Paper, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';
import { useQuery } from '@tanstack/react-query';

interface PopularMedia {
  domain: string;
  name: string;
  count: number;
}

// Según SECCIÓN 20.2 - Lista de medios populares
// En página principal o dashboard:
const PopularMediaList = () => {
  const { data: popularMedia } = useQuery({
    queryKey: ['popular-media'],
    queryFn: () => Promise.resolve([]),
  });
  
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Medios más generados
      </Typography>
      <List>
        {popularMedia?.map((media: PopularMedia) => (
          <ListItem key={media.domain}>
            <ListItemText 
              primary={media.name}
              secondary={`${media.count} spiders generados`}
            />
            <Chip 
              label="Respuesta instantánea" 
              size="small" 
              color="primary"
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default PopularMediaList;