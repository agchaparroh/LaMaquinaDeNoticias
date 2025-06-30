import React, { useState } from 'react';
import { 
  Box, 
  Chip, 
  Typography, 
  Collapse, 
  IconButton,
  Paper
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';

interface ExampleShowcaseProps {
  title: string;
  examples: string[];
  onSelect?: (example: string) => void;
  maxVisible?: number;
  variant?: 'outlined' | 'filled';
}

const ExampleShowcase: React.FC<ExampleShowcaseProps> = ({
  title,
  examples,
  onSelect,
  maxVisible = 3,
  variant = 'outlined'
}) => {
  const [expanded, setExpanded] = useState(false);
  
  const visibleExamples = expanded ? examples : examples.slice(0, maxVisible);
  const hasMore = examples.length > maxVisible;

  const handleExampleClick = (example: string) => {
    if (onSelect) {
      onSelect(example);
    }
  };

  return (
    <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
      <Typography variant="caption" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: hasMore ? 1 : 0 }}>
        {visibleExamples.map((example, index) => (
          <Chip
            key={index}
            label={example}
            variant={variant}
            size="small"
            onClick={() => handleExampleClick(example)}
            sx={{ 
              cursor: onSelect ? 'pointer' : 'default',
              '&:hover': onSelect ? { bgcolor: 'primary.light', color: 'primary.contrastText' } : {}
            }}
          />
        ))}
      </Box>

      {hasMore && (
        <Collapse in={expanded}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
            {examples.slice(maxVisible).map((example, index) => (
              <Chip
                key={index + maxVisible}
                label={example}
                variant={variant}
                size="small"
                onClick={() => handleExampleClick(example)}
                sx={{ 
                  cursor: onSelect ? 'pointer' : 'default',
                  '&:hover': onSelect ? { bgcolor: 'primary.light', color: 'primary.contrastText' } : {}
                }}
              />
            ))}
          </Box>
        </Collapse>
      )}

      {hasMore && (
        <Box sx={{ textAlign: 'center', mt: 1 }}>
          <IconButton 
            size="small" 
            onClick={() => setExpanded(!expanded)}
            sx={{ 
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s'
            }}
          >
            <ExpandMoreIcon fontSize="small" />
          </IconButton>
        </Box>
      )}
    </Paper>
  );
};

export default ExampleShowcase;