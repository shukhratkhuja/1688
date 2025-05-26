"""
Worker Threads for background scraping operations
"""

import sys, os
import time
import threading
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
    """Base worker thread with common functionality"""
    
    # Signals
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    status_updated = pyqtSignal(str)  # status_message
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, process_type, db_controller):
        super().__init__()
        self.process_type = process_type
        self.db_controller = db_controller
        self.logger = get_logger(f"worker_{process_type}", "app.log")
        
        # Control flags
        self._should_stop = False
        self._is_running = False
        
        # Progress tracking
        self._current_step = 0
        self._total_steps = 0
        self._last_progress_time = 0
    
    def stop_process(self):
        """Signal the worker to stop"""
        self._should_stop = True
        self.logger.info(f"Stop signal sent to {self.process_type} worker")
    
    def is_running(self):
        """Check if worker is currently running"""
        return self._is_running
    
    def emit_progress(self, current, total, message):
        """Emit progress update with throttling"""
        current_time = time.time()
        
        # Throttle progress updates (max once per second)
        if current_time - self._last_progress_time >= 1.0:
            self.progress_updated.emit(current, total, message)
            self._last_progress_time = current_time
    
    def emit_status(self, message):
        """Emit status update"""
        self.status_updated.emit(message)
        self.logger.info(f"Status: {message}")
    
    def emit_error(self, error_message):
        """Emit error signal"""
        self.error_occurred.emit(error_message)
        self.logger.error(f"Error: {error_message}")
    
    def run(self):
        """Main thread execution - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement run method")


class ScrapingWorkerThread(BaseWorkerThread):
    """Worker thread for new product scraping"""
    
    def __init__(self, process_type, db_controller):
        super().__init__(process_type, db_controller)
        self.logger = get_logger("scraping_worker", "app.log")
    
    def run(self):
        """Execute new product scraping"""
        self._is_running = True
        success = False
        
        try:
            self.logger.info("Starting new product scraping process...")
            self.emit_status("Initializing scraping process...")
            
            # Check initial state
            initial_stats = self.db_controller.get_processing_stats()
            total_products = initial_stats.get('total_products', 0)
            
            if total_products == 0:
                self.emit_status("No products found in database")
                self.logger.warning("No products to scrape")
                return
            
            self.emit_progress(0, total_products, "Starting scraping process...")
            
            # Monitor progress while scraping runs
            scraping_thread = threading.Thread(target=self._run_scraping_process)
            scraping_thread.daemon = True
            scraping_thread.start()
            
            # Monitor progress
            self._monitor_scraping_progress(total_products)
            
            # Wait for scraping thread to complete
            scraping_thread.join(timeout=60)  # Wait up to 1 minute for cleanup
            
            # Final status check
            final_stats = self.db_controller.get_processing_stats()
            completed = final_stats.get('scraped', 0)
            
            success_message = f"Scraping completed! Processed {completed}/{total_products} products"
            self.emit_status(success_message)
            self.logger.info(success_message)
            
            success = True
            
        except Exception as e:
            error_msg = f"Scraping process failed: {str(e)}"
            self.emit_error(error_msg)
            self.logger.log_exception(e, "scraping worker")
            success = False
            
        finally:
            self._is_running = False
            self.finished.emit(success)
    
    def _run_scraping_process(self):
        """Run the actual scraping process in a separate thread"""
        try:
            self.logger.info("Executing main scraping function...")
            go_main()  # Call your main scraping function
            self.logger.info("Main scraping function completed")
            
        except Exception as e:
            self.logger.log_exception(e, "running main scraping process")
            raise
    
    def _monitor_scraping_progress(self, total_products):
        """Monitor scraping progress and update UI"""
        start_time = time.time()
        last_completed = 0
        stall_counter = 0
        
        while not self._should_stop:
            try:
                # Get current stats
                current_stats = self.db_controller.get_processing_stats()
                completed = current_stats.get('scraped', 0)
                
                # Calculate progress
                progress_message = f"Scraped {completed}/{total_products} products"
                self.emit_progress(completed, total_products, progress_message)
                
                # Check for completion
                if not current_stats.get('is_processing', True):
                    self.logger.info("Scraping process appears to be complete")
                    break
                
                # Check for stalled progress
                if completed == last_completed:
                    stall_counter += 1
                    if stall_counter > 60:  # 60 * 5 seconds = 5 minutes stalled
                        self.logger.warning("Scraping process appears stalled")
                        self.emit_status("Warning: Process may be stalled")
                else:
                    stall_counter = 0
                    last_completed = completed
                
                # Check stop signal
                if self._should_stop:
                    self.logger.info("Stop signal received, terminating monitoring")
                    break
                
                # Wait before next check
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.warning(f"Error monitoring progress: {e}")
                time.sleep(5)
                
        # Final progress update
        try:
            final_stats = self.db_controller.get_processing_stats()
            final_completed = final_stats.get('scraped', 0)
            final_message = f"Final status: {final_completed}/{total_products} products scraped"
            self.emit_progress(final_completed, total_products, final_message)
        except:
            pass


class RetakeWorkerThread(BaseWorkerThread):
    """Worker thread for retaking failed products"""
    
    def __init__(self, process_type, db_controller, failed_products):
        super().__init__(process_type, db_controller)
        self.failed_products = failed_products
        self.logger = get_logger("retake_worker", "app.log")
    
    def run(self):
        """Execute retake process for failed products"""
        self._is_running = True
        success = False
        
        try:
            self.logger.info(f"Starting retake process for {len(self.failed_products)} products...")
            self.emit_status("Initializing retake process...")
            
            if not self.failed_products:
                self.emit_status("No failed products to retake")
                self.logger.info("No failed products found")
                return
            
            total_failed = len(self.failed_products)
            self.emit_progress(0, total_failed, "Preparing products for retake...")
            
            # Reset status for failed products (already done in controller, but verify)
            self.emit_status("Resetting product statuses...")
            reset_count = 0
            
            for i, product in enumerate(self.failed_products):
                if self._should_stop:
                    break
                    
                product_url = product[1]  # URL is at index 1
                if self.db_controller.reset_product_status(product_url):
                    reset_count += 1
                
                self.emit_progress(i + 1, total_failed, f"Reset {reset_count}/{total_failed} products")
            
            if self._should_stop:
                self.emit_status("Retake process stopped by user")
                return
            
            self.logger.info(f"Reset status for {reset_count} products, starting scraping...")
            
            # Start scraping process
            scraping_thread = threading.Thread(target=self._run_retake_scraping)
            scraping_thread.daemon = True
            scraping_thread.start()
            
            # Monitor retake progress
            self._monitor_retake_progress(total_failed)
            
            # Wait for scraping to complete
            scraping_thread.join(timeout=60)
            
            # Final status
            success_message = f"Retake process completed for {total_failed} products"
            self.emit_status(success_message)
            self.logger.info(success_message)
            
            success = True
            
        except Exception as e:
            error_msg = f"Retake process failed: {str(e)}"
            self.emit_error(error_msg)
            self.logger.log_exception(e, "retake worker")
            success = False
            
        finally:
            self._is_running = False
            self.finished.emit(success)
    
    def _run_retake_scraping(self):
        """Run the scraping process for retake"""
        try:
            self.logger.info("Executing main scraping function for retake...")
            go_main()  # Call your main scraping function
            self.logger.info("Retake scraping function completed")
            
        except Exception as e:
            self.logger.log_exception(e, "running retake scraping process")
            raise
    
    def _monitor_retake_progress(self, total_retake):
        """Monitor retake progress"""
        start_time = time.time()
        
        while not self._should_stop:
            try:
                # Get current processing stats
                current_stats = self.db_controller.get_processing_stats()
                
                # For retake, we monitor how many are no longer '404'
                current_failed = self.db_controller.get_failed_products_count()
                processed = total_retake - current_failed
                
                progress_message = f"Retake progress: {processed}/{total_retake} products processed"
                self.emit_progress(processed, total_retake, progress_message)
                
                # Check if processing is still active
                if not current_stats.get('is_processing', True):
                    self.logger.info("Retake process appears to be complete")
                    break
                
                # Check stop signal
                if self._should_stop:
                    self.logger.info("Stop signal received for retake process")
                    break
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.warning(f"Error monitoring retake progress: {e}")
                time.sleep(5)


class ProgressMonitorThread(QThread):
    """Thread for monitoring general system progress"""
    
    progress_update = pyqtSignal(dict)  # progress_data
    
    def __init__(self, db_controller):
        super().__init__()
        self.db_controller = db_controller
        self.logger = get_logger("progress_monitor", "app.log")
        self._should_stop = False
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self._should_stop = True
    
    def run(self):
        """Monitor system progress continuously"""
        while not self._should_stop:
            try:
                # Get comprehensive stats
                stats = self.db_controller.get_processing_stats()
                
                # Add timestamp
                stats['timestamp'] = time.time()
                stats['formatted_time'] = time.strftime('%H:%M:%S')
                
                # Emit progress data
                self.progress_update.emit(stats)
                
                # Wait before next update
                time.sleep(3)  # Update every 3 seconds
                
            except Exception as e:
                self.logger.warning(f"Error in progress monitoring: {e}")
                time.sleep(5)


class LogTailThread(QThread):
    """Thread for tailing log file changes"""
    
    new_log_lines = pyqtSignal(list)  # list of new log lines
    
    def __init__(self, log_file_path="logs/app.log"):
        super().__init__()
        self.log_file_path = Path(log_file_path)
        self.logger = get_logger("log_tail", "app.log")
        self._should_stop = False
        self._last_position = 0
    
    def stop_tailing(self):
        """Stop tailing the log file"""
        self._should_stop = True
    
    def run(self):
        """Continuously tail the log file for new entries"""
        # Initialize position
        if self.log_file_path.exists():
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # Go to end of file
                self._last_position = f.tell()
        
        while not self._should_stop:
            try:
                if self.log_file_path.exists():
                    with open(self.log_file_path, 'r', encoding='utf-8') as f:
                        f.seek(self._last_position)
                        new_content = f.read()
                        
                        if new_content:
                            new_lines = new_content.strip().split('\n')
                            new_lines = [line for line in new_lines if line.strip()]
                            
                            if new_lines:
                                self.new_log_lines.emit(new_lines)
                            
                            self._last_position = f.tell()
                
                # Wait before checking again
                self.msleep(1000)  # Check every second
                
            except Exception as e:
                self.logger.warning(f"Error tailing log file: {e}")
                self.msleep(5000)  # Wait 5 seconds on error


class DatabaseCleanupThread(QThread):
    """Thread for database maintenance and cleanup operations"""
    
    cleanup_completed = pyqtSignal(dict)  # cleanup_results
    
    def __init__(self, db_controller):
        super().__init__()
        self.db_controller = db_controller
        self.logger = get_logger("db_cleanup", "app.log")
    
    def run(self):
        """Perform database cleanup operations"""
        try:
            self.logger.info("Starting database cleanup operations...")
            
            results = {
                'vacuum_completed': False,
                'integrity_check': False,
                'orphaned_records_cleaned': 0,
                'old_logs_cleaned': 0
            }
            
            # Vacuum database
            try:
                import sqlite3
                with sqlite3.connect(self.db_controller.db_path) as conn:
                    conn.execute("VACUUM")
                    results['vacuum_completed'] = True
                    self.logger.info("Database vacuum completed")
            except Exception as e:
                self.logger.warning(f"Database vacuum failed: {e}")
            
            # Integrity check
            try:
                integrity_results = self.db_controller.validate_database_integrity()
                results['integrity_check'] = all(integrity_results.values())
                self.logger.info(f"Database integrity check: {results['integrity_check']}")
            except Exception as e:
                self.logger.warning(f"Integrity check failed: {e}")
            
            # Clean up old logs (optional)
            try:
                log_dir = Path("logs")
                if log_dir.exists():
                    # Keep only last 10 log files (example cleanup)
                    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                    for old_log in log_files[10:]:  # Keep only latest 10
                        try:
                            old_log.unlink()
                            results['old_logs_cleaned'] += 1
                        except:
                            pass
            except Exception as e:
                self.logger.warning(f"Log cleanup failed: {e}")
            
            self.logger.info(f"Database cleanup completed: {results}")
            self.cleanup_completed.emit(results)
            
        except Exception as e:
            self.logger.log_exception(e, "database cleanup")
            self.cleanup_completed.emit({'error': str(e)})