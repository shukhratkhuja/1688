import os
import sys
import json
import time
import multiprocessing
from pathlib import Path

# Add paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ocr.pytsrct_ocr import is_text_present
from utils.db_utils import update_row
from utils.constants import DB_NAME, TABLE_PRODUCT_IMAGES, LOCAL_IMAGES_FOLDER, LOCAL_OUTPUT_FOLDER
from utils.log_config import get_logger

logger = get_logger("paddle_ocr", "app.log")

# Global PaddleOCR instance to avoid re-initialization
_paddleocr_instance = None
_ocr_lock = multiprocessing.Lock()


def get_paddleocr_instance():
    """Get or create PaddleOCR instance with crash protection"""
    global _paddleocr_instance
    
    if _paddleocr_instance is None:
        try:
            # Set environment variables for stability
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            os.environ['OPENBLAS_NUM_THREADS'] = '1'
            os.environ['MKL_NUM_THREADS'] = '1'
            
            # Import and create PaddleOCR with minimal configuration
            from paddleocr import PaddleOCR
            
            logger.info("Initializing PaddleOCR...")
            _paddleocr_instance = PaddleOCR(
                use_angle_cls=True, 
                lang='ch', 
                use_space_char=True,
                show_log=False,  # Disable verbose logging
                use_gpu=False,   # Force CPU usage for stability
                cpu_threads=1    # Single thread to avoid conflicts
            )
            logger.info("PaddleOCR initialized successfully")
            
        except Exception as e:
            logger.log_exception(e, "initializing PaddleOCR")
            raise
    
    return _paddleocr_instance


def extract_text_safe(image_path, timeout=60):
    """Extract text with timeout and crash protection"""
    try:
        # Check if text is present first (lightweight check)
        if not is_text_present(image_path=image_path):
            logger.info(f"No text detected in image: {image_path}")
            return None
        
        # Use multiprocessing to isolate PaddleOCR
        with multiprocessing.Pool(processes=1) as pool:
            try:
                result = pool.apply_async(extract_text_worker, (image_path,))
                text_list = result.get(timeout=timeout)
                return text_list
            except multiprocessing.TimeoutError:
                logger.warning(f"OCR timeout for image: {image_path}")
                pool.terminate()
                pool.join()
                return None
            except Exception as e:
                logger.warning(f"OCR process error for {image_path}: {e}")
                pool.terminate()
                pool.join()
                return None
                
    except Exception as e:
        logger.log_exception(e, f"OCR extraction for {image_path}")
        return None


def extract_text_worker(image_path):
    """Worker function for OCR extraction (runs in separate process)"""
    try:
        # Set environment variables in worker process
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        
        # Import in worker process
        from paddleocr import PaddleOCR
        
        # Create OCR instance in worker
        ocr = PaddleOCR(
            use_angle_cls=True, 
            lang='ch', 
            use_space_char=True,
            show_log=False,
            use_gpu=False,
            cpu_threads=1
        )
        
        # Perform OCR
        results = ocr.ocr(image_path, cls=True)
        
        # Process results
        text_list = []
        if results and results[0]:  # Check if results exist
            for line in results[0]:
                if line and len(line) >= 2:  # Check line structure
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    if text and len(text.strip()) > 0:
                        text_list.append(text.strip())
        
        return text_list
        
    except Exception as e:
        # Log error in worker process
        print(f"Worker OCR error: {e}")  # Use print since logger might not work in subprocess
        return None


def extract_text(image_path):
    """Main OCR function with fallback mechanisms"""
    try:
        logger.info(f"Starting OCR for: {image_path}")
        
        # Verify image exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Check file size (skip very large files)
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        if file_size > 50:  # Skip files larger than 50MB
            logger.warning(f"Skipping large image ({file_size:.1f}MB): {image_path}")
            return None
        
        # Try safe extraction with timeout
        text_list = extract_text_safe(image_path, timeout=60)
        
        if text_list:
            logger.info(f"OCR successful: extracted {len(text_list)} text lines")
            return text_list
        else:
            logger.info(f"No text extracted from: {image_path}")
            return None
            
    except Exception as e:
        logger.log_exception(e, f"OCR extraction for {image_path}")
        return None


def extract_line_by_line(image_path):
    """Extract text line by line with improved error handling"""
    try:
        # Make path absolute
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(image_path):
            image_path = os.path.join(base_dir, image_path)
        
        logger.info(f"Processing image: {image_path}")
        
        # Check if text is present (lightweight check first)
        if not is_text_present(image_path=image_path):
            logger.info("No text detected in image")
            return None
        
        # Extract text with crash protection
        text_list = extract_text(image_path)
        
        if text_list:
            # Process and clean text
            cleaned_lines = []
            for text in text_list:
                if text and len(text.strip()) > 0:
                    # Basic cleaning
                    cleaned_text = text.strip().replace('\n', ' ').replace('\r', ' ')
                    if len(cleaned_text) > 0:
                        cleaned_lines.append(cleaned_text)
            
            if cleaned_lines:
                logger.info(f"Extracted {len(cleaned_lines)} lines of text")
                return cleaned_lines
        
        logger.info("No valid text lines extracted")
        return None
        
    except Exception as e:
        logger.log_exception(e, f"line-by-line extraction for {image_path}")
        return None


