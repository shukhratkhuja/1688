"""
Worker Threads for background scraping operations - SIGNAL ISSUES FIXED
"""

import sys, os
import time
import threading
import signal
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

# Add project root to Python path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent

sys.path.insert(0, str(desktop_dir))  # For desktop_app modules
sys.path.insert(0, str(project_root)) # For original utils

from utils.log_config import get_logger
from main import main as go_main  # Importing main scraping function


class BaseWorkerThread(QThread):
    """Base worker thread with corrected signal definitions"""
    
    # Signals - CORRECTED: QThread.finished already exists with no arguments
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    status_updated = pyqtSignal(str)  # status_message
    error_occurred = pyqtSignal(str)  # error_message
    process_completed = pyqtSignal(bool)  # success - NEW SIGNAL instead of overriding finished
    
    def __init__(self, process_type, db_controller):
        super().__init__()
        self.process_type = process_type
        self.db_controller = db_controller
        self.logger = get_logger(f"worker_{process_type}", "app.log")
        
        # Control flags - IMPROVED
        self._should_stop = False
        self._is_running = False
        self._force_stop = False
        self._stop_lock = threading.Lock()
        
        # Progress tracking
        self._current_step = 0
        self._total_steps = 0
        self._last_progress_time = 0
    
    def stop_process(self):
        """Signal the worker to stop gracefully"""
        with self._stop_lock:
            self._should_stop = True
            self._force_stop = True
            
        self.logger.info(f"Stop signal sent to {self.process_type} worker")
        self.requestInterruption()
    
    def is_running(self):
        """Check if worker is currently running"""
        return self._is_running and not self._should_stop
    
    def should_continue(self):
        """Check if the worker should continue processing"""
        with self._stop_lock:
            return not (self._should_stop or self._force_stop or self.isInterruptionRequested())
    
    def emit_progress(self, current, total, message):
        """Emit progress update with throttling"""
        if not self.should_continue():
            return
            
        current_time = time.time()
        
        # Throttle progress updates (max once per second)
        if current_time - self._last_progress_time >= 1.0:
            self.progress_updated.emit(current, total, message)
            self._last_progress_time = current_time
    
    def emit_status(self, message):
        """Emit status update"""
        if not self.should_continue():
            return
            
        self.status_updated.emit(message)
        self.logger.info(f"Status: {message}")
    
    def emit_error(self, error_message):
        """Emit error signal"""
        self.error_occurred.emit(error_message)
        self.logger.error(f"Error: {error_message}")
    
    def run(self):
        """Main thread execution - to be overridden by subclasses"""
        self._is_running = True
        
        try:
            # Worker logic here
            while self.should_continue():
                # Processing work
                time.sleep(0.1)  # Check stop flag regularly
                
        except Exception as e:
            self.logger.error(f"Worker error: {e}")
            self.emit_error(str(e))
        finally:
            self._is_running = False
            # FIXED: Use our custom signal instead of overriding finished
            success = not (self._should_stop or self._force_stop)
            self.process_completed.emit(success)


