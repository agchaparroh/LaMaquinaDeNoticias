#!/usr/bin/env python3
"""
Module Connector - Bridge between module_scraper and module_pipeline

This module monitors a directory for new .json.gz files containing articles,
validates them, and sends them to the Pipeline API for processing.
"""

import asyncio
import os
import shutil
import sys
import json
import gzip
from typing import List, Dict, Any, Tuple
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from config import (
    SCRAPER_OUTPUT_DIR, 
    PIPELINE_PENDING_DIR, 
    PIPELINE_COMPLETED_DIR,
    PIPELINE_ERROR_DIR,
    POLLING_INTERVAL,
    PIPELINE_API_URL,
    MAX_RETRIES,
    RETRY_BACKOFF,
    LOG_LEVEL, 
    ENABLE_SENTRY, 
    SENTRY_DSN
)
from models import ArticuloInItem, prepare_articulo


def setup_logging():
    """Configure loguru logging"""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=LOG_LEVEL
    )
    
    # Add file handler
    logger.add(
        "logs/connector.log",
        rotation="10 MB",
        retention="1 week", 
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}"
    )


def setup_sentry():
    """Configure Sentry error reporting if enabled"""
    if ENABLE_SENTRY and SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=SENTRY_DSN)
            logger.info("Sentry error reporting enabled")
        except ImportError:
            logger.warning("Sentry SDK not installed, error reporting disabled")


async def monitor_directory():
    """Monitor the scraper output directory for new .json.gz files"""
    logger.info(f"Starting to monitor directory: {SCRAPER_OUTPUT_DIR}")
    
    # Ensure target directories exist
    os.makedirs(SCRAPER_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PIPELINE_PENDING_DIR, exist_ok=True)
    os.makedirs(PIPELINE_COMPLETED_DIR, exist_ok=True)
    os.makedirs(PIPELINE_ERROR_DIR, exist_ok=True)
    
    logger.info(f"Directory structure verified:")
    logger.info(f"  - Input: {SCRAPER_OUTPUT_DIR}")
    logger.info(f"  - Pending: {PIPELINE_PENDING_DIR}")
    logger.info(f"  - Completed: {PIPELINE_COMPLETED_DIR}")
    logger.info(f"  - Error: {PIPELINE_ERROR_DIR}")
    logger.info(f"Polling interval: {POLLING_INTERVAL} seconds")
    
    while True:
        try:
            # Check if input directory exists and is accessible
            if not os.path.exists(SCRAPER_OUTPUT_DIR):
                logger.warning(f"Input directory does not exist: {SCRAPER_OUTPUT_DIR}")
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            
            # List all .json.gz files in the directory
            files = []
            try:
                all_files = os.listdir(SCRAPER_OUTPUT_DIR)
                files = [f for f in all_files 
                        if f.endswith('.json.gz') and 
                        os.path.isfile(os.path.join(SCRAPER_OUTPUT_DIR, f))]
            except PermissionError:
                logger.error(f"Permission denied accessing {SCRAPER_OUTPUT_DIR}")
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            except Exception as e:
                logger.error(f"Error listing directory {SCRAPER_OUTPUT_DIR}: {e}")
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            
            if files:
                logger.info(f"Found {len(files)} .json.gz file(s): {files}")
            
            for file_name in files:
                source_path = os.path.join(SCRAPER_OUTPUT_DIR, file_name)
                dest_path = os.path.join(PIPELINE_PENDING_DIR, file_name)
                
                try:
                    # Move file to pending directory
                    logger.info(f"Moving file {file_name} to pending directory")
                    shutil.move(source_path, dest_path)
                    logger.info(f"File moved successfully: {file_name}")
                    
                    # Process the file
                    logger.info(f"Processing file: {file_name}")
                    valid_articles, invalid_articles, has_valid = await process_file(dest_path)
                    
                    if has_valid:
                        logger.info(f"File {file_name} processed successfully with {len(valid_articles)} valid articles")
                        
                        # Send articles to Pipeline API
                        success_count, failure_count = await send_articles_to_pipeline(valid_articles)
                        
                        # Determine overall success for file movement
                        file_success = success_count > 0
                        
                        # Move file based on results
                        await move_file(dest_path, file_success)
                        
                        if success_count > 0:
                            logger.info(f"Successfully sent {success_count} articles to Pipeline API")
                        
                        if failure_count > 0:
                            logger.warning(f"Failed to send {failure_count} articles to Pipeline API")
                    else:
                        logger.warning(f"File {file_name} contains no valid articles")
                        if invalid_articles:
                            logger.warning(f"Found {len(invalid_articles)} invalid articles in file")
                        
                        # Move to error directory since no valid articles
                        await move_file(dest_path, False)
                    
                except FileNotFoundError:
                    logger.warning(f"File {file_name} disappeared before processing")
                    continue
                except PermissionError:
                    logger.error(f"Permission denied moving file {file_name}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing file {file_name}: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Unexpected error in monitor loop: {str(e)}")
        
        # Wait for the next polling interval
        await asyncio.sleep(POLLING_INTERVAL)


