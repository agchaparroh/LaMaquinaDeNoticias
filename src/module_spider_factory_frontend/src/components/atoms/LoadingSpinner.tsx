import { CircularProgress, Box, BoxProps } from '@mui/material'

interface LoadingSpinnerProps extends BoxProps {
  size?: number
  color?: 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' | 'inherit'
}

function LoadingSpinner({ 
  size = 40, 
  color = 'primary',
  ...boxProps 
}: LoadingSpinnerProps) {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="200px"
      {...boxProps}
    >
      <CircularProgress size={size} color={color} />
    </Box>
  )
}

export default LoadingSpinner