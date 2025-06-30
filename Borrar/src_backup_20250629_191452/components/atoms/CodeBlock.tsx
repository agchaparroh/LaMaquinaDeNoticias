import { Box, Paper, IconButton, Tooltip, useTheme } from '@mui/material'
import { ContentCopy as CopyIcon, Check as CheckIcon } from '@mui/icons-material'
import { useState } from 'react'

interface CodeBlockProps {
  code: string
  language?: string
  showLineNumbers?: boolean
}

function CodeBlock({ code, language = 'python', showLineNumbers = true }: CodeBlockProps) {
  const theme = useTheme()
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const lines = code.split('\n')
  const maxLineNumberWidth = String(lines.length).length

  return (
    <Paper
      elevation={0}
      sx={{
        position: 'relative',
        backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          px: 2,
          py: 1,
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: theme.palette.mode === 'dark' ? '#2d2d2d' : '#e0e0e0',
        }}
      >
        <Box
          component="span"
          sx={{
            fontSize: '0.75rem',
            color: 'text.secondary',
            fontFamily: 'monospace',
          }}
        >
          {language}
        </Box>
        <Tooltip title={copied ? 'Copiado!' : 'Copiar código'}>
          <IconButton size="small" onClick={handleCopy}>
            {copied ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>
      
      <Box
        component="pre"
        sx={{
          m: 0,
          p: 2,
          overflow: 'auto',
          fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
          fontSize: '0.875rem',
          lineHeight: 1.5,
        }}
      >
        {showLineNumbers ? (
          <Box component="code" sx={{ display: 'table' }}>
            {lines.map((line, index) => (
              <Box key={index} sx={{ display: 'table-row' }}>
                <Box
                  component="span"
                  sx={{
                    display: 'table-cell',
                    pr: 2,
                    textAlign: 'right',
                    color: 'text.secondary',
                    userSelect: 'none',
                    width: `${maxLineNumberWidth + 0.5}em`,
                  }}
                >
                  {index + 1}
                </Box>
                <Box
                  component="span"
                  sx={{
                    display: 'table-cell',
                    whiteSpace: 'pre',
                  }}
                >
                  {line || '\n'}
                </Box>
              </Box>
            ))}
          </Box>
        ) : (
          <Box component="code">{code}</Box>
        )}
      </Box>
    </Paper>
  )
}

export default CodeBlock