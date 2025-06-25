import { Alert, AlertTitle, AlertProps } from '@mui/material'

interface ErrorMessageProps extends AlertProps {
  title?: string
  message: string
}

function ErrorMessage({ 
  title = 'Error', 
  message, 
  severity = 'error',
  ...props 
}: ErrorMessageProps) {
  return (
    <Alert severity={severity} {...props}>
      <AlertTitle>{title}</AlertTitle>
      {message}
    </Alert>
  )
}

export default ErrorMessage