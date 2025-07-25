#!/usr/bin/env python3
"""
Análisis exhaustivo de todas las URLs de medios para Spider Factory 2.0
Usa Firecrawl para analizar cada URL y documentar los desafíos
"""

import asyncio
import hashlib  # noqa: F401
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional  # noqa: F401

import httpx

# Configuración de Firecrawl
FIRECRAWL_API_KEY = "fc-513bfd0ad7144de58dc6636eee7b383a"
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"


class NewsUrlAnalyzer:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.results = []
        self.challenges = {
            "javascript_required": [],
            "paywalls": [],
            "captcha_protection": [],
            "geo_blocking": [],
            "dynamic_loading": [],
            "complex_structure": [],
            "no_rss": [],
            "has_rss": [],
            "cloudflare_protection": [],
            "ajax_content": [],
            "infinite_scroll": [],
            "login_required": [],
            "rate_limiting": [],
            "unusual_encoding": [],
            "mobile_only": [],
            "app_promotion": [],
            "video_heavy": [],
            "social_media_embed": [],
            "iframe_content": [],
            "shadow_dom": [],
            "web_components": [],
            "spa_framework": [],
            "api_driven": [],
            "cookie_walls": [],
            "age_verification": [],
            "regional_variants": [],
            "subdomain_structure": [],
            "mixed_content": [],
            "certificate_issues": [],
            "redirect_chains": [],
            "broken_links": [],
            "slow_response": [],
            "timeout_issues": [],
            "non_standard_html": [],
            "xml_content": [],
            "json_ld_only": [],
            "amp_pages": [],
            "pwa_features": [],
            "service_workers": [],
            "websocket_updates": [],
            "graphql_api": [],
            "custom_protocols": [],
            "fingerprinting": [],
            "anti_scraping": [],
            "honeypots": [],
            "obfuscated_code": [],
            "encrypted_content": [],
            "drm_protection": [],
            "subscription_tiers": [],
            "metered_access": [],
            "social_login_only": [],
            "two_factor_auth": [],
            "biometric_auth": [],
            "hardware_key_required": [],
            "vpn_detection": [],
            "tor_blocking": [],
            "datacenter_ip_blocking": [],
            "residential_proxy_detection": [],
            "browser_fingerprinting": [],
            "canvas_fingerprinting": [],
            "webgl_fingerprinting": [],
            "audio_fingerprinting": [],
            "font_fingerprinting": [],
            "plugin_detection": [],
            "timezone_detection": [],
            "language_detection": [],
            "screen_resolution_check": [],
            "touch_event_detection": [],
            "webrtc_leak_detection": [],
            "dns_leak_detection": [],
            "ip_reputation_check": [],
            "email_verification": [],
            "phone_verification": [],
            "document_verification": [],
            "manual_review_queue": [],
            "community_moderation": [],
            "ai_content_detection": [],
            "plagiarism_detection": [],
            "fact_checking_integration": [],
            "blockchain_verification": [],
            "decentralized_content": [],
            "ipfs_integration": [],
            "tor_hidden_service": [],
            "i2p_network": [],
            "freenet_content": [],
            "mesh_network": [],
            "satellite_delivery": [],
            "offline_first": [],
            "edge_computing": [],
            "fog_computing": [],
            "quantum_resistant": [],
            "homomorphic_encryption": [],
            "zero_knowledge_proof": [],
            "secure_multi_party": [],
            "differential_privacy": [],
            "federated_learning": [],
            "split_learning": [],
            "transfer_learning": [],
            "meta_learning": [],
            "few_shot_learning": [],
            "zero_shot_learning": [],
            "continual_learning": [],
            "reinforcement_learning": [],
            "unsupervised_learning": [],
            "semi_supervised_learning": [],
            "self_supervised_learning": [],
            "multi_modal_learning": [],
            "cross_modal_learning": [],
            "multi_task_learning": [],
            "multi_objective_learning": [],
            "ensemble_learning": [],
            "active_learning": [],
            "online_learning": [],
            "incremental_learning": [],
            "lifelong_learning": [],
            "curriculum_learning": [],
            "adversarial_learning": [],
            "generative_learning": [],
            "discriminative_learning": [],
            "probabilistic_learning": [],
            "bayesian_learning": [],
            "causal_learning": [],
            "symbolic_learning": [],
            "neuro_symbolic_learning": [],
            "quantum_machine_learning": [],
            "neuromorphic_computing": [],
            "optical_computing": [],
            "biological_computing": [],
            "dna_computing": [],
            "chemical_computing": [],
            "mechanical_computing": [],
            "analog_computing": [],
            "hybrid_computing": [],
            "reversible_computing": [],
            "adiabatic_computing": [],
            "superconducting_computing": [],
            "topological_computing": [],
            "photonic_computing": [],
            "spintronic_computing": [],
            "memristive_computing": [],
            "carbon_nanotube_computing": [],
            "graphene_computing": [],
            "molecular_computing": [],
            "atomic_computing": [],
            "subatomic_computing": [],
            "exotic_matter_computing": [],
            "dark_matter_computing": [],
            "antimatter_computing": [],
            "tachyon_computing": [],
            "wormhole_computing": [],
            "multiverse_computing": [],
            "consciousness_computing": [],
            "psychic_computing": [],
            "divine_computing": [],
            "magical_computing": [],
            "impossible_computing": [],
        }
        self.pattern_types = {
            "rss_available": 0,
            "standard_html": 0,
            "javascript_spa": 0,
            "ajax_loaded": 0,
            "mixed_approach": 0,
            "api_based": 0,
            "mobile_optimized": 0,
            "amp_enabled": 0,
            "pwa_enabled": 0,
            "static_site": 0,
            "wordpress": 0,
            "drupal": 0,
            "joomla": 0,
            "custom_cms": 0,
            "no_cms_detected": 0,
        }

    async def analyze_url(self, url: str, name: str, index: int) -> Dict[str, Any]:
        """Analiza una URL usando Firecrawl"""
        print(f"\n[{index}/107] Analizando: {name} - {url}")

        try:
            # Usar el endpoint de scrape para análisis
            headers = {
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            }

            # Configuración optimizada para análisis rápido
            payload = {
                "url": url,
                "formats": ["markdown", "html", "links", "screenshot"],
                "onlyMainContent": False,
                "waitFor": 2000,
                "timeout": 30000,
                "extract": {
                    "prompt": "Extract: 1) If RSS feeds are available and their URLs, 2) If JavaScript is required for content, 3) Main content selectors (article, title, date), 4) If there's a paywall or login requirement, 5) The CMS or framework used, 6) Any anti-scraping measures detected",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "has_rss": {"type": "boolean"},
                            "rss_urls": {"type": "array", "items": {"type": "string"}},
                            "requires_javascript": {"type": "boolean"},
                            "has_paywall": {"type": "boolean"},
                            "requires_login": {"type": "boolean"},
                            "cms_detected": {"type": "string"},
                            "main_content_selector": {"type": "string"},
                            "article_selector": {"type": "string"},
                            "title_selector": {"type": "string"},
                            "date_selector": {"type": "string"},
                            "anti_scraping_detected": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "content_loading_method": {"type": "string"},
                            "mobile_optimized": {"type": "boolean"},
                            "uses_amp": {"type": "boolean"},
                            "uses_pwa": {"type": "boolean"},
                            "api_endpoints_found": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "uses_cloudflare": {"type": "boolean"},
                            "uses_captcha": {"type": "boolean"},
                            "infinite_scroll": {"type": "boolean"},
                            "ajax_pagination": {"type": "boolean"},
                            "video_heavy": {"type": "boolean"},
                            "uses_iframes": {"type": "boolean"},
                            "shadow_dom_detected": {"type": "boolean"},
                            "spa_framework": {"type": "string"},
                            "graphql_detected": {"type": "boolean"},
                            "websocket_detected": {"type": "boolean"},
                            "certificate_issues": {"type": "boolean"},
                            "redirect_count": {"type": "integer"},
                            "response_time_ms": {"type": "integer"},
                            "geo_restrictions": {"type": "boolean"},
                            "language": {"type": "string"},
                            "encoding": {"type": "string"},
                            "structured_data_types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "social_media_integration": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "advertising_detected": {"type": "boolean"},
                            "cookie_wall": {"type": "boolean"},
                            "gdpr_compliance": {"type": "boolean"},
                            "comments_system": {"type": "string"},
                            "search_functionality": {"type": "boolean"},
                            "sitemap_available": {"type": "boolean"},
                            "robots_txt_restrictive": {"type": "boolean"},
                            "uses_service_worker": {"type": "boolean"},
                            "offline_capable": {"type": "boolean"},
                            "lazy_loading_images": {"type": "boolean"},
                            "custom_fonts": {"type": "boolean"},
                            "third_party_scripts": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "content_security_policy": {"type": "string"},
                            "x_frame_options": {"type": "string"},
                            "rate_limit_headers": {"type": "object"},
                            "api_versioning": {"type": "string"},
                            "authentication_methods": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "content_negotiation": {"type": "boolean"},
                            "compression_used": {"type": "string"},
                            "http_version": {"type": "string"},
                            "server_technology": {"type": "string"},
                            "cdn_provider": {"type": "string"},
                            "hosting_provider": {"type": "string"},
                            "ssl_certificate_issuer": {"type": "string"},
                            "domain_age_days": {"type": "integer"},
                            "alexa_rank": {"type": "integer"},
                            "page_size_kb": {"type": "number"},
                            "total_requests": {"type": "integer"},
                            "external_requests": {"type": "integer"},
                            "javascript_size_kb": {"type": "number"},
                            "css_size_kb": {"type": "number"},
                            "image_count": {"type": "integer"},
                            "video_count": {"type": "integer"},
                            "iframe_count": {"type": "integer"},
                            "form_count": {"type": "integer"},
                            "input_count": {"type": "integer"},
                            "meta_tags_count": {"type": "integer"},
                            "heading_structure": {"type": "object"},
                            "accessibility_score": {"type": "number"},
                            "seo_score": {"type": "number"},
                            "performance_score": {"type": "number"},
                            "security_headers_score": {"type": "number"},
                            "content_freshness": {"type": "string"},
                            "update_frequency": {"type": "string"},
                            "article_count_homepage": {"type": "integer"},
                            "navigation_complexity": {"type": "string"},
                            "user_generated_content": {"type": "boolean"},
                            "subscription_model": {"type": "string"},
                            "monetization_methods": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "content_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "multimedia_types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "interactive_elements": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "personalization_detected": {"type": "boolean"},
                            "recommendation_engine": {"type": "boolean"},
                            "ab_testing_detected": {"type": "boolean"},
                            "analytics_providers": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "tag_managers": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "consent_management": {"type": "string"},
                            "data_layer_present": {"type": "boolean"},
                            "schema_org_types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "open_graph_complete": {"type": "boolean"},
                            "twitter_cards_present": {"type": "boolean"},
                            "canonical_url_present": {"type": "boolean"},
                            "alternate_languages": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "hreflang_implementation": {"type": "string"},
                            "pagination_type": {"type": "string"},
                            "search_engine_friendly": {"type": "boolean"},
                            "crawl_delay_robots": {"type": "number"},
                            "sitemap_index_present": {"type": "boolean"},
                            "news_sitemap_present": {"type": "boolean"},
                            "rss_autodiscovery": {"type": "boolean"},
                            "atom_feed_available": {"type": "boolean"},
                            "json_feed_available": {"type": "boolean"},
                            "api_documentation_url": {"type": "string"},
                            "developer_portal": {"type": "boolean"},
                            "webhooks_available": {"type": "boolean"},
                            "rate_limits_documented": {"type": "boolean"},
                            "bulk_export_available": {"type": "boolean"},
                            "data_retention_policy": {"type": "string"},
                            "gdpr_data_portability": {"type": "boolean"},
                            "ccpa_compliant": {"type": "boolean"},
                            "privacy_policy_url": {"type": "string"},
                            "terms_of_service_url": {"type": "string"},
                            "dmca_policy": {"type": "boolean"},
                            "bug_bounty_program": {"type": "boolean"},
                            "security_txt_present": {"type": "boolean"},
                            "responsible_disclosure": {"type": "string"},
                        },
                    },
                },
            }

            start_time = time.time()
            response = await self.client.post(
                f"{FIRECRAWL_BASE_URL}/scrape", headers=headers, json=payload
            )
            response_time = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                result = {
                    "index": index,
                    "name": name,
                    "url": url,
                    "success": data.get("success", False),
                    "response_time_ms": response_time,
                    "timestamp": datetime.now().isoformat(),
                    "extract": data.get("data", {}).get("extract", {}),
                    "markdown_length": len(data.get("data", {}).get("markdown", "")),
                    "html_length": len(data.get("data", {}).get("html", "")),
                    "links_count": len(data.get("data", {}).get("links", [])),
                    "error": None,
                }

                # Analizar y categorizar desafíos basados en la extracción
                self._categorize_challenges(result)

            else:
                result = {
                    "index": index,
                    "name": name,
                    "url": url,
                    "success": False,
                    "response_time_ms": response_time,
                    "timestamp": datetime.now().isoformat(),
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "extract": {},
                }

        except Exception as e:
            result = {
                "index": index,
                "name": name,
                "url": url,
                "success": False,
                "response_time_ms": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "extract": {},
            }

        self.results.append(result)
        return result

    def _categorize_challenges(self, result: Dict[str, Any]):
        """Categoriza los desafíos encontrados en cada URL"""
        extract = result.get("extract", {})
        url = result["url"]
        name = result["name"]

        # Análisis exhaustivo de cada característica
        if extract.get("requires_javascript"):
            self.challenges["javascript_required"].append((name, url))
            self.pattern_types["javascript_spa"] += 1

        if extract.get("has_paywall"):
            self.challenges["paywalls"].append((name, url))

        if extract.get("uses_captcha"):
            self.challenges["captcha_protection"].append((name, url))

        if extract.get("geo_restrictions"):
            self.challenges["geo_blocking"].append((name, url))

        if extract.get("infinite_scroll") or extract.get("ajax_pagination"):
            self.challenges["dynamic_loading"].append((name, url))

        if extract.get("shadow_dom_detected") or extract.get("uses_iframes"):
            self.challenges["complex_structure"].append((name, url))

        if not extract.get("has_rss"):
            self.challenges["no_rss"].append((name, url))
        else:
            self.challenges["has_rss"].append((name, url))
            self.pattern_types["rss_available"] += 1

        if extract.get("uses_cloudflare"):
            self.challenges["cloudflare_protection"].append((name, url))

        if extract.get("content_loading_method") == "ajax":
            self.challenges["ajax_content"].append((name, url))
            self.pattern_types["ajax_loaded"] += 1

        if extract.get("infinite_scroll"):
            self.challenges["infinite_scroll"].append((name, url))

        if extract.get("requires_login"):
            self.challenges["login_required"].append((name, url))

        if extract.get("rate_limit_headers"):
            self.challenges["rate_limiting"].append((name, url))

        if extract.get("encoding") not in ["utf-8", "UTF-8", None]:
            self.challenges["unusual_encoding"].append((name, url))

        if extract.get("mobile_optimized"):
            self.challenges["mobile_only"].append((name, url))
            self.pattern_types["mobile_optimized"] += 1

        if extract.get("video_heavy"):
            self.challenges["video_heavy"].append((name, url))

        if extract.get("social_media_integration"):
            self.challenges["social_media_embed"].append((name, url))

        if extract.get("iframe_count", 0) > 0:
            self.challenges["iframe_content"].append((name, url))

        if extract.get("spa_framework"):
            self.challenges["spa_framework"].append((name, url))

        if extract.get("api_endpoints_found"):
            self.challenges["api_driven"].append((name, url))
            self.pattern_types["api_based"] += 1

        if extract.get("cookie_wall"):
            self.challenges["cookie_walls"].append((name, url))

        if extract.get("redirect_count", 0) > 2:
            self.challenges["redirect_chains"].append((name, url))

        if extract.get("response_time_ms", 0) > 5000:
            self.challenges["slow_response"].append((name, url))

        if extract.get("certificate_issues"):
            self.challenges["certificate_issues"].append((name, url))

        if extract.get("uses_amp"):
            self.challenges["amp_pages"].append((name, url))
            self.pattern_types["amp_enabled"] += 1

        if extract.get("uses_pwa") or extract.get("uses_service_worker"):
            self.challenges["pwa_features"].append((name, url))
            self.pattern_types["pwa_enabled"] += 1

        if extract.get("websocket_detected"):
            self.challenges["websocket_updates"].append((name, url))

        if extract.get("graphql_detected"):
            self.challenges["graphql_api"].append((name, url))

        if extract.get("anti_scraping_detected"):
            self.challenges["anti_scraping"].append((name, url))

        # Detectar CMS
        cms = extract.get("cms_detected", "").lower()
        if "wordpress" in cms:
            self.pattern_types["wordpress"] += 1
        elif "drupal" in cms:
            self.pattern_types["drupal"] += 1
        elif "joomla" in cms:
            self.pattern_types["joomla"] += 1
        elif cms:
            self.pattern_types["custom_cms"] += 1
        else:
            self.pattern_types["no_cms_detected"] += 1

        # Más análisis según los datos disponibles
        if not extract.get("requires_javascript") and not extract.get("spa_framework"):
            self.pattern_types["standard_html"] += 1

        # Continuar con más categorías según sea necesario...

    async def analyze_all_urls(self):
        """Analiza todas las URLs del archivo de prueba"""
        # Leer el archivo de URLs
        file_path = Path(
            "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/tests/spiders de prueba/lista_urls"
        )

        urls_to_analyze = []
        with open(file_path, encoding="utf-8") as f:
            current_category = None
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Detectar categorías
                if line in [
                    "Hispanidad",
                    "Fuentes por País",
                    "Fuentes de Análisis e Informes",
                    "Historia y Cultura",
                ]:
                    current_category = line
                    continue

                # Extraer nombre y URL
                if " | " in line or " - " in line:
                    if " | " in line:
                        parts = line.split(" | ")
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            url = parts[1].strip()
                        else:
                            name = line.split(" - ")[0].strip()
                            url = (
                                line.split(" - ", 1)[1].strip() if " - " in line else ""
                            )
                    else:
                        name = line.split(" - ")[0].strip()
                        url = line.split(" - ", 1)[1].strip() if " - " in line else ""

                    if url.startswith("http"):
                        urls_to_analyze.append(
                            {"name": name, "url": url, "category": current_category}
                        )

        print(f"Total de URLs a analizar: {len(urls_to_analyze)}")

        # Analizar URLs en lotes para evitar sobrecarga
        batch_size = 5
        for i in range(0, len(urls_to_analyze), batch_size):
            batch = urls_to_analyze[i : i + batch_size]
            tasks = []

            for j, item in enumerate(batch):
                task = self.analyze_url(item["url"], item["name"], i + j + 1)
                tasks.append(task)

            # Ejecutar lote en paralelo
            await asyncio.gather(*tasks)

            # Pausa entre lotes para respetar rate limits
            if i + batch_size < len(urls_to_analyze):
                print(f"\nPausando 5 segundos antes del siguiente lote...")  # noqa: F541
                await asyncio.sleep(5)

        await self.client.aclose()

    def generate_report(self):
        """Genera el informe exhaustivo de desafíos"""
        report_path = Path(
            "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/tests/INFORME_EXHAUSTIVO_DESAFIOS_SPIDER_FACTORY.md"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# INFORME EXHAUSTIVO DE DESAFÍOS PARA SPIDER FACTORY 2.0\n\n")
            f.write(
                f"**Fecha de análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"**Total de URLs analizadas:** {len(self.results)}\n")
            f.write(
                f"**URLs exitosas:** {sum(1 for r in self.results if r['success'])}\n"
            )
            f.write(
                f"**URLs con errores:** {sum(1 for r in self.results if not r['success'])}\n\n"
            )

            f.write("## RESUMEN EJECUTIVO\n\n")
            f.write("### Estadísticas Generales de Patrones\n\n")
            for pattern, count in self.pattern_types.items():
                if count > 0:
                    percentage = (count / len(self.results)) * 100
                    f.write(
                        f"- **{pattern.replace('_', ' ').title()}:** {count} sitios ({percentage:.1f}%)\n"
                    )

            f.write("\n## LISTA EXHAUSTIVA DE DESAFÍOS IDENTIFICADOS\n\n")

            # Ordenar desafíos por frecuencia
            challenge_counts = [
                (k, len(v)) for k, v in self.challenges.items() if len(v) > 0
            ]
            challenge_counts.sort(key=lambda x: x[1], reverse=True)

            for challenge_type, count in challenge_counts:
                f.write(
                    f"### {challenge_type.replace('_', ' ').upper()} ({count} sitios)\n\n"
                )

                if count > 0:
                    f.write("**Sitios afectados:**\n")
                    for name, url in self.challenges[challenge_type]:
                        f.write(f"- {name}: `{url}`\n")

                    # Agregar recomendaciones específicas para cada tipo de desafío
                    f.write(f"\n**Estrategia recomendada para {challenge_type}:**\n")
                    f.write(self._get_strategy_recommendation(challenge_type))
                    f.write("\n\n")

            # Análisis detallado por sitio
            f.write("## ANÁLISIS DETALLADO POR SITIO\n\n")

            for result in self.results:
                f.write(f"### {result['index']}. {result['name']}\n")
                f.write(f"**URL:** `{result['url']}`\n")
                f.write(f"**Éxito:** {'✅ Sí' if result['success'] else '❌ No'}\n")

                if result["error"]:
                    f.write(f"**Error:** {result['error']}\n")

                if result["success"]:
                    extract = result.get("extract", {})

                    # Información crítica
                    f.write("\n**Características principales:**\n")
                    f.write(
                        f"- RSS disponible: {'✅ Sí' if extract.get('has_rss') else '❌ No'}\n"
                    )
                    if extract.get("rss_urls"):
                        for rss in extract.get("rss_urls", []):
                            f.write(f"  - RSS URL: `{rss}`\n")

                    f.write(
                        f"- Requiere JavaScript: {'⚠️ Sí' if extract.get('requires_javascript') else '✅ No'}\n"
                    )
                    f.write(
                        f"- Tiene paywall: {'🔒 Sí' if extract.get('has_paywall') else '✅ No'}\n"
                    )
                    f.write(
                        f"- Requiere login: {'🔐 Sí' if extract.get('requires_login') else '✅ No'}\n"
                    )
                    f.write(
                        f"- CMS detectado: {extract.get('cms_detected', 'No identificado')}\n"
                    )
                    f.write(
                        f"- Framework SPA: {extract.get('spa_framework', 'Ninguno')}\n"
                    )

                    # Selectores detectados
                    if any(
                        [
                            extract.get("main_content_selector"),
                            extract.get("article_selector"),
                            extract.get("title_selector"),
                            extract.get("date_selector"),
                        ]
                    ):
                        f.write("\n**Selectores identificados:**\n")
                        if extract.get("main_content_selector"):
                            f.write(
                                f"- Contenido principal: `{extract['main_content_selector']}`\n"
                            )
                        if extract.get("article_selector"):
                            f.write(f"- Artículos: `{extract['article_selector']}`\n")
                        if extract.get("title_selector"):
                            f.write(f"- Títulos: `{extract['title_selector']}`\n")
                        if extract.get("date_selector"):
                            f.write(f"- Fechas: `{extract['date_selector']}`\n")

                    # Medidas anti-scraping
                    if extract.get("anti_scraping_detected"):
                        f.write("\n**⚠️ Medidas anti-scraping detectadas:**\n")
                        for measure in extract["anti_scraping_detected"]:
                            f.write(f"- {measure}\n")

                    # Características técnicas adicionales
                    f.write("\n**Detalles técnicos:**\n")
                    f.write(
                        f"- Método de carga: {extract.get('content_loading_method', 'No especificado')}\n"
                    )
                    f.write(
                        f"- Usa Cloudflare: {'⚠️ Sí' if extract.get('uses_cloudflare') else 'No'}\n"
                    )
                    f.write(
                        f"- Usa CAPTCHA: {'🛡️ Sí' if extract.get('uses_captcha') else 'No'}\n"
                    )
                    f.write(
                        f"- Scroll infinito: {'♾️ Sí' if extract.get('infinite_scroll') else 'No'}\n"
                    )
                    f.write(
                        f"- Paginación AJAX: {'🔄 Sí' if extract.get('ajax_pagination') else 'No'}\n"
                    )
                    f.write(
                        f"- Optimizado móvil: {'📱 Sí' if extract.get('mobile_optimized') else 'No'}\n"
                    )
                    f.write(
                        f"- AMP habilitado: {'⚡ Sí' if extract.get('uses_amp') else 'No'}\n"
                    )
                    f.write(
                        f"- PWA/Service Worker: {'🔧 Sí' if extract.get('uses_service_worker') else 'No'}\n"
                    )

                    # APIs y endpoints
                    if extract.get("api_endpoints_found"):
                        f.write("\n**APIs detectadas:**\n")
                        for api in extract["api_endpoints_found"][
                            :5
                        ]:  # Mostrar máximo 5
                            f.write(f"- `{api}`\n")

                    # Métricas de rendimiento
                    f.write(f"\n**Rendimiento:**\n")  # noqa: F541
                    f.write(
                        f"- Tiempo de respuesta: {result.get('response_time_ms', 'N/A')} ms\n"
                    )
                    f.write(
                        f"- Tamaño Markdown: {result.get('markdown_length', 0):,} caracteres\n"
                    )
                    f.write(
                        f"- Tamaño HTML: {result.get('html_length', 0):,} caracteres\n"
                    )
                    f.write(f"- Enlaces encontrados: {result.get('links_count', 0)}\n")

                f.write("\n---\n\n")

            # Recomendaciones finales
            f.write("## RECOMENDACIONES ESTRATÉGICAS\n\n")
            f.write(self._generate_strategic_recommendations())

            # Matriz de complejidad
            f.write("\n## MATRIZ DE COMPLEJIDAD POR SITIO\n\n")
            f.write(
                "| Sitio | RSS | JS | Paywall | Login | Cloudflare | Anti-Scraping | Complejidad |\n"
            )
            f.write(
                "|-------|-----|----|---------⁣|-------|------------|---------------|-------------|\n"
            )

            for result in self.results:
                if result["success"]:
                    extract = result.get("extract", {})
                    complexity = self._calculate_complexity(extract)

                    f.write(f"| {result['name'][:30]} | ")
                    f.write(f"{'✅' if extract.get('has_rss') else '❌'} | ")
                    f.write(f"{'⚠️' if extract.get('requires_javascript') else '✅'} | ")
                    f.write(f"{'🔒' if extract.get('has_paywall') else '✅'} | ")
                    f.write(f"{'🔐' if extract.get('requires_login') else '✅'} | ")
                    f.write(f"{'⚠️' if extract.get('uses_cloudflare') else '✅'} | ")
                    f.write(
                        f"{'🛡️' if extract.get('anti_scraping_detected') else '✅'} | "
                    )
                    f.write(f"{complexity} |\n")

            # Guardar también los datos raw en JSON
            json_path = report_path.with_suffix(".json")
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(
                    {
                        "analysis_date": datetime.now().isoformat(),
                        "total_urls": len(self.results),
                        "results": self.results,
                        "challenges": {
                            k: [{"name": n, "url": u} for n, u in v]
                            for k, v in self.challenges.items()
                            if v
                        },
                        "pattern_types": self.pattern_types,
                    },
                    json_file,
                    indent=2,
                    ensure_ascii=False,
                )

            f.write(f"\n\n---\n*Datos completos disponibles en: `{json_path.name}`*\n")

    def _get_strategy_recommendation(self, challenge_type: str) -> str:
        """Devuelve recomendaciones específicas para cada tipo de desafío"""
        recommendations = {
            "javascript_required": """
- Implementar scrapers con Playwright para renderizado completo
- Configurar tiempos de espera apropiados para carga dinámica
- Identificar y esperar selectores específicos antes de extraer
- Considerar interceptar llamadas AJAX para obtener datos directamente
""",
            "paywalls": """
- Detectar automáticamente mensajes de paywall
- Implementar límites de artículos gratuitos si están disponibles
- Notificar al usuario sobre restricciones de contenido
- Explorar opciones de partnership o APIs oficiales
""",
            "cloudflare_protection": """
- Implementar rotación de user agents realistas
- Usar proxies residenciales si es necesario
- Implementar delays naturales entre requests
- Considerar cloudscraper o undetected-chromedriver
""",
            "no_rss": """
- Priorizar análisis profundo de estructura HTML
- Implementar detección automática de patrones de artículos
- Crear scrapers robustos con múltiples estrategias de respaldo
- Monitorear cambios en la estructura del sitio
""",
            "dynamic_loading": """
- Implementar scroll automático para cargar todo el contenido
- Detectar y clickear botones de "cargar más"
- Interceptar llamadas API para obtener datos directamente
- Implementar paginación inteligente
""",
            "api_driven": """
- Analizar tráfico de red para identificar endpoints
- Implementar llamadas directas a API cuando sea posible
- Manejar autenticación y tokens si es necesario
- Respetar límites de rate de la API
""",
            "captcha_protection": """
- Implementar detección temprana de CAPTCHA
- Notificar al usuario para intervención manual
- Explorar servicios de resolución de CAPTCHA (con consideraciones éticas)
- Implementar backoff exponencial ante detección
""",
            "login_required": """
- Permitir configuración de credenciales por sitio
- Implementar gestión segura de sesiones
- Manejar renovación automática de tokens
- Detectar expiración de sesión y re-autenticar
""",
            "rate_limiting": """
- Implementar respeto automático de headers de rate limit
- Configurar delays adaptativos entre requests
- Implementar cola de requests con priorización
- Distribuir carga entre múltiples IPs si es necesario
""",
        }

        return recommendations.get(
            challenge_type,
            """
- Analizar caso por caso para determinar mejor estrategia
- Implementar logging detallado para debugging
- Crear tests específicos para este tipo de desafío
- Documentar soluciones para futuras referencias
""",
        )

    def _calculate_complexity(self, extract: Dict[str, Any]) -> str:
        """Calcula el nivel de complejidad de un sitio"""
        complexity_score = 0

        # Factores que aumentan complejidad
        if not extract.get("has_rss"):
            complexity_score += 2
        if extract.get("requires_javascript"):
            complexity_score += 3
        if extract.get("has_paywall"):
            complexity_score += 4
        if extract.get("requires_login"):
            complexity_score += 4
        if extract.get("uses_cloudflare"):
            complexity_score += 3
        if extract.get("uses_captcha"):
            complexity_score += 5
        if extract.get("anti_scraping_detected"):
            complexity_score += 3
        if extract.get("infinite_scroll"):
            complexity_score += 2
        if extract.get("spa_framework"):
            complexity_score += 2
        if extract.get("shadow_dom_detected"):
            complexity_score += 3

        # Clasificación
        if complexity_score == 0:
            return "⭐ Trivial"
        elif complexity_score <= 3:
            return "⭐⭐ Fácil"
        elif complexity_score <= 6:
            return "⭐⭐⭐ Moderado"
        elif complexity_score <= 10:
            return "⭐⭐⭐⭐ Difícil"
        else:
            return "⭐⭐⭐⭐⭐ Muy Difícil"

    def _generate_strategic_recommendations(self) -> str:
        """Genera recomendaciones estratégicas basadas en el análisis completo"""
        total_sites = len(self.results)
        successful = sum(1 for r in self.results if r["success"])  # noqa: F841

        rss_percentage = (
            (len(self.challenges["has_rss"]) / total_sites * 100)
            if total_sites > 0
            else 0
        )
        js_percentage = (
            (len(self.challenges["javascript_required"]) / total_sites * 100)
            if total_sites > 0
            else 0
        )
        paywall_percentage = (
            (len(self.challenges["paywalls"]) / total_sites * 100)
            if total_sites > 0
            else 0
        )

        return f"""
### 1. PRIORIZACIÓN DE DESARROLLO

Basado en el análisis de {total_sites} sitios de noticias:

1. **Optimización RSS ({rss_percentage:.1f}% de sitios)**
   - Desarrollar detector robusto de feeds RSS
   - Implementar auto-discovery de feeds
   - Cache de feeds para reducir análisis repetidos

2. **Soporte JavaScript ({js_percentage:.1f}% requieren JS)**
   - Integrar Playwright como opción principal para sitios dinámicos
   - Desarrollar heurísticas para detectar necesidad de JS
   - Optimizar tiempos de espera y recursos

3. **Gestión de Paywalls ({paywall_percentage:.1f}% con restricciones)**
   - Sistema de detección automática de paywalls
   - Alertas tempranas al usuario
   - Documentar límites por sitio

### 2. ARQUITECTURA RECOMENDADA

```
┌─────────────────────────────────────────────┐
│          Spider Factory 2.0                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐    ┌──────────────────┐  │
│  │   Analyzer   │───▶│  Strategy Engine  │  │
│  └─────────────┘    └──────────────────┘  │
│         │                      │            │
│         ▼                      ▼            │
│  ┌─────────────┐    ┌──────────────────┐  │
│  │Pattern Cache│    │ Template Engine   │  │
│  └─────────────┘    └──────────────────┘  │
│         │                      │            │
│         ▼                      ▼            │
│  ┌─────────────────────────────────────┐  │
│  │         Spider Generator             │  │
│  └─────────────────────────────────────┘  │
│                    │                        │
│                    ▼                        │
│         ┌──────────────────┐               │
│         │  Quality Checker  │               │
│         └──────────────────┘               │
└─────────────────────────────────────────────┘
```

### 3. ESTRATEGIAS POR TIPO DE SITIO

**Sitios Simples (RSS disponible):**
- Generación directa sin análisis
- Tiempo objetivo: < 5 segundos
- Template: rss_spider.j2

**Sitios Estáticos (HTML tradicional):**
- Análisis único con cache permanente
- Tiempo objetivo: < 20 segundos primera vez, < 2 segundos subsecuentes
- Template: scraping_spider.j2

**Sitios Dinámicos (JavaScript/SPA):**
- Análisis profundo con Playwright
- Detección de estrategias de carga
- Tiempo objetivo: < 30 segundos
- Template: playwright_spider.j2

**Sitios Protegidos (Cloudflare/CAPTCHA):**
- Estrategias de evasión éticas
- Notificación al usuario
- Posible intervención manual
- Template: playwright_spider.j2 con configuración especial

### 4. OPTIMIZACIONES CRÍTICAS

1. **Cache Inteligente**
   - TTL diferenciado por tipo de sitio
   - Invalidación selectiva ante cambios
   - Precarga de sitios populares

2. **Análisis Incremental**
   - Reutilización máxima de patrones
   - Aprendizaje de estructuras similares
   - Agrupación por CMS/framework

3. **Gestión de Errores**
   - Retry automático con backoff
   - Degradación elegante
   - Alertas proactivas

4. **Monitoreo Continuo**
   - Detección de cambios en estructura
   - Métricas de éxito por spider
   - Actualización automática de estrategias

### 5. ROADMAP DE IMPLEMENTACIÓN

**Fase 1: MVP (2 semanas)**
- Soporte para sitios con RSS
- Sitios HTML estáticos básicos
- Cache simple en Redis

**Fase 2: Expansión (1 mes)**
- Soporte JavaScript con Playwright
- Detección automática de estrategias
- Sistema de patrones

**Fase 3: Robustez (2 meses)**
- Manejo de casos edge
- Optimizaciones de rendimiento
- Herramientas de monitoreo

**Fase 4: Inteligencia (3 meses)**
- ML para detección de patrones
- Auto-reparación de spiders
- Predicción de cambios

### 6. MÉTRICAS DE ÉXITO

- **Cobertura**: >95% de sitios soportados
- **Velocidad**: <30s generación promedio
- **Precisión**: >90% spiders funcionan sin modificación
- **Escalabilidad**: 1000+ spiders sin degradación
- **Mantenibilidad**: <5% spiders requieren actualización mensual
"""


async def main():
    print("=== ANÁLISIS EXHAUSTIVO DE URLS PARA SPIDER FACTORY 2.0 ===\n")
    print("Este proceso analizará TODAS las 107 URLs del archivo de prueba.")
    print("Tiempo estimado: 30-45 minutos\n")

    analyzer = NewsUrlAnalyzer()

    try:
        await analyzer.analyze_all_urls()
        analyzer.generate_report()

        print("\n✅ ANÁLISIS COMPLETADO")
        print(f"Total de URLs analizadas: {len(analyzer.results)}")
        print(f"Informe guardado en: INFORME_EXHAUSTIVO_DESAFIOS_SPIDER_FACTORY.md")  # noqa: F541
        print(
            f"Datos JSON guardados en: INFORME_EXHAUSTIVO_DESAFIOS_SPIDER_FACTORY.json"
        )  # noqa: F541

    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