async def process_file(file_path: str) -> Tuple[List[ArticuloInItem], List[Dict[str, Any]], bool]:
    """
    Process a .json.gz file containing article data
    
    Args:
        file_path: Path to the .json.gz file to process
        
    Returns:
        Tuple containing:
        - List of valid articles (ArticuloInItem instances)
        - List of invalid articles with errors (dict with 'data' and 'error' keys)
        - Boolean indicating if any articles were valid
    """
    valid_articles = []
    invalid_articles = []
    
    try:
        logger.info(f"Processing file: {os.path.basename(file_path)}")
        
        # Verify file exists
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return [], [], False
        
        # Read and decompress the file
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Successfully read and decompressed file, size: {len(content)} characters")
        except gzip.BadGzipFile:
            logger.error(f"Invalid gzip file: {file_path}")
            return [], [], False
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error reading file {file_path}: {e}")
            return [], [], False
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return [], [], False
            
        # Parse JSON content
        try:
            data = json.loads(content)
            logger.debug("Successfully parsed JSON content")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return [], [], False
        
        # Handle both single object and list of objects
        if isinstance(data, list):
            articles_data = data
            logger.info(f"Found list with {len(articles_data)} articles in file")
        elif isinstance(data, dict):
            articles_data = [data]
            logger.info("Found single article object in file")
        else:
            logger.error(f"Unexpected data type in JSON file: {type(data)}")
            return [], [], False
        
        # Validate each article
        for i, article_data in enumerate(articles_data):
            try:
                # Prepare and validate article using Pydantic model
                article = prepare_articulo(article_data)
                valid_articles.append(article)
                
                # Log with truncated title for readability
                title_preview = article.titular[:50] + "..." if len(article.titular) > 50 else article.titular
                logger.debug(f"✅ Validated article {i+1}: '{title_preview}'")
                
            except Exception as e:
                # Log validation errors with context
                logger.warning(f"❌ Validation error for article {i+1}: {str(e)}")
                
                # Try to get some identifying info for the error report
                try:
                    title_hint = article_data.get('titular', 'Unknown title')[:30]
                except:
                    title_hint = 'Unable to extract title'
                
                invalid_articles.append({
                    "index": i + 1,
                    "title_hint": title_hint,
                    "data": article_data,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
        
        # Summary logging
        total_articles = len(articles_data)
        valid_count = len(valid_articles)
        invalid_count = len(invalid_articles)
        
        logger.info(f"Processing complete: {valid_count}/{total_articles} articles valid, {invalid_count} invalid")
        
        if invalid_count > 0:
            logger.warning(f"File {os.path.basename(file_path)} contains {invalid_count} invalid articles")
        
        return valid_articles, invalid_articles, len(valid_articles) > 0
        
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_path}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return [], [], False


# Define which exceptions should trigger a retry
retryable_exceptions = (aiohttp.ClientError, aiohttp.ServerTimeoutError, aiohttp.ClientConnectorError)


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=RETRY_BACKOFF, min=1, max=60),
    retry=retry_if_exception_type(retryable_exceptions),
    reraise=True
)
async def send_to_pipeline(session: aiohttp.ClientSession, article: ArticuloInItem) -> bool:
    """
    Send an article to the Pipeline API with retry logic
    
    Args:
        session: aiohttp ClientSession for making the request
        article: ArticuloInItem instance to send
        
    Returns:
        Boolean indicating success (True) or failure (False)
    """
    endpoint = f"{PIPELINE_API_URL}/procesar"
    
    try:
        # Convert Pydantic model to dict
        article_dict = article.dict()
        payload = {"articulo": article_dict}
        
        # Log with article identifier
        article_id = getattr(article, 'id', 'unknown')
        title_preview = article.titular[:30] + "..." if len(article.titular) > 30 else article.titular
        logger.info(f"Sending article to pipeline: '{title_preview}' (ID: {article_id})")
        
        # Send POST request to Pipeline API
        async with session.post(
            endpoint, 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            status = response.status
            
            if status == 202:
                # Success - article accepted by pipeline
                logger.info(f"✅ Article successfully sent to pipeline (ID: {article_id})")
                return True
                
            elif status == 400:
                # Validation error - don't retry (permanent failure)
                try:
                    error_data = await response.json()
                    logger.error(f"❌ Pipeline validation error for article {article_id}: {error_data}")
                except:
                    error_text = await response.text()
                    logger.error(f"❌ Pipeline validation error for article {article_id}: {error_text}")
                return False
                
            elif status in [500, 503]:
                # Server error or service unavailable - will be retried by tenacity
                logger.warning(f"⚠️  Pipeline server error {status} for article {article_id} (will retry)")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=status,
                    message=f"Pipeline server error: {status}"
                )
                
            else:
                # Unexpected status - don't retry
                logger.error(f"❌ Unexpected response from pipeline for article {article_id}: {status}")
                return False
                
    except retryable_exceptions as e:
        # These exceptions will trigger retry via tenacity
        logger.warning(f"⚠️  Connection error for article {article_id} (will retry): {str(e)}")
        raise
        
    except aiohttp.ClientResponseError as e:
        # Server errors that should be retried
        if e.status in [500, 503]:
            logger.warning(f"⚠️  Server error {e.status} for article {article_id} (will retry)")
            raise
        else:
            logger.error(f"❌ Client error for article {article_id}: {e}")
            return False
            
    except Exception as e:
        # Non-retryable exceptions
        logger.error(f"❌ Unexpected error sending article {article_id} to pipeline: {str(e)}")
        return False


