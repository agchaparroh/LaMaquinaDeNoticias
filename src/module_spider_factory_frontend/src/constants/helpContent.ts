// Contenido de ayuda contextual para el wizard
export const HELP_CONTENT = {
  // Paso 1: Información básica
  URL_SITIO: "Ingresa la dirección web completa del sitio de noticias que quieres monitorear. Ejemplo: https://elpais.com",
  MEDIO: "Nombre del medio de comunicación para identificarlo fácilmente en tu lista. Ejemplo: El País, La Vanguardia",
  AREA_GEOGRAFICA: "Región o país al que pertenece el medio. Esto ayuda a organizar tus monitores por ubicación geográfica",
  TIPO_MEDIO: "Tipo de publicación: Diario (noticias diarias), Revista (publicación periódica), Agencia (distribuidor de noticias)",
  FRECUENCIA: "¿Con qué frecuencia quieres que revisemos el sitio en busca de nuevas noticias? Más frecuente = más actualizado pero más recursos",
  FORZAR_ANALISIS: "Activar si quieres hacer un análisis completamente nuevo, ignorando cualquier información guardada previamente",

  // Paso 2: URLs y sección
  SECCION: "Nombre de la sección específica que quieres monitorear. Ejemplo: 'Política', 'Deportes', 'Internacional'",
  URL_SECCION: "Dirección web específica de la sección. Ejemplo: https://elpais.com/espana/politica/",
  TIENE_RSS: "¿El sitio web tiene feeds RSS? Los RSS son más eficientes para obtener noticias actualizadas",
  RSS_URL: "Si el sitio tiene RSS, ingresa aquí la dirección del feed. Ejemplo: https://elpais.com/rss/ccaa/madrid.xml",

  // Análisis y configuración
  ESTRATEGIA_DETECCION: "Método que usaremos para obtener las noticias: RSS (más rápido), Web Scraping (más completo) o Híbrido",
  RENDERIZADO_JS: "Algunos sitios modernos necesitan JavaScript para mostrar el contenido. Activar si el sitio no funciona normalmente",
  SELECTORES_CSS: "Códigos técnicos que le dicen al sistema dónde encontrar los elementos específicos en la página web",
};

export const EXAMPLES = {
  // Ejemplos para cada campo
  URLS_POPULARES: [
    "https://elpais.com",
    "https://lavanguardia.com", 
    "https://elmundo.es",
    "https://abc.es",
    "https://20minutos.es"
  ],
  
  NOMBRES_MEDIOS: [
    "El País",
    "La Vanguardia",
    "El Mundo",
    "ABC",
    "20 Minutos"
  ],
  
  SECCIONES_COMUNES: [
    "Política",
    "Deportes", 
    "Internacional",
    "Economía",
    "Cultura",
    "Tecnología",
    "Sociedad"
  ],
  
  URLS_SECCION: [
    "https://elpais.com/espana/",
    "https://lavanguardia.com/deportes/",
    "https://elmundo.es/internacional/",
    "https://abc.es/economia/"
  ]
};

export const VALIDATION_MESSAGES = {
  URL_INVALID: "Por favor, ingresa una URL válida que comience con http:// o https://",
  URL_REQUIRED: "La URL del sitio es obligatoria",
  MEDIO_REQUIRED: "El nombre del medio es obligatorio",
  MEDIO_TOO_SHORT: "El nombre debe tener al menos 3 caracteres",
  SECCION_REQUIRED: "El nombre de la sección es obligatorio", 
  URL_SECCION_REQUIRED: "La URL de la sección es obligatoria",
  RSS_URL_INVALID: "La URL del RSS no es válida",
};