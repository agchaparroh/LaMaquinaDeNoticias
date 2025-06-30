import { Box, Typography, Button } from '@mui/material'
import { SvgIconComponent } from '@mui/icons-material'

interface EmptyStateProps {
  icon: SvgIconComponent
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}

function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  actionLabel, 
  onAction 
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 400,
        p: 4,
        textAlign: 'center',
      }}
    >
      <Icon 
        sx={{ 
          fontSize: 80, 
          color: 'text.secondary', 
          mb: 2,
          opacity: 0.5
        }} 
      />
      <Typography variant="h5" gutterBottom color="text.secondary">
        {title}
      </Typography>
      {description && (
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </Box>
  )
}

export default EmptyState