async def send_articles_to_pipeline(articles: List[ArticuloInItem]) -> Tuple[int, int]:
    """
    Send multiple articles to the Pipeline API
    
    Args:
        articles: List of ArticuloInItem instances to send
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    if not articles:
        logger.info("No articles to send to pipeline")
        return 0, 0
    
    success_count = 0
    failure_count = 0
    
    logger.info(f"Sending {len(articles)} articles to Pipeline API at {PIPELINE_API_URL}")
    
    # Create a shared session for all requests
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i, article in enumerate(articles, 1):
            try:
                logger.debug(f"Processing article {i}/{len(articles)}")
                success = await send_to_pipeline(session, article)
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                # Final fallback - count as failure
                logger.error(f"❌ Final failure sending article {i}: {e}")
                failure_count += 1
    
    # Summary logging
    total_articles = len(articles)
    success_rate = (success_count / total_articles * 100) if total_articles > 0 else 0
    
    if success_count > 0:
        logger.info(f"✅ Pipeline API results: {success_count}/{total_articles} articles sent successfully ({success_rate:.1f}%)")
    
    if failure_count > 0:
        logger.warning(f"❌ {failure_count}/{total_articles} articles failed to send ({(failure_count/total_articles*100):.1f}%)")
    
    return success_count, failure_count


async def move_file(file_path: str, success: bool) -> None:
    """
    Move a processed file to the appropriate directory based on processing result
    
    Args:
        file_path: Path to the file to move
        success: Whether processing was successful
    """
    try:
        # Get the filename from the path
        file_name = os.path.basename(file_path)
        
        # Verify source file exists
        if not os.path.exists(file_path):
            logger.error(f"📁 Source file does not exist: {file_path}")
            return
        
        # Determine destination directory
        if success:
            dest_dir = PIPELINE_COMPLETED_DIR
            logger.info(f"📋 Moving file to completed directory: {file_name}")
        else:
            dest_dir = PIPELINE_ERROR_DIR
            logger.warning(f"❌ Moving file to error directory: {file_name}")
        
        # Ensure destination directory exists
        os.makedirs(dest_dir, exist_ok=True)
        
        # Check if destination file already exists
        dest_path = os.path.join(dest_dir, file_name)
        if os.path.exists(dest_path):
            # Create a unique filename with timestamp
            import time
            timestamp = int(time.time())
            name, ext = os.path.splitext(file_name)
            unique_filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(dest_dir, unique_filename)
            logger.info(f"🔄 File exists, using unique name: {unique_filename}")
        
        # Move the file
        shutil.move(file_path, dest_path)
        logger.info(f"✅ File moved successfully: {file_name} -> {os.path.basename(dest_path)}")
        
    except PermissionError:
        logger.error(f"🚫 Permission denied moving file {file_path}")
    except OSError as e:
        logger.error(f"📁 OS error moving file {file_path}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error moving file {file_path}: {str(e)}")


async def process_pending_files() -> Tuple[int, int, int]:
    """
    Process all pending files in the PIPELINE_PENDING_DIR
    
    Returns:
        Tuple of (files_processed, files_succeeded, files_failed)
    """
    try:
        # Ensure directory exists
        os.makedirs(PIPELINE_PENDING_DIR, exist_ok=True)
        
        # List all .json.gz files in the pending directory
        files = []
        try:
            all_files = os.listdir(PIPELINE_PENDING_DIR)
            files = [f for f in all_files 
                    if f.endswith('.json.gz') and 
                    os.path.isfile(os.path.join(PIPELINE_PENDING_DIR, f))]
        except PermissionError:
            logger.error(f"🚫 Permission denied accessing {PIPELINE_PENDING_DIR}")
            return 0, 0, 0
        except Exception as e:
            logger.error(f"📁 Error listing pending directory: {e}")
            return 0, 0, 0
        
        if not files:
            logger.info("🗺 No pending files to process")
            return 0, 0, 0
        
        logger.info(f"📁 Found {len(files)} pending files to process")
        
        files_processed = 0
        files_succeeded = 0
        files_failed = 0
        
        for file_name in files:
            file_path = os.path.join(PIPELINE_PENDING_DIR, file_name)
            
            try:
                logger.info(f"🔄 Processing pending file: {file_name}")
                
                # Process the file
                valid_articles, invalid_articles, has_valid = await process_file(file_path)
                
                success = False
                
                if valid_articles:
                    # Send valid articles to pipeline
                    success_count, failure_count = await send_articles_to_pipeline(valid_articles)
                    
                    # Consider successful if at least one article was sent successfully
                    success = success_count > 0
                    
                    if success:
                        logger.info(f"✅ File {file_name}: {success_count}/{len(valid_articles)} articles sent successfully")
                    else:
                        logger.warning(f"❌ File {file_name}: All {len(valid_articles)} articles failed to send")
                else:
                    logger.warning(f"❌ File {file_name}: No valid articles found")
                
                # Move file to appropriate directory
                await move_file(file_path, success)
                
                # Update counters
                files_processed += 1
                if success:
                    files_succeeded += 1
                else:
                    files_failed += 1
                
                # Log processing summary
                total_articles = len(valid_articles) + len(invalid_articles)
                valid_count = len(valid_articles)
                invalid_count = len(invalid_articles)
                
                logger.info(f"📊 File {file_name} summary: {valid_count}/{total_articles} valid articles, {invalid_count} invalid")
                
            except Exception as e:
                logger.error(f"❌ Error processing pending file {file_name}: {e}")
                
                # Move to error directory on processing failure
                try:
                    await move_file(file_path, False)
                except:
                    pass  # Don't let move errors prevent continuing
                
                files_processed += 1
                files_failed += 1
        
        # Final summary
        success_rate = (files_succeeded / files_processed * 100) if files_processed > 0 else 0
        logger.info(f"🏁 Pending files processing complete: {files_succeeded}/{files_processed} successful ({success_rate:.1f}%)")
        
        return files_processed, files_succeeded, files_failed
        
    except Exception as e:
        logger.error(f"❌ Error in process_pending_files: {str(e)}")
        return 0, 0, 0


async def main():
    """Main async function - entry point that orchestrates the entire workflow"""
    setup_logging()
    setup_sentry()
    
    logger.info("🚀 Module Connector starting up...")
    logger.info(f"📊 Configuration:")
    logger.info(f"  - Input directory: {SCRAPER_OUTPUT_DIR}")
    logger.info(f"  - Pipeline API: {PIPELINE_API_URL}")
    logger.info(f"  - Polling interval: {POLLING_INTERVAL}s")
    logger.info(f"  - Max retries: {MAX_RETRIES}")
    
    try:
        # Process any existing pending files first
        logger.info("🔍 Checking for existing pending files...")
        files_processed, files_succeeded, files_failed = await process_pending_files()
        
        if files_processed > 0:
            logger.info(f"📋 Startup processing complete: {files_succeeded}/{files_processed} files successful")
        else:
            logger.info("✨ No pending files found, starting fresh")
        
        # Start monitoring for new files
        logger.info("👁️  Starting directory monitoring...")
        await monitor_directory()
        
    except KeyboardInterrupt:
        logger.info("⚠️  Received interrupt signal, shutting down gracefully...")
        return 0
    except Exception as e:
        logger.error(f"💥 Fatal error in main: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        logger.info("🛑 Module Connector shutting down...")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⚠️  Received interrupt signal, shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)
