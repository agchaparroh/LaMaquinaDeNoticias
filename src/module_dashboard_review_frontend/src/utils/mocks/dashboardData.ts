// Mock data extendido para desarrollo del dashboard
// Incluye casos extremos, excepciones y todas las funcionalidades
import type { Hecho, FilterOptions } from '@/types/domain';

export const mockHechos: Hecho[] = [
  // CASO 1: Múltiples países (5 países) - Caso extremo geográfico
  {
    id: 1,
    contenido: "Cumbre internacional sobre cambio climático alcanza acuerdo histórico para reducir emisiones de carbono en un 50% para 2030, con participación de líderes mundiales y compromisos financieros sin precedentes.",
    fechaOcurrencia: "2025-06-12",
    precisionTemporal: "exacta",
    importancia: 10,
    tipoHecho: "EVENTO",
    pais: ["Brasil", "Argentina", "Colombia", "México", "Chile"],
    etiquetas: ["cumbre", "clima", "internacional", "acuerdo", "emisiones", "2030"],
    frecuenciaCitacion: 156,
    totalMenciones: 234,
    mencionesConfirmatorias: 198,
    fechaIngreso: "2025-06-12T08:30:00Z",
    evaluacionEditorial: "verificado_ok_editorial",
    editorEvaluador: "Dr. María Elena Vásquez",
    fechaEvaluacionEditorial: "2025-06-12T10:15:00Z",
    justificacionEvaluacionEditorial: "Confirmado con múltiples fuentes oficiales de la ONU y gobiernos participantes",
    consensoFuentes: "confirmado_multiples_fuentes",
    esEventoFuturo: false,
    metadata: {
      coberturaTv: true,
      trending: "#CumbreClima2025",
      impactoGlobal: "alto"
    },
    articuloMetadata: {
      medio: "Reuters América Latina",
      titular: "Histórico: Cinco países latinoamericanos firman pacto climático más ambicioso de la región",
      url: "https://reuters.com/mundo/cumbre-clima-latinoamerica-2025",
      fechaPublicacion: "2025-06-12T09:45:00Z",
      paisPublicacion: "Estados Unidos",
      tipoMedio: "digital",
      autor: "Isabella García-Montenegro",
      seccion: "Internacional",
      esOpinion: false,
      esOficial: true,
      resumen: "La cumbre climática latinoamericana concluyó con un acuerdo sin precedentes donde Brasil, Argentina, Colombia, México y Chile se comprometen a reducir sus emisiones de carbono en un 50% para 2030. El acuerdo incluye un fondo de $50 mil millones para tecnologías limpias y programas de reforestación masiva. Los presidentes firmaron el documento en una ceremonia transmitida en vivo desde Brasília.",
      categoriasAsignadas: ["Medio Ambiente", "Política Internacional", "Economía Verde", "Desarrollo Sostenible"],
      puntuacionRelevancia: 95,
      estadoProcesamiento: "completo"
    }
  },

  // CASO 2: Texto extremadamente largo - Caso extremo de contenido
  {
    id: 2,
    contenido: "Investigadores del Instituto Nacional de Biotecnología de Colombia, en colaboración con universidades internacionales de Estados Unidos, Reino Unido y Japón, anunciaron el desarrollo exitoso de una innovadora terapia génica para tratar la distrofia muscular de Duchenne, una enfermedad degenerativa que afecta principalmente a niños varones y que hasta ahora no tenía cura definitiva. Los ensayos clínicos de fase III, realizados durante los últimos 4 años con 847 pacientes de 23 países diferentes, mostraron una efectividad del 89% en la restauración de la función muscular y una mejora significativa en la calidad de vida de los pacientes tratados, lo que representa un avance médico revolucionario que podría cambiar para siempre el pronóstico de esta devastadora condición genética.",
    fechaOcurrencia: "2025-06-11",
    precisionTemporal: "dia",
    importancia: 9,
    tipoHecho: "ANUNCIO",
    pais: ["Colombia"],
    etiquetas: ["medicina", "terapia génica", "distrofia muscular", "investigación", "biotecnología", "ensayos clínicos", "avance médico", "colaboración internacional", "duchenne", "tratamiento", "cura", "pacientes", "innovación"],
    frecuenciaCitacion: 89,
    totalMenciones: 167,
    mencionesConfirmatorias: 134,
    fechaIngreso: "2025-06-11T14:22:00Z",
    evaluacionEditorial: "verificado_ok_editorial",
    editorEvaluador: "Dr. Carlos Mendoza Ruiz",
    fechaEvaluacionEditorial: "2025-06-11T16:30:00Z",
    justificacionEvaluacionEditorial: "Información verificada directamente con el Instituto Nacional de Biotecnología. Se confirmaron los datos de efectividad con la publicación en Nature Medicine.",
    consensoFuentes: "confirmado_multiples_fuentes",
    esEventoFuturo: false,
    articuloMetadata: {
      medio: "El Espectador",
      titular: "Científicos colombianos logran breakthrough histórico en terapia génica para distrofia muscular de Duchenne",
      url: "https://elespectador.com/salud/terapia-genica-duchenne-colombia-2025",
      fechaPublicacion: "2025-06-11T13:15:00Z",
      paisPublicacion: "Colombia",
      tipoMedio: "digital",
      autor: "Dra. Patricia Villamizar",
      seccion: "Salud y Ciencia",
      esOpinion: false,
      esOficial: false,
      resumen: "El Instituto Nacional de Biotecnología de Colombia presenta resultados de ensayos clínicos fase III para nueva terapia génica contra distrofia muscular de Duchenne. El tratamiento mostró 89% de efectividad en 847 pacientes de 23 países. La investigación, realizada en colaboración con universidades de EE.UU., Reino Unido y Japón, representa el mayor avance médico en esta área en décadas.",
      categoriasAsignadas: ["Ciencia", "Medicina", "Biotecnología", "Salud Pública", "Investigación"],
      puntuacionRelevancia: 92,
      estadoProcesamiento: "completo"
    }
  },

  // CASO 3: Importancia mínima (1) + Sin evaluación + Pocos datos
  {
    id: 3,
    contenido: "Actor local gana premio en festival de cine independiente.",
    fechaOcurrencia: "2025-06-10",
    importancia: 1,
    tipoHecho: "SUCESO",
    pais: ["Uruguay"],
    frecuenciaCitacion: 2,
    totalMenciones: 5,
    mencionesConfirmatorias: 3,
    evaluacionEditorial: undefined,
    consensoFuentes: "sin_confirmacion_suficiente_fuentes",
    articuloMetadata: {
      medio: "El País Uruguay",
      titular: "Actor uruguayo triunfa en festival de cine local",
      url: "https://elpais.com.uy/actor-festival-cine",
      fechaPublicacion: "2025-06-10T11:30:00Z",
      autor: "Redacción Cultural"
    }
  },

  // CASO 4: Consenso en disputa + Evaluación falsa + Muchas etiquetas
  {
    id: 4,
    contenido: "Supuesto hallazgo arqueológico de civilización perdida en la Amazonía genera controversia entre expertos internacionales debido a inconsistencias en las pruebas de carbono y metodología cuestionable.",
    fechaOcurrencia: "2025-06-09",
    precisionTemporal: "semana",
    importancia: 5,
    tipoHecho: "DECLARACION",
    pais: ["Perú", "Brasil"],
    etiquetas: ["arqueología", "amazonía", "civilización", "hallazgo", "controversia", "expertos", "carbono", "metodología", "ciencia", "historia", "investigación", "disputa", "academia", "peer-review", "evidencia"],
    frecuenciaCitacion: 34,
    totalMenciones: 78,
    mencionesConfirmatorias: 23,
    fechaIngreso: "2025-06-09T16:45:00Z",
    evaluacionEditorial: "declarado_falso_editorial",
    editorEvaluador: "Arq. Ana Sofía Torres",
    fechaEvaluacionEditorial: "2025-06-10T09:30:00Z",
    justificacionEvaluacionEditorial: "Múltiples expertos han desmentido el hallazgo. Las pruebas de carbono fueron realizadas por laboratorio no certificado. La metodología no cumple con estándares arqueológicos internacionales.",
    consensoFuentes: "en_disputa_por_hechos_contradictorios",
    esEventoFuturo: false,
    articuloMetadata: {
      medio: "National Geographic en Español",
      titular: "¿Civilización perdida en el Amazonas? Arqueólogos cuestionan controversial 'descubrimiento'",
      url: "https://nationalgeographic.es/amazonas-civilizacion-controversia",
      fechaPublicacion: "2025-06-09T14:20:00Z",
      paisPublicacion: "España",
      tipoMedio: "revista digital",
      autor: "Dr. Roberto Chimoy Effio",
      seccion: "Arqueología",
      esOpinion: false,
      esOficial: false,
      resumen: "Un supuesto hallazgo arqueológico en la selva amazónica peruana ha generado división en la comunidad científica. Mientras algunos investigadores afirman haber encontrado evidencias de una civilización desconocida, expertos internacionales cuestionan la metodología y validez de las pruebas presentadas.",
      categoriasAsignadas: ["Arqueología", "Ciencia", "Amazonía", "Controversia Científica", "Historia Precolombina"],
      puntuacionRelevancia: 67,
      estadoProcesamiento: "en_revision"
    }
  },

  // CASO 5: Evento futuro + Programación + Categorías IA extensas
  {
    id: 5,
    contenido: "Se anuncia la construcción del primer centro espacial comercial de Sudamérica que será inaugurado en Ecuador en 2027, con inversión de 2.8 mil millones de dólares.",
    fechaOcurrencia: "2027-03-15",
    precisionTemporal: "mes",
    importancia: 8,
    tipoHecho: "ANUNCIO",
    pais: ["Ecuador"],
    etiquetas: ["espacio", "comercial", "sudamérica", "construcción", "inversión", "tecnología", "futuro"],
    frecuenciaCitacion: 45,
    totalMenciones: 89,
    mencionesConfirmatorias: 67,
    fechaIngreso: "2025-06-08T10:15:00Z",
    evaluacionEditorial: "pendiente_revision_editorial",
    consensoFuentes: "pendiente_analisis_fuentes",
    esEventoFuturo: true,
    estadoProgramacion: "anunciado_oficial",
    articuloMetadata: {
      medio: "El Comercio Ecuador",
      titular: "Ecuador será sede del primer centro espacial comercial de Sudamérica con inversión multimillonaria",
      url: "https://elcomercio.com/centro-espacial-ecuador-2027",
      fechaPublicacion: "2025-06-08T08:45:00Z",
      paisPublicacion: "Ecuador",
      tipoMedio: "digital",
      autor: "Ing. María Fernanda Quiroz",
      seccion: "Tecnología",
      esOpinion: false,
      esOficial: true,
      resumen: "El gobierno ecuatoriano y un consorcio internacional anunciaron la construcción del primer centro espacial comercial de Sudamérica. La instalación, ubicada en la costa ecuatoriana, aprovechará la posición geográfica privilegiada del país para lanzamientos satelitales comerciales.",
      categoriasAsignadas: ["Tecnología Espacial", "Inversión Extranjera", "Desarrollo Tecnológico", "Industria Aeroespacial", "Innovación", "Economía Digital", "Infraestructura", "Ciencia y Tecnología"],
      puntuacionRelevancia: 85,
      estadoProcesamiento: "completo"
    }
  },

  // CASO 6: Sin etiquetas, sin estadísticas + Campo pais como string (caso legacy)
  {
    id: 6,
    contenido: "Festival gastronómico atrae turistas a la capital.",
    fechaOcurrencia: "2025-06-07",
    importancia: 2,
    tipoHecho: "EVENTO",
    pais: "Paraguay" as any, // Caso legacy donde es string en lugar de array
    evaluacionEditorial: undefined,
    articuloMetadata: {
      medio: "Última Hora",
      titular: "Gran festival gastronómico en Asunción",
      url: "https://ultimahora.com/festival-gastronomico",
      fechaPublicacion: "2025-06-07T15:30:00Z"
    }
  },

  // CASO 7: Múltiples categorías IA + Sin resumen + Datos de credibilidad altos
  {
    id: 7,
    contenido: "Nueva plataforma de inteligencia artificial desarrollada en Argentina promete revolucionar la educación online con personalización adaptativa basada en neurociencia cognitiva.",
    fechaOcurrencia: "2025-06-06",
    precisionTemporal: "exacta",
    importancia: 7,
    tipoHecho: "ANUNCIO",
    pais: ["Argentina"],
    etiquetas: ["IA", "educación", "tecnología", "neurociencia", "personalización", "argentina", "innovación"],
    frecuenciaCitacion: 67,
    totalMenciones: 145,
    mencionesConfirmatorias: 98,
    fechaIngreso: "2025-06-06T12:00:00Z",
    evaluacionEditorial: "verificado_ok_editorial",
    editorEvaluador: "Ing. Patricia Álvarez",
    fechaEvaluacionEditorial: "2025-06-06T14:45:00Z",
    justificacionEvaluacionEditorial: "Confirmado con la empresa desarrolladora y universidad asociada",
    consensoFuentes: "confirmado_multiples_fuentes",
    esEventoFuturo: false,
    articuloMetadata: {
      medio: "Página 12",
      titular: "Startup argentina crea IA revolucionaria para educación personalizada",
      url: "https://pagina12.com.ar/startup-ia-educacion",
      fechaPublicacion: "2025-06-06T11:30:00Z",
      paisPublicacion: "Argentina",
      tipoMedio: "digital",
      autor: "Lic. Fernando Gómez Herrera",
      seccion: "Tecnología",
      esOpinion: false,
      esOficial: false,
      // Sin resumen intencionalmente
      categoriasAsignadas: ["Inteligencia Artificial", "Educación Digital", "Neurociencia", "Tecnología Educativa", "Startups", "Innovación Argentina", "EdTech", "Personalización", "Aprendizaje Adaptativo", "Ciencias Cognitivas"],
      puntuacionRelevancia: 78,
      estadoProcesamiento: "completo"
    }
  },

  // CASO 8: Política internacional compleja + 3 países + Opinion piece
  {
    id: 8,
    contenido: "Tensiones diplomáticas entre Venezuela, Colombia y Brasil se intensifican tras disputas por recursos fronterizos y políticas migratorias, generando preocupación en organismos internacionales.",
    fechaOcurrencia: "2025-06-05",
    precisionTemporal: "dia",
    importancia: 9,
    tipoHecho: "DECLARACION",
    pais: ["Venezuela", "Colombia", "Brasil"],
    etiquetas: ["diplomacia", "tensiones", "frontera", "migración", "recursos", "internacional", "organismos"],
    frecuenciaCitacion: 234,
    totalMenciones: 456,
    mencionesConfirmatorias: 289,
    fechaIngreso: "2025-06-05T09:30:00Z",
    evaluacionEditorial: "verificado_ok_editorial",
    editorEvaluador: "Dra. Carmen Delgado",
    fechaEvaluacionEditorial: "2025-06-05T18:20:00Z",
    justificacionEvaluacionEditorial: "Información corroborada con fuentes diplomáticas de los tres países y OEA",
    consensoFuentes: "confirmado_multiples_fuentes",
    esEventoFuturo: false,
    articuloMetadata: {
      medio: "El Universal",
      titular: "Crisis diplomática trilateral: Venezuela, Colombia y Brasil en su peor momento de relaciones",
      url: "https://eluniversal.com/crisis-diplomatica-trilateral",
      fechaPublicacion: "2025-06-05T07:45:00Z",
      paisPublicacion: "Venezuela",
      tipoMedio: "digital",
      autor: "Amb. Ricardo Montoya Sánchez",
      seccion: "Internacional",
      esOpinion: true,
      esOficial: false,
      resumen: "Las relaciones entre Venezuela, Colombia y Brasil han alcanzado su punto más bajo en décadas debido a disputas por recursos fronterizos y políticas migratorias divergentes. Organismos internacionales como la OEA y UNASUR expresan preocupación por el escalamiento de tensiones que podría afectar la estabilidad regional.",
      categoriasAsignadas: ["Política Internacional", "Diplomacia", "Crisis Regional", "Migración", "Recursos Fronterizos"],
      puntuacionRelevancia: 91,
      estadoProcesamiento: "completo"
    }
  },

  // CASO 9: Deporte + Sin consenso fuentes + Evaluación pendiente
  {
    id: 9,
    contenido: "Futbolista boliviano fichado por equipo europeo de primera división en transferencia récord para el fútbol sudamericano.",
    fechaOcurrencia: "2025-06-04",
    importancia: 4,
    tipoHecho: "SUCESO",
    pais: ["Bolivia"],
    etiquetas: ["fútbol", "transferencia", "bolivia", "europa", "récord"],
    frecuenciaCitacion: 18,
    totalMenciones: 34,
    mencionesConfirmatorias: 12,
    fechaIngreso: "2025-06-04T16:20:00Z",
    evaluacionEditorial: "pendiente_revision_editorial",
    consensoFuentes: "sin_confirmacion_suficiente_fuentes",
    esEventoFuturo: false,
    articuloMetadata: {
      medio: "Los Tiempos",
      titular: "Histórico: Futbolista boliviano rompe récord en transferencia europea",
      url: "https://lostiempos.com/futbolista-boliviano-record",
      fechaPublicacion: "2025-06-04T14:10:00Z",
      paisPublicacion: "Bolivia",
      tipoMedio: "digital",
      autor: "Carlos Mendez",
      seccion: "Deportes",
      esOpinion: false,
      esOficial: false,
      resumen: "Un joven futbolista boliviano de 19 años ha sido fichado por un club de primera división europea en una transferencia que rompe todos los récords para el fútbol sudamericano. El monto de la operación no ha sido revelado oficialmente.",
      categoriasAsignadas: ["Deportes", "Fútbol", "Transferencias", "Bolivia", "Europa"],
      puntuacionRelevancia: 65,
      estadoProcesamiento: "pendiente"
    }
  },

  // CASO 10: Economía + 4 países + Datos máximos de credibilidad
  {
    id: 10,
    contenido: "Alianza económica entre Chile, Perú, Colombia y México establece nuevo bloque comercial del Pacífico con proyecciones de crecimiento del PIB conjunto del 15% en los próximos 5 años.",
    fechaOcurrencia: "2025-06-03",
    precisionTemporal: "exacta",
    importancia: 10,
    tipoHecho: "ANUNCIO",
    pais: ["Chile", "Perú", "Colombia", "México"],
    etiquetas: ["economía", "alianza", "pacífico", "comercio", "crecimiento", "PIB", "bloque", "proyecciones"],
    frecuenciaCitacion: 567,
    totalMenciones: 892,
    mencionesConfirmatorias: 743,
    fechaIngreso: "2025-06-03T11:15:00Z",
    evaluacionEditorial: "verificado_ok_editorial",
    editorEvaluador: "Ec. Miguel Herrera Vásquez",
    fechaEvaluacionEditorial: "2025-06-03T13:30:00Z",
    justificacionEvaluacionEditorial: "Confirmado oficialmente por los ministerios de economía de los cuatro países participantes",
    consensoFuentes: "confirmado_multiples_fuentes",
    esEventoFuturo: false,
    metadata: {
      impactoEconomico: "muy_alto",
      coberturaMedios: "internacional",
      trending: ["#AlianzaPacifico2025", "#BloqueEconomico"]
    },
    articuloMetadata: {
      medio: "Bloomberg Línea",
      titular: "Nace el mega bloque del Pacífico: Chile, Perú, Colombia y México crean alianza económica histórica",
      url: "https://bloomberg.com/alianza-pacifico-historica",
      fechaPublicacion: "2025-06-03T09:00:00Z",
      paisPublicacion: "Estados Unidos",
      tipoMedio: "digital",
      autor: "Dra. Patricia Morales-Chen",
      seccion: "Economía Internacional",
      esOpinion: false,
      esOficial: true,
      resumen: "Los presidentes de Chile, Perú, Colombia y México firmaron un acuerdo histórico para crear el bloque comercial más ambicioso del Pacífico latinoamericano. La alianza incluye eliminación de aranceles, libre movimiento de capitales y proyectos de infraestructura conjunta por $200 mil millones. Economistas proyectan un crecimiento del PIB conjunto del 15% en cinco años.",
      categoriasAsignadas: ["Economía Internacional", "Comercio Exterior", "Bloques Económicos", "Integración Regional", "Pacífico", "Crecimiento Económico"],
      puntuacionRelevancia: 98,
      estadoProcesamiento: "completo"
    }
  }
];

