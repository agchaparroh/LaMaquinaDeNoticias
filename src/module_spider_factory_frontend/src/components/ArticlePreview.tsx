import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { Article } from '../types';

interface ArticlePreviewProps {
  articles: Article[];
}

// Según SECCIÓN 3.1 - Componente de preview de artículos EXACTO
const ArticlePreview = ({ articles }: ArticlePreviewProps) => (
  <Box>
    <Typography variant="h6">Artículos detectados:</Typography>
    {articles.map((article, index) => (
      <Card key={index} sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1">{article.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            {article.date} - {article.excerpt}
          </Typography>
        </CardContent>
      </Card>
    ))}
  </Box>
);

export default ArticlePreview;