def process_single_image(image_url, image_filename):
    """Process a single image with comprehensive error handling"""
    try:
        logger.info(f"Processing image: {image_filename}")
        
        # Build image path
        image_path = os.path.join(LOCAL_OUTPUT_FOLDER, LOCAL_IMAGES_FOLDER, image_filename)
        
        # Verify image exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            # Mark as processed even if file missing
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[("text_extracted_status", "1")],
                where=[("image_url", "=", image_url)]
            )
            return False
        
        # Extract text with timeout protection
        text_list = extract_line_by_line(image_path)
        
        # Prepare text for database
        if text_list:
            # Clean text for database storage
            cleaned_text_list = []
            for text in text_list:
                # Replace single quotes for SQL safety
                clean_text = text.replace("'", "''")
                cleaned_text_list.append(clean_text)
            
            # Update database with extracted text
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[
                    ("image_text", json.dumps(cleaned_text_list, ensure_ascii=False)),
                    ("text_extracted_status", "1")
                ],
                where=[("image_url", "=", image_url)]
            )
            logger.info(f"Successfully processed image: {image_filename}")
            
        else:
            # No text found, but mark as processed
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[("text_extracted_status", "1")],
                where=[("image_url", "=", image_url)]
            )
            logger.info(f"No text found in image: {image_filename}")
        
        return True
        
    except Exception as e:
        logger.log_exception(e, f"processing image {image_filename}")
        
        # Mark as processed even on error to avoid infinite retries
        try:
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[("text_extracted_status", "1")],
                where=[("image_url", "=", image_url)]
            )
        except Exception as db_error:
            logger.error(f"Failed to update database after OCR error: {db_error}")
        
        return False


def main(img_details):
    """Main OCR processing function with batch processing and error recovery"""
    try:
        logger.info(f"Starting OCR processing for {len(img_details)} images")
        
        if not img_details:
            logger.info("No images to process")
            return
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for i, (image_url, image_filename) in enumerate(img_details):
            try:
                logger.info(f"Processing image {i+1}/{len(img_details)}: {image_filename}")
                
                # Process single image with error isolation
                success = process_single_image(image_url, image_filename)
                
                processed_count += 1
                if success:
                    success_count += 1
                else:
                    error_count += 1
                
                # Small delay between images to prevent system overload
                time.sleep(0.5)
                
                # Progress logging
                if processed_count % 10 == 0:
                    logger.info(f"Progress: {processed_count}/{len(img_details)} images processed")
                
            except Exception as e:
                logger.log_exception(e, f"processing batch item {i+1}")
                error_count += 1
                
                # Continue with next image
                continue
        
        # Final summary
        logger.info(f"OCR processing completed:")
        logger.info(f"  Total processed: {processed_count}")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Errors: {error_count}")
        
    except Exception as e:
        logger.log_exception(e, "OCR main processing")
        raise


def cleanup_ocr_resources():
    """Cleanup OCR resources to prevent memory leaks"""
    global _paddleocr_instance
    
    try:
        if _paddleocr_instance is not None:
            # Clear the instance
            _paddleocr_instance = None
            logger.info("OCR resources cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up OCR resources: {e}")


def test_ocr_functionality():
    """Test OCR functionality with a simple check"""
    try:
        logger.info("Testing OCR functionality...")
        
        # Try to import PaddleOCR
        from paddleocr import PaddleOCR
        logger.info("PaddleOCR import successful")
        
        # Try to create instance
        ocr = PaddleOCR(
            use_angle_cls=False, 
            lang='ch', 
            show_log=False,
            use_gpu=False
        )
        logger.info("PaddleOCR instance created successfully")
        
        return True
        
    except Exception as e:
        logger.log_exception(e, "OCR functionality test")
        return False


# Graceful shutdown handler
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, cleaning up OCR resources...")
    cleanup_ocr_resources()
    sys.exit(0)


# Register signal handlers if running as main process
if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


# Alternative OCR function using Tesseract as fallback
def extract_text_tesseract_fallback(image_path):
    """Fallback OCR using Tesseract if PaddleOCR fails"""
    try:
        import pytesseract
        from PIL import Image
        
        logger.info(f"Using Tesseract fallback for: {image_path}")
        
        # Open image
        image = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        
        if text and len(text.strip()) > 0:
            # Split into lines and clean
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return lines
        
        return None
        
    except Exception as e:
        logger.warning(f"Tesseract fallback failed: {e}")
        return None


def extract_text_with_fallback(image_path):
    """Extract text with PaddleOCR and Tesseract fallback"""
    try:
        # Try PaddleOCR first
        text_list = extract_text(image_path)
        
        if text_list and len(text_list) > 0:
            return text_list
        
        # If PaddleOCR fails or returns no text, try Tesseract
        logger.info("Trying Tesseract fallback...")
        tesseract_result = extract_text_tesseract_fallback(image_path)
        
        if tesseract_result:
            logger.info("Tesseract fallback successful")
            return tesseract_result
        
        logger.info("Both OCR methods failed to extract text")
        return None
        
    except Exception as e:
        logger.log_exception(e, f"OCR with fallback for {image_path}")
        return None


# Export main functions
__all__ = [
    'main',
    'extract_text',
    'extract_line_by_line',
    'extract_text_with_fallback',
    'cleanup_ocr_resources',
    'test_ocr_functionality'
]