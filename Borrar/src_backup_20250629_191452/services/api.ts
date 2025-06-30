import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_TIMEOUT = 30000 // 30 segundos

// Tipo para errores personalizados
export interface CustomError {
  message: string
  status?: number
  data?: any
  originalError: AxiosError
}

// Crear instancia de Axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token de autenticación (si es necesario en el futuro)
let authToken: string | null = null

export const setAuthToken = (token: string | null) => {
  authToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// Interceptor de request
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Agregar timestamp a las requests para evitar caché
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }

    // Log de requests en desarrollo
    if (import.meta.env.DEV) {
      console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`, config.data)
    }

    return config
  },
  (error: AxiosError) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Interceptor de response
api.interceptors.response.use(
  (response) => {
    // Log de responses en desarrollo
    if (import.meta.env.DEV) {
      console.log(`✅ Response from ${response.config.url}:`, response.data)
    }
    return response
  },
  async (error: AxiosError<{ message?: string; detail?: string }>) => {
    // Manejo de errores específicos
    if (error.response) {
      const errorMessage = error.response.data?.message || 
                          error.response.data?.detail || 
                          'Error en la solicitud'
      
      switch (error.response.status) {
        case 401:
          // Token expirado o inválido
          setAuthToken(null)
          // Solo redirigir a login si no estamos ya en esa página
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          break
        
        case 403:
          console.error('Acceso denegado:', errorMessage)
          break
        
        case 404:
          console.error('Recurso no encontrado:', errorMessage)
          break
        
        case 429:
          // Rate limiting
          console.error('Demasiadas solicitudes. Por favor intenta más tarde.')
          break
        
        case 500:
        case 502:
        case 503:
        case 504:
          console.error('Error del servidor:', errorMessage)
          break
        
        default:
          console.error(`Error ${error.response.status}:`, errorMessage)
      }
    } else if (error.request) {
      // La request se hizo pero no se recibió respuesta
      console.error('No se pudo conectar con el servidor')
    } else {
      // Algo pasó al configurar la request
      console.error('Error de configuración:', error.message)
    }

    // Transformar error para un manejo más fácil
    const customError: CustomError = {
      message: error.response?.data?.message || 
               error.response?.data?.detail || 
               error.message || 
               'Error desconocido',
      status: error.response?.status,
      data: error.response?.data,
      originalError: error,
    }

    return Promise.reject(customError)
  }
)

// Funciones helper para requests comunes
export const apiClient = {
  get: <T = any>(url: string, params?: any) => 
    api.get<T>(url, { params }).then(res => res.data),
  
  post: <T = any>(url: string, data?: any) => 
    api.post<T>(url, data).then(res => res.data),
  
  put: <T = any>(url: string, data?: any) => 
    api.put<T>(url, data).then(res => res.data),
  
  patch: <T = any>(url: string, data?: any) => 
    api.patch<T>(url, data).then(res => res.data),
  
  delete: <T = any>(url: string) => 
    api.delete<T>(url).then(res => res.data),
}

// Función para manejar uploads
export const uploadFile = async (url: string, file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress?.(progress)
      }
    },
  })
}

// Función para descargar archivos
export const downloadFile = async (url: string, filename: string) => {
  try {
    const response = await api.get(url, {
      responseType: 'blob',
    })

    // Crear un enlace temporal para descargar
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error('Error descargando archivo:', error)
    throw error
  }
}

export default api