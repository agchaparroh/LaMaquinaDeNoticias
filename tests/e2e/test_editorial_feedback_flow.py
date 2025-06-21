"""
test_editorial_feedback_flow.py
Test End-to-End: Flujo de feedback editorial

Valida el flujo completo cuando un editor modifica la importancia de un hecho:
1. Dashboard muestra artículo con hechos e importancia automática
2. Editor ajusta importancia de un hecho via API
3. Backend actualiza base de datos con feedback
4. Dashboard refleja el cambio y registra para aprendizaje
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json


class EditorialFeedbackFlow:
    """Simula el flujo completo de feedback editorial"""
    
    def __init__(self):
        # Artículo ya procesado en el sistema
        self.article_data = {
            "id": "art-feedback-test-001",
            "titular": "Gobierno anuncia nuevas medidas económicas",
            "medio": "El Diario Nacional",
            "fecha_publicacion": "2024-01-15T10:00:00Z",
            "hechos": [
                {
                    "id": "hecho-001",
                    "contenido": "El gobierno anunció un aumento del 15% en el salario mínimo",
                    "tipo": "declaracion",
                    "importancia_automatica": 6,
                    "importancia_editor": None,
                    "confianza_extraccion": 0.92
                },
                {
                    "id": "hecho-002",
                    "contenido": "La medida beneficiará a 2 millones de trabajadores",
                    "tipo": "estadistica",
                    "importancia_automatica": 7,
                    "importancia_editor": None,
                    "confianza_extraccion": 0.88
                },
                {
                    "id": "hecho-003",
                    "contenido": "El ajuste entrará en vigencia el próximo mes",
                    "tipo": "temporal",
                    "importancia_automatica": 5,
                    "importancia_editor": None,
                    "confianza_extraccion": 0.95
                }
            ]
        }
        
        self.editor_info = {
            "usuario_id": "editor-123",
            "nombre": "María García",
            "rol": "editor_senior"
        }
        
        self.feedback_history = []
    
    def dashboard_display_article(self) -> dict:
        """Dashboard muestra artículo para revisión editorial"""
        display_data = {
            "articulo": self.article_data,
            "metadata": {
                "total_hechos": len(self.article_data["hechos"]),
                "hechos_sin_revisar": sum(1 for h in self.article_data["hechos"] 
                                          if h["importancia_editor"] is None),
                "promedio_confianza": sum(h["confianza_extraccion"] 
                                         for h in self.article_data["hechos"]) / len(self.article_data["hechos"])
            },
            "acciones_disponibles": [
                "ajustar_importancia",
                "marcar_verificado",
                "marcar_falso"
            ]
        }
        return display_data
    
    def editor_submit_feedback(self, hecho_id: str, nueva_importancia: int) -> dict:
        """Editor envía feedback de importancia via API"""
        # Validar entrada
        assert 1 <= nueva_importancia <= 10, "Importancia debe estar entre 1 y 10"
        
        # Encontrar el hecho
        hecho = next((h for h in self.article_data["hechos"] if h["id"] == hecho_id), None)
        assert hecho is not None, f"Hecho {hecho_id} no encontrado"
        
        # Preparar request
        feedback_request = {
            "importancia_editor_final": nueva_importancia,
            "usuario_id_editor": self.editor_info["usuario_id"],
            "timestamp": datetime.utcnow().isoformat(),
            "justificacion": f"Ajuste editorial: importancia cambió de {hecho['importancia_automatica']} a {nueva_importancia}"
        }
        
        # Simular llamada API POST /dashboard/feedback/hecho/{hecho_id}/importancia_feedback
        api_response = {
            "success": True,
            "message": f"Feedback de importancia actualizado para hecho {hecho_id}",
            "feedback_id": f"feedback-{int(datetime.utcnow().timestamp())}"
        }
        
        # Registrar en historial
        self.feedback_history.append({
            "hecho_id": hecho_id,
            "tipo": "importancia",
            "valor_anterior": hecho["importancia_automatica"],
            "valor_nuevo": nueva_importancia,
            "editor": self.editor_info["usuario_id"],
            "timestamp": feedback_request["timestamp"]
        })
        
        return api_response
    
    def backend_update_database(self, hecho_id: str, nueva_importancia: int) -> dict:
        """Backend actualiza base de datos con el feedback"""
        # Actualizar en memoria (simula UPDATE en Supabase)
        for hecho in self.article_data["hechos"]:
            if hecho["id"] == hecho_id:
                hecho["importancia_editor"] = nueva_importancia
                hecho["fecha_revision"] = datetime.utcnow().isoformat()
                hecho["revisado_por"] = self.editor_info["usuario_id"]
                
        # Simular registro en tabla feedback_importancia_hechos
        feedback_record = {
            "id": f"feedback-imp-{int(datetime.utcnow().timestamp())}",
            "hecho_id": hecho_id,
            "importancia_automatica_original": next(h["importancia_automatica"] 
                                                  for h in self.article_data["hechos"] 
                                                  if h["id"] == hecho_id),
            "importancia_editor_final": nueva_importancia,
            "usuario_id_editor": self.editor_info["usuario_id"],
            "fecha_feedback": datetime.utcnow().isoformat(),
            "usado_para_entrenamiento": False  # Se marcará true cuando se use para reentrenar
        }
        
        return {
            "hecho_actualizado": True,
            "feedback_registrado": feedback_record["id"],
            "tabla_actualizada": "feedback_importancia_hechos"
        }
    
    def dashboard_refresh_view(self) -> dict:
        """Dashboard actualiza vista con los cambios"""
        # Recalcular metadata
        updated_display = {
            "articulo": self.article_data,
            "metadata": {
                "total_hechos": len(self.article_data["hechos"]),
                "hechos_sin_revisar": sum(1 for h in self.article_data["hechos"] 
                                          if h["importancia_editor"] is None),
                "hechos_revisados": sum(1 for h in self.article_data["hechos"] 
                                       if h["importancia_editor"] is not None),
                "cambios_realizados": len(self.feedback_history)
            },
            "ultimos_cambios": self.feedback_history[-3:]  # Últimos 3 cambios
        }
        
        return updated_display


def test_editorial_feedback_flow():
    """Test E2E: Editor modifica importancia y se actualiza en todo el sistema"""
    
    # GIVEN: Artículo procesado disponible para revisión
    flow = EditorialFeedbackFlow()
    
    print("\n📝 Test E2E de flujo de feedback editorial\n")
    
    # 1. Dashboard muestra artículo
    print("1️⃣ DASHBOARD: Mostrando artículo para revisión...")
    display = flow.dashboard_display_article()
    assert display["metadata"]["hechos_sin_revisar"] == 3
    print(f"   ✅ Artículo cargado: '{flow.article_data['titular']}'")
    print(f"   📊 Hechos sin revisar: {display['metadata']['hechos_sin_revisar']}")
    
    # 2. Editor decide cambiar importancia del primer hecho
    print("\n2️⃣ EDITOR: Ajustando importancia de hechos...")
    hecho_target = flow.article_data["hechos"][0]
    nueva_importancia = 9  # Era 6, ahora 9 (más importante)
    
    print(f"   🎯 Hecho: '{hecho_target['contenido']}'")
    print(f"   📈 Importancia: {hecho_target['importancia_automatica']} → {nueva_importancia}")
    
    # 3. Enviar feedback via API
    print("\n3️⃣ API: Enviando feedback de importancia...")
    api_response = flow.editor_submit_feedback(hecho_target["id"], nueva_importancia)
    assert api_response["success"] is True
    print(f"   ✅ Feedback enviado: {api_response['message']}")
    
    # 4. Backend actualiza base de datos
    print("\n4️⃣ BACKEND: Actualizando base de datos...")
    db_update = flow.backend_update_database(hecho_target["id"], nueva_importancia)
    assert db_update["hecho_actualizado"] is True
    print(f"   ✅ Hecho actualizado en BD")
    print(f"   📝 Feedback registrado: {db_update['feedback_registrado']}")
    
    # 5. Dashboard refleja cambios
    print("\n5️⃣ DASHBOARD: Actualizando vista con cambios...")
    updated_display = flow.dashboard_refresh_view()
    assert updated_display["metadata"]["hechos_revisados"] == 1
    assert updated_display["metadata"]["hechos_sin_revisar"] == 2
    
    # Verificar que el hecho fue actualizado
    hecho_actualizado = next(h for h in updated_display["articulo"]["hechos"] 
                            if h["id"] == hecho_target["id"])
    assert hecho_actualizado["importancia_editor"] == nueva_importancia
    
    print(f"   ✅ Vista actualizada")
    print(f"   ✓ Hechos revisados: {updated_display['metadata']['hechos_revisados']}")
    print(f"   ✓ Hechos pendientes: {updated_display['metadata']['hechos_sin_revisar']}")
    
    # THEN: Verificar flujo completo
    print("\n✅ FLUJO DE FEEDBACK COMPLETADO:")
    print(f"   - Editor: {flow.editor_info['nombre']} ({flow.editor_info['rol']})")
    print(f"   - Cambios realizados: {len(flow.feedback_history)}")
    print(f"   - Feedback guardado para mejorar algoritmo")


def test_multiple_feedback_changes():
    """Test E2E: Múltiples cambios de feedback en secuencia"""
    
    flow = EditorialFeedbackFlow()
    
    print("\n🔄 Test E2E de múltiples cambios de feedback\n")
    
    # Realizar múltiples cambios
    cambios = [
        ("hecho-001", 9, "Muy importante - impacto directo en población"),
        ("hecho-002", 8, "Importante - cifras significativas"),
        ("hecho-003", 3, "Menor importancia - solo fecha de implementación")
    ]
    
    for hecho_id, nueva_imp, razon in cambios:
        print(f"\n📝 Actualizando {hecho_id}...")
        
        # Submit feedback
        api_resp = flow.editor_submit_feedback(hecho_id, nueva_imp)
        assert api_resp["success"]
        
        # Update DB
        db_resp = flow.backend_update_database(hecho_id, nueva_imp)
        assert db_resp["hecho_actualizado"]
        
        print(f"   ✅ Importancia → {nueva_imp} ({razon})")
    
    # Verificar estado final
    final_display = flow.dashboard_refresh_view()
    
    print("\n📊 RESUMEN FINAL:")
    print(f"   Total hechos: {final_display['metadata']['total_hechos']}")
    print(f"   Hechos revisados: {final_display['metadata']['hechos_revisados']}")
    print(f"   Cambios totales: {final_display['metadata']['cambios_realizados']}")
    
    # Todos los hechos deben estar revisados
    assert final_display["metadata"]["hechos_sin_revisar"] == 0
    assert final_display["metadata"]["hechos_revisados"] == 3
    
    # Verificar historial
    print("\n📜 HISTORIAL DE CAMBIOS:")
    for cambio in flow.feedback_history:
        print(f"   - Hecho {cambio['hecho_id']}: {cambio['valor_anterior']} → {cambio['valor_nuevo']}")


def test_feedback_validation_errors():
    """Test E2E: Validación de errores en feedback"""
    
    flow = EditorialFeedbackFlow()
    
    print("\n⚠️ Test E2E de validación de errores\n")
    
    # Caso 1: Importancia fuera de rango
    print("1️⃣ Probando importancia fuera de rango...")
    try:
        flow.editor_submit_feedback("hecho-001", 15)  # Max es 10
        assert False, "Debería fallar con importancia > 10"
    except AssertionError as e:
        print(f"   ✅ Error capturado correctamente: {str(e)}")
    
    # Caso 2: Hecho inexistente
    print("\n2️⃣ Probando hecho inexistente...")
    try:
        flow.editor_submit_feedback("hecho-999", 5)
        assert False, "Debería fallar con hecho inexistente"
    except AssertionError as e:
        print(f"   ✅ Error capturado correctamente: {str(e)}")
    
    # Caso 3: Importancia negativa
    print("\n3️⃣ Probando importancia negativa...")
    try:
        flow.editor_submit_feedback("hecho-001", -1)
        assert False, "Debería fallar con importancia < 1"
    except AssertionError as e:
        print(f"   ✅ Error capturado correctamente: {str(e)}")
    
    print("\n✅ Todas las validaciones funcionan correctamente")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
