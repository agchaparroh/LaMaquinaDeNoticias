import { LinearProgress, Box, Typography } from '@mui/material'

interface ProgressBarProps {
  value: number
  label?: string
  showPercentage?: boolean
  color?: 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'
}

function ProgressBar({ 
  value, 
  label, 
  showPercentage = true,
  color = 'primary' 
}: ProgressBarProps) {
  return (
    <Box sx={{ width: '100%' }}>
      {(label || showPercentage) && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          {label && (
            <Typography variant="body2" color="text.secondary">
              {label}
            </Typography>
          )}
          {showPercentage && (
            <Typography variant="body2" color="text.secondary">
              {`${Math.round(value)}%`}
            </Typography>
          )}
        </Box>
      )}
      <LinearProgress 
        variant="determinate" 
        value={value} 
        color={color}
        sx={{
          height: 8,
          borderRadius: 4,
          backgroundColor: (theme) => 
            theme.palette.mode === 'dark' ? 'grey.800' : 'grey.200',
        }}
      />
    </Box>
  )
}

export default ProgressBar