"""
Scraping Controller - Fixed version with proper thread management
"""

import sys
import threading
import time
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

# Add both desktop_app and project root to path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent
sys.path.insert(0, str(desktop_dir))  # For desktop_app modules
sys.path.insert(0, str(project_root)) # For original utils

from utils.log_config import get_logger
from main import main as go_main
 
from desktop_app.controllers.database_controller import DatabaseController
from desktop_app.utils.worker_threads import ScrapingWorkerThread, RetakeWorkerThread


class ScrapingController(QObject):
    """Controller for managing scraping operations with proper thread lifecycle"""
    
    # Signals for UI communication
    process_started = pyqtSignal(str)  # process_type
    process_finished = pyqtSignal(str, bool)  # process_type, success
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    status_updated = pyqtSignal(str)  # status_message
    error_occurred = pyqtSignal(str)  # error_message
    

    def __init__(self):
        super().__init__()
        self.logger = get_logger("scraping_controller", "app.log")
        
        # Initialize database controller
        try:
            self.db_controller = DatabaseController()
            self.logger.info("Database controller initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database controller: {e}")
            raise
        
        # Process state - CRUCIAL: proper initialization
        self._is_processing = False
        self._current_process = None
        self._worker_thread = None
        self._should_stop = False
        self._stop_requested = False  # New flag for better control
        
        # Progress tracking
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)
    

    def is_processing(self):
        """Check if any process is currently running"""
        return self._is_processing and self._worker_thread is not None and self._worker_thread.isRunning()
    

    def start_new_scraping(self):
        """Start new product scraping process"""
        if self.is_processing():
            self.logger.warning("Cannot start new scraping: another process is running")
            self.status_updated.emit("⚠️ Another process is already running")
            return False
        
        try:
            self.logger.info("Starting new product scraping process...")
            
            # IMPORTANT: Reset all flags before starting
            self._reset_process_state()
            
            # Create and start worker thread
            self._worker_thread = ScrapingWorkerThread(
                process_type="new_scraping",
                db_controller=self.db_controller
            )
            
            # Connect worker signals
            self._connect_worker_signals()
            
            # Start the process
            self._is_processing = True
            self._current_process = "New Product Scraping"
            self._should_stop = False
            self._stop_requested = False
            
            self._worker_thread.start()
            self._progress_timer.start(3000)  # Update progress every 3 seconds
            
            self.process_started.emit(self._current_process)
            self.logger.info("New scraping process started successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting new scraping: {e}")
            self.error_occurred.emit(f"Failed to start scraping: {str(e)}")
            self._reset_process_state()
            return False
    

    def start_retake_process(self, selected_products=None):
        """Start retake process for failed products"""
        if self.is_processing():
            self.logger.warning("Cannot start retake: another process is running")
            self.status_updated.emit("⚠️ Another process is already running")
            return False
        
        try:
            # Get failed products or use selected ones
            if selected_products:
                failed_products = selected_products
                self.logger.info(f"Starting retake process for {len(selected_products)} selected products...")
            else:
                failed_products = self.db_controller.get_failed_products()
                self.logger.info(f"Starting retake process for all {len(failed_products)} failed products...")
            
            if not failed_products:
                self.status_updated.emit("No failed products found for retake")
                return False
            
            # IMPORTANT: Reset all flags before starting
            self._reset_process_state()
            
            # Reset status for failed products
            self._reset_failed_products_status(failed_products)
            
            # Create and start worker thread
            self._worker_thread = RetakeWorkerThread(
                process_type="retake",
                db_controller=self.db_controller,
                failed_products=failed_products
            )
            
            # Connect worker signals
            self._connect_worker_signals()
            
            # Start the process
            self._is_processing = True
            self._current_process = "Product Retake"
            self._should_stop = False
            self._stop_requested = False
            
            self._worker_thread.start()
            self._progress_timer.start(3000)  # Update progress every 3 seconds
            
            self.process_started.emit(self._current_process)
            self.logger.info(f"Retake process started successfully for {len(failed_products)} products")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting retake process: {e}")
            self.error_occurred.emit(f"Failed to start retake: {str(e)}")
            self._reset_process_state()
            return False
    

    def stop_process(self):
        """Stop current scraping process - IMPROVED VERSION"""
        if not self.is_processing():
            self.logger.info("No process running to stop")
            return True
        
        try:
            self.logger.info("Stopping current process...")
            self._stop_requested = True
            self._should_stop = True
            
            # Stop progress timer immediately
            if self._progress_timer.isActive():
                self._progress_timer.stop()
            
            if self._worker_thread and self._worker_thread.isRunning():
                # Signal the worker to stop gracefully
                self._worker_thread.stop_process()
                
                # Wait for thread to finish (maximum 10 seconds)
                if self._worker_thread.wait(10000):  # 10 seconds
                    self.logger.info("Worker thread stopped gracefully")
                else:
                    self.logger.warning("Worker thread timeout, requesting interruption...")
                    self._worker_thread.requestInterruption()
                    
                    # Wait additional 5 seconds for forced stop
                    if self._worker_thread.wait(5000):
                        self.logger.info("Worker thread stopped after interruption")
                    else:
                        self.logger.error("Worker thread failed to stop, will be cleaned up on exit")
            
            # Force reset state regardless of thread status
            self._reset_process_state()
            
            self.status_updated.emit("Process stopped by user")
            self.process_finished.emit(self._current_process or "Unknown Process", False)
            self.logger.info("Process stopped successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            # Force reset even on error
            self._reset_process_state()
            self.error_occurred.emit(f"Process stopped with error: {str(e)}")
            return False

    
    def _connect_worker_signals(self):
        """Connect worker thread signals to controller slots"""
        if self._worker_thread:
            # FIXED: Use process_completed instead of finished
            self._worker_thread.process_completed.connect(self._on_worker_finished)
            self._worker_thread.progress_updated.connect(self._on_worker_progress)
            self._worker_thread.status_updated.connect(self._on_worker_status)
            self._worker_thread.error_occurred.connect(self._on_worker_error)
    

    def _reset_failed_products_status(self, failed_products):
        """Reset status columns for failed products"""
        try:
            for product in failed_products:
                product_url = product[1]  # Assuming URL is at index 1
                
                # Reset all status columns to 0
                self.db_controller.reset_product_status(product_url)
                
            self.logger.info(f"Reset status for {len(failed_products)} failed products")
            
        except Exception as e:
            self.logger.error(f"Error resetting failed products status: {e}")
            raise
    

    def _update_progress(self):
        """Update progress information from database"""
        if not self._is_processing or self._stop_requested:
            return
        
        try:
            # Get current progress stats
            stats = self.db_controller.get_processing_stats()
            
            # Emit progress based on current process
            if self._current_process == "New Product Scraping":
                total = stats.get('total_products', 0)
                completed = stats.get('scraped', 0)
                message = f"Processing products: {completed}/{total}"
                
            elif self._current_process == "Product Retake":
                total = stats.get('total_products', 0)
                failed = stats.get('failed', 0)
                completed = total - failed
                message = f"Retaking failed products: {completed}/{total}"
                
            else:
                total = 0
                completed = 0
                message = "Processing..."
            
            self.progress_updated.emit(completed, total, message)
            
        except Exception as e:
            self.logger.warning(f"Error updating progress: {e}")
    

    def _reset_process_state(self):
        """Reset controller state after process completion - IMPROVED"""
        self.logger.info("Resetting process state...")
        
        # Stop timer first
        if self._progress_timer.isActive():
            self._progress_timer.stop()
        
        # Disconnect signals if worker exists
        if self._worker_thread:
            try:
                self._worker_thread.disconnect()
            except:
                pass  # Ignore disconnection errors
        
        # Reset state variables
        self._is_processing = False
        self._current_process = None
        self._should_stop = False
        self._stop_requested = False
        self._worker_thread = None
        
        self.logger.info("Process state reset complete")
    

    def _on_worker_finished(self, success):
        """Handle worker thread completion"""
        process_name = self._current_process or "Unknown Process"
        
        if success:
            self.logger.info(f"{process_name} completed successfully")
        else:
            self.logger.warning(f"{process_name} completed with errors")
        
        self.process_finished.emit(process_name, success)
        self._reset_process_state()
    

    def _on_worker_progress(self, current, total, message):
        """Handle progress updates from worker"""
        if not self._stop_requested:
            self.progress_updated.emit(current, total, message)
    

    def _on_worker_status(self, message):
        """Handle status updates from worker"""
        if not self._stop_requested:
            self.status_updated.emit(message)
    

    def _on_worker_error(self, error_message):
        """Handle error from worker"""
        self.logger.error(f"Worker error: {error_message}")
        self.error_occurred.emit(error_message)
    
    
    def get_current_process_info(self):
        """Get information about current process"""
        return {
            'is_processing': self._is_processing,
            'process_type': self._current_process,
            'should_stop': self._should_stop,
            'stop_requested': self._stop_requested,
            'worker_running': self._worker_thread.isRunning() if self._worker_thread else False
        }
    
    
    def cleanup(self):
        """Cleanup resources before destruction - IMPROVED"""
        try:
            self.logger.info("Starting controller cleanup...")
            
            if self.is_processing():
                self.logger.info("Stopping process during cleanup...")
                self.stop_process()
            
            # Stop timer
            if self._progress_timer.isActive():
                self._progress_timer.stop()
            
            # Clean up worker thread
            if self._worker_thread:
                if self._worker_thread.isRunning():
                    self._worker_thread.requestInterruption()
                    self._worker_thread.wait(3000)  # Wait up to 3 seconds
                
                try:
                    self._worker_thread.disconnect()
                except:
                    pass
                
                self._worker_thread = None
            
            self.logger.info("Controller cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")