class ScrapingWorkerThread(BaseWorkerThread):
    """Worker thread for new product scraping - SIGNAL FIXED"""
    
    def __init__(self, process_type, db_controller):
        super().__init__(process_type, db_controller)
        self.logger = get_logger("scraping_worker", "app.log")
        self._scraping_process = None
    
    def run(self):
        """Execute new product scraping with better control"""
        self._is_running = True
        success = False
        
        try:
            self.logger.info("Starting new product scraping process...")
            self.emit_status("Initializing scraping process...")
            
            # Check if we should stop before starting
            if not self.should_continue():
                self.logger.info("Stop requested before starting")
                return
            
            # Check initial state
            initial_stats = self.db_controller.get_processing_stats()
            total_products = initial_stats.get('total_products', 0)
            
            if total_products == 0:
                self.emit_status("No products found in database")
                self.logger.warning("No products to scrape")
                success = True  # Not an error, just nothing to do
                return
            
            self.emit_progress(0, total_products, "Starting scraping process...")
            
            # Start monitoring in a separate thread
            monitoring_thread = threading.Thread(target=self._monitor_scraping_progress, args=(total_products,))
            monitoring_thread.daemon = True
            monitoring_thread.start()
            
            # Run the actual scraping process with error protection
            try:
                self._run_scraping_process()
                success = True
            except Exception as e:
                self.logger.log_exception(e, "scraping process execution")
                success = False
            
            # Wait for monitoring to finish
            monitoring_thread.join(timeout=10)
            
            # Final status check
            if self.should_continue() and success:
                final_stats = self.db_controller.get_processing_stats()
                completed = final_stats.get('scraped', 0)
                
                success_message = f"Scraping completed! Processed {completed}/{total_products} products"
                self.emit_status(success_message)
                self.logger.info(success_message)
            elif not self.should_continue():
                self.emit_status("Scraping process was stopped")
                self.logger.info("Scraping process was stopped by user")
                success = False
            
        except Exception as e:
            error_msg = f"Scraping process failed: {str(e)}"
            self.emit_error(error_msg)
            self.logger.log_exception(e, "scraping worker")
            success = False
            
        finally:
            self._is_running = False
            # FIXED: Use custom signal
            self.process_completed.emit(success)
    
    def _run_scraping_process(self):
        """Run the actual scraping process with crash protection"""
        try:
            self.logger.info("Executing main scraping function...")
            
            # Store reference to current process for potential termination
            self._scraping_process = threading.current_thread()
            
            # Check if we should continue before running
            if not self.should_continue():
                self.logger.info("Cancelling scraping before execution")
                return
            
            # PROTECTION: Set environment variables for stability
            os.environ['PYTHONPATH'] = str(project_root)
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # For OpenMP issues
            
            # Execute main scraping function with timeout protection
            self._execute_with_timeout()
            
            self.logger.info("Main scraping function completed")
            
        except Exception as e:
            if self.should_continue():  # Only log as error if not stopped
                self.logger.log_exception(e, "running main scraping process")
                raise
            else:
                self.logger.info("Scraping process interrupted by stop signal")
    
    def _execute_with_timeout(self):
        """Execute main function with timeout protection"""
        import threading
        
        # Create a thread for the main function
        main_thread = threading.Thread(target=go_main)
        main_thread.daemon = True
        main_thread.start()
        
        # Monitor the thread
        while main_thread.is_alive() and self.should_continue():
            main_thread.join(timeout=5)  # Check every 5 seconds
        
        if main_thread.is_alive() and not self.should_continue():
            self.logger.info("Main process thread still running after stop signal")
            # Note: We can't force kill the thread, but we've stopped monitoring
    
    def _monitor_scraping_progress(self, total_products):
        """Monitor scraping progress and update UI"""
        start_time = time.time()
        last_completed = 0
        stall_counter = 0
        
        while self.should_continue():
            try:
                # Get current stats
                current_stats = self.db_controller.get_processing_stats()
                completed = current_stats.get('scraped', 0)
                
                # Calculate progress
                progress_message = f"Scraped {completed}/{total_products} products"
                self.emit_progress(completed, total_products, progress_message)
                
                # Check for completion
                if not current_stats.get('is_processing', True) and completed > 0:
                    self.logger.info("Scraping process appears to be complete")
                    break
                
                # Check for stalled progress
                if completed == last_completed:
                    stall_counter += 1
                    if stall_counter > 60:  # 60 * 5 seconds = 5 minutes stalled
                        if self.should_continue():
                            self.logger.warning("Scraping process appears stalled")
                            self.emit_status("Warning: Process may be stalled")
                else:
                    stall_counter = 0
                    last_completed = completed
                
                # Wait before next check
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                if self.should_continue():
                    self.logger.warning(f"Error monitoring progress: {e}")
                time.sleep(5)
        
        # Final progress update
        if self.should_continue():
            try:
                final_stats = self.db_controller.get_processing_stats()
                final_completed = final_stats.get('scraped', 0)
                final_message = f"Final status: {final_completed}/{total_products} products scraped"
                self.emit_progress(final_completed, total_products, final_message)
            except:
                pass


