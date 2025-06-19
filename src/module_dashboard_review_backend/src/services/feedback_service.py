"""
Feedback service for handling editorial feedback operations.
Manages importance feedback and editorial evaluations for facts (hechos).
"""

from typing import Optional
from loguru import logger

from .supabase_client import SupabaseClient
from ..models.requests import ImportanciaFeedbackRequest, EvaluacionEditorialRequest
from ..utils.exceptions import ResourceNotFoundError


class FeedbackService:
    """
    Service layer for handling feedback operations.
    
    This service manages all feedback-related database operations including
    importance adjustments and editorial evaluations for facts.
    """
    
    def __init__(self):
        """Initialize FeedbackService with Supabase client."""
        # Use singleton pattern via get_client() instead of direct instantiation
        self.supabase_client = SupabaseClient.get_client()
        logger.debug("FeedbackService initialized")
    
    async def submit_importancia_feedback(
        self, 
        hecho_id: int, 
        feedback: ImportanciaFeedbackRequest
    ) -> None:
        """
        Submit or update importance feedback for a fact.
        
        This method handles both creation of new feedback and updates to existing
        feedback. It verifies the fact exists before processing the feedback.
        
        Args:
            hecho_id: ID of the fact to provide feedback for
            feedback: Feedback data containing importance and editor ID
            
        Raises:
            HTTPException: If the fact doesn't exist (404) or database error occurs
        """
        logger.info(
            f"Processing importance feedback for hecho {hecho_id} "
            f"from editor {feedback.usuario_id_editor}"
        )
        
        # First, verify the hecho exists
        hecho = await SupabaseClient.get_single_record(
            table_name="hechos",
            record_id=hecho_id
        )
        
        if not hecho:
            logger.error(f"Hecho with ID {hecho_id} not found")
            raise ResourceNotFoundError(
                detail=f"Hecho with ID {hecho_id} not found"
            )
        
        logger.debug(f"Hecho {hecho_id} found, proceeding with feedback")
        
        # Check if feedback already exists for this hecho and editor
        def _check_existing_feedback():
            client = SupabaseClient.get_client()
            return client.table('feedback_importancia_hechos')\
                .select('id')\
                .eq('hecho_id', hecho_id)\
                .eq('usuario_id_editor', feedback.usuario_id_editor)\
                .limit(1)\
                .execute()
        
        existing_result = await SupabaseClient.execute_with_retry(
            _check_existing_feedback
        )
        
        if existing_result.data and len(existing_result.data) > 0:
            # Update existing feedback
            feedback_id = existing_result.data[0]['id']
            logger.info(
                f"Updating existing feedback {feedback_id} for hecho {hecho_id}"
            )
            
            def _update_feedback():
                client = SupabaseClient.get_client()
                return client.table('feedback_importancia_hechos')\
                    .update({
                        'importancia_editor_final': feedback.importancia_editor_final,
                        'updated_at': 'now()'
                    })\
                    .eq('id', feedback_id)\
                    .execute()
            
            await SupabaseClient.execute_with_retry(_update_feedback)
            
            logger.info(
                f"Successfully updated importance feedback for hecho {hecho_id}"
            )
        else:
            # Insert new feedback
            logger.info(
                f"Creating new feedback for hecho {hecho_id}"
            )
            
            def _insert_feedback():
                client = SupabaseClient.get_client()
                return client.table('feedback_importancia_hechos')\
                    .insert({
                        'hecho_id': hecho_id,
                        'usuario_id_editor': feedback.usuario_id_editor,
                        'importancia_editor_final': feedback.importancia_editor_final
                    })\
                    .execute()
            
            await SupabaseClient.execute_with_retry(_insert_feedback)
            
            logger.info(
                f"Successfully created new importance feedback for hecho {hecho_id}"
            )
    
    async def submit_evaluacion_editorial(
        self,
        hecho_id: int,
        evaluacion: EvaluacionEditorialRequest
    ) -> None:
        """
        Submit editorial evaluation for a fact.
        
        This method updates the editorial evaluation and justification for a fact.
        It verifies the fact exists before processing the evaluation.
        
        Args:
            hecho_id: ID of the fact to evaluate
            evaluacion: Evaluation data containing verdict and justification
            
        Raises:
            HTTPException: If the fact doesn't exist (404) or database error occurs
        """
        logger.info(
            f"Processing editorial evaluation for hecho {hecho_id} "
            f"with verdict: {evaluacion.evaluacion_editorial}"
        )
        
        # First, verify the hecho exists
        hecho = await SupabaseClient.get_single_record(
            table_name="hechos",
            record_id=hecho_id
        )
        
        if not hecho:
            logger.error(f"Hecho with ID {hecho_id} not found")
            raise ResourceNotFoundError(
                detail=f"Hecho with ID {hecho_id} not found"
            )
        
        logger.debug(f"Hecho {hecho_id} found, proceeding with editorial evaluation")
        
        # Update evaluacion_editorial fields
        def _update_evaluation():
            client = SupabaseClient.get_client()
            return client.table('hechos')\
                .update({
                    'evaluacion_editorial': evaluacion.evaluacion_editorial,
                    'justificacion_evaluacion_editorial': evaluacion.justificacion_evaluacion_editorial,
                    'updated_at': 'now()'
                })\
                .eq('id', hecho_id)\
                .execute()
        
        await SupabaseClient.execute_with_retry(_update_evaluation)
        
        logger.info(
            f"Successfully updated editorial evaluation for hecho {hecho_id}"
        )
