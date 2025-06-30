import { Chip, ChipProps } from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  HourglassEmpty as PendingIcon
} from '@mui/icons-material'

export type Status = 'success' | 'error' | 'warning' | 'info' | 'pending'

interface StatusChipProps extends Omit<ChipProps, 'color'> {
  status: Status
  label: string
}

const statusConfig: Record<Status, { 
  color: ChipProps['color'], 
  icon: React.ReactElement 
}> = {
  success: { 
    color: 'success', 
    icon: <CheckCircleIcon /> 
  },
  error: { 
    color: 'error', 
    icon: <ErrorIcon /> 
  },
  warning: { 
    color: 'warning', 
    icon: <WarningIcon /> 
  },
  info: { 
    color: 'info', 
    icon: <InfoIcon /> 
  },
  pending: { 
    color: 'default', 
    icon: <PendingIcon /> 
  },
}

function StatusChip({ status, label, ...props }: StatusChipProps) {
  const config = statusConfig[status]
  
  return (
    <Chip
      label={label}
      color={config.color}
      icon={config.icon}
      size="small"
      {...props}
    />
  )
}

export default StatusChip