class RetakeWorkerThread(BaseWorkerThread):
    """Worker thread for retaking failed products - SIGNAL FIXED"""
    
    def __init__(self, process_type, db_controller, failed_products):
        super().__init__(process_type, db_controller)
        self.failed_products = failed_products
        self.logger = get_logger("retake_worker", "app.log")
        self._retake_process = None
    
    def run(self):
        """Execute retake process for failed products with better control"""
        self._is_running = True
        success = False
        
        try:
            self.logger.info(f"Starting retake process for {len(self.failed_products)} products...")
            self.emit_status("Initializing retake process...")
            
            if not self.failed_products:
                self.emit_status("No failed products to retake")
                self.logger.info("No failed products found")
                success = True
                return
            
            if not self.should_continue():
                self.logger.info("Stop requested before starting retake")
                return
            
            total_failed = len(self.failed_products)
            self.emit_progress(0, total_failed, "Preparing products for retake...")
            
            # Reset status for failed products
            self.emit_status("Resetting product statuses...")
            reset_count = 0
            
            for i, product in enumerate(self.failed_products):
                if not self.should_continue():
                    break
                    
                product_url = product[1]  # URL is at index 1
                if self.db_controller.reset_product_status(product_url):
                    reset_count += 1
                
                self.emit_progress(i + 1, total_failed, f"Reset {reset_count}/{total_failed} products")
            
            if not self.should_continue():
                self.emit_status("Retake process stopped by user")
                return
            
            self.logger.info(f"Reset status for {reset_count} products, starting scraping...")
            
            # Start monitoring
            monitoring_thread = threading.Thread(target=self._monitor_retake_progress, args=(total_failed,))
            monitoring_thread.daemon = True
            monitoring_thread.start()
            
            # Start scraping process with error protection
            try:
                self._run_retake_scraping()
                success = True
            except Exception as e:
                self.logger.log_exception(e, "retake scraping execution")
                success = False
            
            # Wait for monitoring to finish
            monitoring_thread.join(timeout=10)
            
            # Final status
            if self.should_continue() and success:
                success_message = f"Retake process completed for {total_failed} products"
                self.emit_status(success_message)
                self.logger.info(success_message)
            elif not self.should_continue():
                self.emit_status("Retake process was stopped")
                success = False
            
        except Exception as e:
            error_msg = f"Retake process failed: {str(e)}"
            self.emit_error(error_msg)
            self.logger.log_exception(e, "retake worker")
            success = False
            
        finally:
            self._is_running = False
            # FIXED: Use custom signal
            self.process_completed.emit(success)
    
    def _run_retake_scraping(self):
        """Run the scraping process for retake with crash protection"""
        try:
            self.logger.info("Executing main scraping function for retake...")
            
            self._retake_process = threading.current_thread()
            
            if not self.should_continue():
                self.logger.info("Cancelling retake before execution")
                return
            
            # PROTECTION: Set environment variables
            os.environ['PYTHONPATH'] = str(project_root)
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            
            # Execute with timeout protection
            self._execute_retake_with_timeout()
            
            self.logger.info("Retake scraping function completed")
            
        except Exception as e:
            if self.should_continue():
                self.logger.log_exception(e, "running retake scraping process")
                raise
            else:
                self.logger.info("Retake process interrupted by stop signal")
    
    def _execute_retake_with_timeout(self):
        """Execute retake function with timeout protection"""
        import threading
        
        # Create a thread for the main function
        retake_thread = threading.Thread(target=go_main)
        retake_thread.daemon = True
        retake_thread.start()
        
        # Monitor the thread
        while retake_thread.is_alive() and self.should_continue():
            retake_thread.join(timeout=5)  # Check every 5 seconds
        
        if retake_thread.is_alive() and not self.should_continue():
            self.logger.info("Retake process thread still running after stop signal")
    
    def _monitor_retake_progress(self, total_retake):
        """Monitor retake progress"""
        start_time = time.time()
        
        while self.should_continue():
            try:
                # Get current processing stats
                current_stats = self.db_controller.get_processing_stats()
                
                # For retake, we monitor how many are no longer '404'
                current_failed = self.db_controller.get_failed_products_count()
                processed = total_retake - current_failed
                
                progress_message = f"Retake progress: {processed}/{total_retake} products processed"
                self.emit_progress(processed, total_retake, progress_message)
                
                # Check if processing is still active
                if not current_stats.get('is_processing', True) and processed > 0:
                    self.logger.info("Retake process appears to be complete")
                    break
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                if self.should_continue():
                    self.logger.warning(f"Error monitoring retake progress: {e}")
                time.sleep(5)