export const mockFilterOptions: FilterOptions = {
  medios: [
    "Reuters América Latina", "El Espectador", "El País Uruguay", "National Geographic en Español",
    "El Comercio Ecuador", "Última Hora", "Página 12", "El Universal", "Los Tiempos", "Bloomberg Línea",
    "La Nación", "El Tiempo", "Folha de S.Paulo", "La Tercera", "Clarín", "El País", "BBC Mundo"
  ],
  paises: [
    "Argentina", "Brasil", "Chile", "Colombia", "Ecuador", "México", "Perú", "Uruguay", 
    "Paraguay", "Bolivia", "Venezuela", "Costa Rica", "Panamá", "Guatemala", "Honduras"
  ],
  tiposHecho: ["SUCESO", "ANUNCIO", "DECLARACION", "BIOGRAFIA", "CONCEPTO", "NORMATIVA", "EVENTO"],
  evaluacionesEditoriales: ["pendiente_revision_editorial", "verificado_ok_editorial", "declarado_falso_editorial"]
};

// Función para generar hechos adicionales con variedad extrema
export const generateMockHechos = (count: number): Hecho[] => {
  const contenidoTemplates = [
    "Investigación revela que el {percentage}% de {group} en {region} experimenta {phenomenon}",
    "Nuevo {technology} desarrollado en {country} promete {benefit} para {sector}",
    "Autoridades de {country} implementan {policy} para combatir {problem}",
    "Empresa {industry} anuncia inversión de ${amount} millones en {project}",
    "Expertos {field} alertan sobre {risk} que podría afectar {population}"
  ];

  const variables = {
    percentage: ["45", "67", "78", "23", "89", "34", "56", "91"],
    group: ["jóvenes", "adultos mayores", "estudiantes", "trabajadores", "familias"],
    region: ["urbana", "rural", "metropolitana", "costera", "andina"],
    phenomenon: ["estrés laboral", "uso de redes sociales", "cambios climáticos", "nuevas tecnologías"],
    technology: ["algoritmo", "plataforma", "dispositivo", "sistema", "aplicación"],
    country: ["Argentina", "Chile", "Colombia", "México", "Brasil"],
    benefit: ["revolucionar", "mejorar", "optimizar", "transformar", "modernizar"],
    sector: ["educación", "salud", "transporte", "agricultura", "turismo"],
    policy: ["nuevas regulaciones", "programa social", "plan económico", "iniciativa ambiental"],
    problem: ["la pobreza", "el desempleo", "la contaminación", "la inseguridad"],
    industry: ["tecnológica", "farmacéutica", "automotriz", "energética", "alimentaria"],
    amount: ["150", "300", "750", "1200", "2500"],
    project: ["infraestructura", "investigación", "desarrollo sostenible", "innovación"],
    field: ["económicos", "médicos", "ambientales", "tecnológicos", "sociales"],
    risk: ["crisis económica", "emergencia sanitaria", "desastre natural", "ciberataque"],
    population: ["la región", "los ciudadanos", "la economía", "el medio ambiente"]
  };

  return Array.from({ length: count }, (_, index) => {
    const template = contenidoTemplates[index % contenidoTemplates.length];
    let contenido = template;
    
    // Reemplazar variables en el template
    Object.entries(variables).forEach(([key, values]) => {
      const regex = new RegExp(`{${key}}`, 'g');
      contenido = contenido.replace(regex, values[index % values.length]);
    });

    // Generar país(es) aleatorio(s)
    const numPaises = Math.random() > 0.7 ? (Math.random() > 0.5 ? 2 : 3) : 1;
    const paisesDisponibles = [...mockFilterOptions.paises];
    const paisesSeleccionados = [];
    for (let i = 0; i < numPaises; i++) {
      const randomIndex = Math.floor(Math.random() * paisesDisponibles.length);
      paisesSeleccionados.push(paisesDisponibles.splice(randomIndex, 1)[0]);
    }

    return {
      id: 1000 + index,
      contenido,
      fechaOcurrencia: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString().split('T')[0],
      importancia: Math.floor(Math.random() * 10) + 1,
      tipoHecho: mockFilterOptions.tiposHecho[index % mockFilterOptions.tiposHecho.length],
      pais: numPaises === 1 ? paisesSeleccionados[0] : paisesSeleccionados,
      etiquetas: Math.random() > 0.5 ? [`tag${index}`, `categoria${index % 5}`] : undefined,
      frecuenciaCitacion: Math.floor(Math.random() * 100),
      totalMenciones: Math.floor(Math.random() * 200),
      mencionesConfirmatorias: Math.floor(Math.random() * 150),
      evaluacionEditorial: Math.random() > 0.6 ? 
        (Math.random() > 0.7 ? 'verificado_ok_editorial' : 
         Math.random() > 0.5 ? 'declarado_falso_editorial' : 'pendiente_revision_editorial') : undefined,
      consensoFuentes: Math.random() > 0.5 ? 
        mockFilterOptions.evaluacionesEditoriales[Math.floor(Math.random() * 4)] : undefined,
      articuloMetadata: {
        medio: mockFilterOptions.medios[index % mockFilterOptions.medios.length],
        titular: `${contenido.substring(0, 60)}...`,
        url: `https://ejemplo${1000 + index}.com/noticia`,
        fechaPublicacion: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString(),
        autor: `Autor Generado ${index + 1}`,
        categoriasAsignadas: Math.random() > 0.3 ? [`Categoría ${index % 5}`, `Tema ${index % 3}`] : undefined
      }
    };
  });
};
