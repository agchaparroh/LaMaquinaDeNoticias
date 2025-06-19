"""
Feedback API routes for editorial review endpoints.

Provides endpoints for submitting feedback on facts (hechos) including
importance adjustments and editorial evaluations.
"""

from fastapi import APIRouter, Depends, Path, HTTPException
from loguru import logger

# Import models
from ..models.requests import ImportanciaFeedbackRequest, EvaluacionEditorialRequest
from ..models.responses import FeedbackResponse

# Import services and dependencies
from ..services.feedback_service import FeedbackService
from ..core.dependencies import get_feedback_service

# Import custom exceptions
from ..utils.exceptions import ResourceNotFoundError

# Create router instance
router = APIRouter()


@router.post(
    "/hecho/{hecho_id}/importancia_feedback",
    response_model=FeedbackResponse,
    summary="Submit importance feedback",
    description="""
    Submit editorial feedback on the importance level of a fact (hecho).
    
    This endpoint allows editors to provide feedback on the automatically
    assigned importance, creating a learning loop by recording corrections
    in the feedback_importancia_hechos table to improve the importance
    algorithm over time.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/dashboard/feedback/hecho/123/importancia_feedback" \\
         -H "Content-Type: application/json" \\
         -d '{
           "importancia_editor_final": 8,
           "usuario_id_editor": "editor123"
         }'
    ```
    """,
    responses={
        200: {
            "description": "Feedback successfully submitted",
            "model": FeedbackResponse
        },
        400: {
            "description": "Bad request or database error"
        },
        404: {
            "description": "Fact (hecho) not found"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def submit_importancia_feedback(
    hecho_id: int = Path(..., gt=0, description="ID of the fact to provide feedback for"),
    feedback: ImportanciaFeedbackRequest = None,
    feedback_service: FeedbackService = Depends(get_feedback_service)
) -> FeedbackResponse:
    """
    Submit importance feedback for a specific fact.
    
    Args:
        hecho_id: ID of the fact (must be greater than 0)
        feedback: Feedback data containing new importance level and editor ID
        feedback_service: Injected service for handling feedback operations
        
    Returns:
        FeedbackResponse with success status and confirmation message
        
    Raises:
        HTTPException 404: If the fact with given ID doesn't exist
        HTTPException 400: If any other error occurs during processing
    """
    try:
        logger.info(
            f"Received importance feedback request for hecho {hecho_id}",
            extra={
                "hecho_id": hecho_id,
                "editor": feedback.usuario_id_editor,
                "new_importance": feedback.importancia_editor_final
            }
        )
        
        # Call service to submit feedback
        await feedback_service.submit_importancia_feedback(hecho_id, feedback)
        
        # Return success response
        return FeedbackResponse(
            success=True,
            message=f"Feedback de importancia actualizado para hecho {hecho_id}"
        )
        
    except ResourceNotFoundError as e:
        # Re-raise custom exceptions as HTTPException for API response
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error processing importance feedback: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/hecho/{hecho_id}/evaluacion_editorial",
    response_model=FeedbackResponse,
    summary="Submit editorial evaluation",
    description="""
    Submit editorial evaluation for a fact (hecho).
    
    This endpoint allows editors to evaluate facts as either 'verificado_ok_editorial'
    (verified as correct) or 'declarado_falso_editorial' (declared as false),
    along with a justification for their decision. This feedback is crucial
    for quality control and improving the automatic extraction system.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/dashboard/feedback/hecho/123/evaluacion_editorial" \\
         -H "Content-Type: application/json" \\
         -d '{
           "evaluacion_editorial": "verificado_ok_editorial",
           "justificacion_evaluacion_editorial": "Fact correctly extracted and verified against multiple sources"
         }'
    ```
    """,
    responses={
        200: {
            "description": "Evaluation successfully submitted",
            "model": FeedbackResponse
        },
        400: {
            "description": "Bad request or database error"
        },
        404: {
            "description": "Fact (hecho) not found"
        },
        422: {
            "description": "Validation error - invalid evaluation value"
        }
    }
)
async def submit_evaluacion_editorial(
    hecho_id: int = Path(..., gt=0, description="ID of the fact to evaluate"),
    evaluacion: EvaluacionEditorialRequest = None,
    feedback_service: FeedbackService = Depends(get_feedback_service)
) -> FeedbackResponse:
    """
    Submit editorial evaluation for a specific fact.
    
    Args:
        hecho_id: ID of the fact (must be greater than 0)
        evaluacion: Evaluation data containing verdict and justification
        feedback_service: Injected service for handling feedback operations
        
    Returns:
        FeedbackResponse with success status and confirmation message
        
    Raises:
        HTTPException 404: If the fact with given ID doesn't exist
        HTTPException 400: If any other error occurs during processing
    """
    try:
        logger.info(
            f"Received editorial evaluation request for hecho {hecho_id}",
            extra={
                "hecho_id": hecho_id,
                "verdict": evaluacion.evaluacion_editorial,
                "has_justification": bool(evaluacion.justificacion_evaluacion_editorial)
            }
        )
        
        # Call service to submit evaluation
        await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion)
        
        # Return success response
        return FeedbackResponse(
            success=True,
            message=f"Evaluación editorial actualizada para hecho {hecho_id}"
        )
        
    except ResourceNotFoundError as e:
        # Re-raise custom exceptions as HTTPException for API response
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error processing editorial evaluation: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