class SafeProgressMonitorThread(QThread):
    """Thread for monitoring general system progress - CRASH PROTECTED"""
    
    progress_update = pyqtSignal(dict)  # progress_data
    
    def __init__(self, db_controller):
        super().__init__()
        self.db_controller = db_controller
        self.logger = get_logger("progress_monitor", "app.log")
        self._should_stop = False
        self._stop_lock = threading.Lock()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        with self._stop_lock:
            self._should_stop = True
        
        self.requestInterruption()
    
    def should_continue(self):
        """Check if monitoring should continue"""
        with self._stop_lock:
            return not (self._should_stop or self.isInterruptionRequested())
    
    def run(self):
        """Monitor system progress continuously with crash protection"""
        while self.should_continue():
            try:
                # Get comprehensive stats with error protection
                stats = self._safe_get_stats()
                
                if stats and self.should_continue():
                    self.progress_update.emit(stats)
                
                # Wait before next update
                time.sleep(3)  # Update every 3 seconds
                
            except Exception as e:
                if self.should_continue():
                    self.logger.warning(f"Error in progress monitoring: {e}")
                time.sleep(5)
    
    def _safe_get_stats(self):
        """Safely get database stats with error handling"""
        try:
            stats = self.db_controller.get_processing_stats()
            
            # Add timestamp
            stats['timestamp'] = time.time()
            stats['formatted_time'] = time.strftime('%H:%M:%S')
            
            return stats
        except Exception as e:
            self.logger.warning(f"Error getting stats: {e}")
            return None


class SafeLogTailThread(QThread):
    """Thread for tailing log file changes - CRASH PROTECTED"""
    
    new_log_lines = pyqtSignal(list)  # list of new log lines
    
    def __init__(self, log_file_path="logs/app.log"):
        super().__init__()
        self.log_file_path = Path(log_file_path)
        self.logger = get_logger("log_tail", "app.log")
        self._should_stop = False
        self._last_position = 0
        self._stop_lock = threading.Lock()
    
    def stop_tailing(self):
        """Stop tailing the log file"""
        with self._stop_lock:
            self._should_stop = True
        
        self.requestInterruption()
    
    def should_continue(self):
        """Check if tailing should continue"""
        with self._stop_lock:
            return not (self._should_stop or self.isInterruptionRequested())
    
    def run(self):
        """Continuously tail the log file for new entries with crash protection"""
        # Initialize position safely
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)  # Go to end of file
                    self._last_position = f.tell()
        except Exception as e:
            self.logger.warning(f"Error initializing log tail: {e}")
        
        while self.should_continue():
            try:
                new_lines = self._safe_read_new_lines()
                
                if new_lines and self.should_continue():
                    self.new_log_lines.emit(new_lines)
                
                # Wait before checking again
                self.msleep(1000)  # Check every second
                
            except Exception as e:
                if self.should_continue():
                    self.logger.warning(f"Error tailing log file: {e}")
                self.msleep(5000)  # Wait 5 seconds on error
    
    def _safe_read_new_lines(self):
        """Safely read new lines from log file"""
        try:
            if not self.log_file_path.exists():
                return None
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self._last_position)
                new_content = f.read()
                
                if new_content:
                    new_lines = new_content.strip().split('\n')
                    new_lines = [line for line in new_lines if line.strip()]
                    
                    if new_lines:
                        self._last_position = f.tell()
                        return new_lines
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error reading log file: {e}")
            return None


# Export all thread classes
__all__ = [
    'BaseWorkerThread',
    'ScrapingWorkerThread', 
    'RetakeWorkerThread',
    'SafeProgressMonitorThread',
    'SafeLogTailThread'
]