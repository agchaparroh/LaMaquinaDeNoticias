import { Button, ButtonProps } from '@mui/material'
import { CloudUpload as UploadIcon } from '@mui/icons-material'
import { useRef } from 'react'

interface FileUploadButtonProps extends Omit<ButtonProps, 'onChange'> {
  accept?: string
  multiple?: boolean
  onChange: (files: FileList | null) => void
  label?: string
}

function FileUploadButton({ 
  accept = '*', 
  multiple = false, 
  onChange,
  label = 'Subir archivo',
  ...buttonProps 
}: FileUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.files)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        style={{ display: 'none' }}
      />
      <Button
        startIcon={<UploadIcon />}
        onClick={handleClick}
        variant="contained"
        {...buttonProps}
      >
        {label}
      </Button>
    </>
  )
}

export default FileUploadButton