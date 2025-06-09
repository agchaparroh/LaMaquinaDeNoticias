"""
Modelos Pydantic específicos para metadatos del pipeline.
Reemplazan los campos genéricos metadata_*: Dict[str, Any] 
con estructuras específicas que preservan información de LLMs.

SOLUCIÓN AL PROBLEMA: Preservación de Información Estructurada
==============================================================
Los LLMs generan 43 campos específicos y validados que antes se perdían
al colapsar en campos genéricos. Estos modelos preservan el 100% de 
esa información con validación automática.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class MetadatosHecho(BaseModel):
    """
    Metadatos específicos para hechos extraídos por Prompt_2.
    Preserva campos que antes se perdían en metadata_hecho genérico.
    
    Campos preservados del JSON del LLM:
    - precision_temporal, tipo_hecho, pais, region, ciudad
    - es_futuro, estado_programacion
    """
    # Campos de precisión temporal y clasificación
    precision_temporal: Optional[str] = Field(
        None, 
        description="Precisión temporal del hecho",
        pattern=r"^(exacta|dia|semana|mes|trimestre|año|decada|periodo)$"
    )
    tipo_hecho: Optional[str] = Field(
        None,
        description="Tipo de hecho identificado",
        pattern=r"^(SUCESO|ANUNCIO|DECLARACION|BIOGRAFIA|CONCEPTO|NORMATIVA|EVENTO)$"
    )
    
    # Campos geográficos (arrays del JSON)
    pais: List[str] = Field(
        default_factory=list,
        description="Lista de países relevantes para el hecho"
    )
    region: List[str] = Field(
        default_factory=list,
        description="Lista de regiones mencionadas"
    )
    ciudad: List[str] = Field(
        default_factory=list,
        description="Lista de ciudades mencionadas"
    )
    
    # Campos temporales futuros
    es_futuro: Optional[bool] = Field(
        None,
        description="Indica si el hecho es un evento futuro"
    )
    estado_programacion: Optional[str] = Field(
        None,
        description="Estado de programación para eventos futuros",
        pattern=r"^(programado|confirmado|cancelado|modificado)$"
    )

class MetadatosEntidad(BaseModel):
    """
    Metadatos específicos para entidades extraídas por Prompt_2.
    Preserva campos que antes se perdían en metadata_entidad genérico.
    
    Campos preservados del JSON del LLM:
    - tipo, alias, fecha_nacimiento, fecha_disolucion, descripcion
    """
    # Tipo de entidad con validación estricta
    tipo: Optional[str] = Field(
        None,
        description="Tipo de entidad identificada",
        pattern=r"^(PERSONA|ORGANIZACION|INSTITUCION|LUGAR|EVENTO|NORMATIVA|CONCEPTO)$"
    )
    
    # Alias como array (preserva estructura original)
    alias: List[str] = Field(
        default_factory=list,
        description="Nombres alternativos, siglas o alias de la entidad"
    )
    
    # Fechas con validación de formato
    fecha_nacimiento: Optional[str] = Field(
        None,
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="Fecha de nacimiento/inicio en formato YYYY-MM-DD"
    )
    fecha_disolucion: Optional[str] = Field(
        None,
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="Fecha de disolución/fin en formato YYYY-MM-DD"
    )
    
    # Campo para descripción estructurada (los guiones del prompt)
    descripcion_estructurada: Optional[List[str]] = Field(
        default_factory=list,
        description="Descripción como lista de puntos (separados por guiones en prompt)"
    )

class MetadatosCita(BaseModel):
    """
    Metadatos específicos para citas extraídas por Prompt_3.
    Preserva campos que antes se perdían en metadata_cita genérico.
    
    Campos preservados del JSON del LLM:
    - fecha, contexto, relevancia (con constraint 1-5)
    """
    # Fecha específica de la cita
    fecha: Optional[str] = Field(
        None,
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="Fecha específica de la cita en formato YYYY-MM-DD"
    )
    
    # Contexto de la declaración
    contexto: Optional[str] = Field(
        None,
        description="Contexto breve en que se realizó la cita"
    )
    
    # Relevancia con constraint numérico del prompt
    relevancia: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Relevancia de la cita en escala 1-5"
    )

class PeriodoReferencia(BaseModel):
    """Periodo de referencia para datos cuantitativos"""
    inicio: Optional[str] = Field(
        None, 
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="Fecha de inicio del periodo"
    )
    fin: Optional[str] = Field(
        None, 
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="Fecha de fin del periodo"
    )

class MetadatosDato(BaseModel):
    """
    Metadatos específicos para datos cuantitativos extraídos por Prompt_3.
    Preserva campos que antes se perdían en metadata_dato genérico.
    
    Campos preservados del JSON del LLM:
    - categoria, tipo_periodo, tendencia, valor_anterior, variaciones
    - ambito_geografico, periodo (objeto anidado)
    """
    # Categoría con validación estricta según prompt
    categoria: Optional[str] = Field(
        None,
        description="Categoría del dato cuantitativo",
        pattern=r"^(económico|demográfico|electoral|social|presupuestario|sanitario|ambiental|conflicto|otro)$"
    )
    
    # Tipo de periodo según prompt
    tipo_periodo: Optional[str] = Field(
        None,
        description="Tipo de periodo al que se refiere el dato",
        pattern=r"^(anual|trimestral|mensual|semanal|diario|puntual|acumulado)$"
    )
    
    # Tendencia según prompt
    tendencia: Optional[str] = Field(
        None,
        description="Tendencia observada en el dato",
        pattern=r"^(aumento|disminución|estable)$"
    )
    
    # Valores comparativos
    valor_anterior: Optional[float] = Field(
        None,
        description="Valor anterior para comparación"
    )
    variacion_absoluta: Optional[float] = Field(
        None,
        description="Variación absoluta respecto al valor anterior"
    )
    variacion_porcentual: Optional[float] = Field(
        None,
        description="Variación porcentual respecto al valor anterior"
    )
    
    # Ámbito geográfico como array
    ambito_geografico: List[str] = Field(
        default_factory=list,
        description="Ámbito geográfico al que se refiere el dato"
    )
    
    # Periodo como objeto anidado
    periodo: Optional[PeriodoReferencia] = Field(
        None,
        description="Periodo de referencia específico"
    )
