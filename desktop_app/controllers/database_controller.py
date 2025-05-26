"""
Database Controller - Handles all database operations for the desktop app
"""

import sys, os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Add both desktop_app and project root to path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent
sys.path.insert(0, str(desktop_dir))  # For desktop_app modules
sys.path.insert(0, str(project_root)) # For original utils


from utils.log_config import get_logger
from utils.db_utils import fetch_many, update_row
from utils.constants import DB_NAME, TABLE_PRODUCT_DATA, TABLE_PRODUCT_IMAGES


class DatabaseController:
    """Controller for database operations with error handling and logging"""
    
    def __init__(self):
        self.logger = get_logger("database_controller", "app.log")
        self.db_path = DB_NAME
        self._verify_database_connection()
    
    def _verify_database_connection(self):
        """Verify database exists and is accessible"""
        try:
            db_file = Path(self.db_path)
            if not db_file.exists():
                self.logger.error(f"Database file not found: {self.db_path}")
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            
            # Test connection
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
            self.logger.info(f"Database connected successfully. Found {len(tables)} tables.")
            
        except Exception as e:
            self.logger.log_exception(e, "database connection verification")
            raise
    
    def get_products_for_display(self, limit: int = 1000) -> List[Tuple]:
        """Get product data for table display"""
        try:
            products = fetch_many(
                db=self.db_path,
                table=TABLE_PRODUCT_DATA,
                columns_list=[
                    "id",
                    "product_url", 
                    "title_chn",
                    "title_en",
                    "scraped_status",
                    "translated_status", 
                    "uploaded_to_gd_status",
                    "updated_on_notion_status",
                    "created_at"
                ],
                order_by=[("id", "DESC")],
                limit=limit,
                logger=self.logger
            )
            
            return products or []
            
        except Exception as e:
            self.logger.log_exception(e, "getting products for display")
            return []
    
    def get_failed_products(self) -> List[Tuple]:
        """Get products with '404' status (failed products)"""
        try:
            failed_products = fetch_many(
                db=self.db_path,
                table=TABLE_PRODUCT_DATA,
                columns_list=[
                    "id",
                    "product_url",
                    "title_chn", 
                    "created_at"
                ],
                where=[("title_chn", "=", "404")],
                order_by=[("id", "DESC")],
                logger=self.logger
            )
            
            return failed_products or []
            
        except Exception as e:
            self.logger.log_exception(e, "getting failed products")
            return []
    
    def get_failed_products_count(self) -> int:
        """Get count of products with '404' status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE title_chn = ?",
                    ("404",)
                )
                count = cursor.fetchone()[0]
                return count
                
        except Exception as e:
            self.logger.log_exception(e, "getting failed products count")
            return 0
    
    def get_total_products(self) -> int:
        """Get total number of products in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA}")
                count = cursor.fetchone()[0]
                return count
                
        except Exception as e:
            self.logger.log_exception(e, "getting total products")
            return 0
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get comprehensive processing statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get various counts
                stats_queries = {
                    'total_products': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA}",
                    'scraped': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE scraped_status = 1",
                    'translated': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE translated_status = 1",
                    'uploaded': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE uploaded_to_gd_status = 1",
                    'notion_updated': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE updated_on_notion_status = 1",
                    'failed': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE title_chn = '404'",
                    'pending_scrape': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE scraped_status = 0",
                    'pending_translation': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE scraped_status = 1 AND translated_status = 0 AND title_chn != '404'",
                    'pending_upload': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE translated_status = 1 AND uploaded_to_gd_status = 0",
                    'pending_notion': f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE uploaded_to_gd_status = 1 AND updated_on_notion_status = 0"
                }
                
                stats = {}
                for key, query in stats_queries.items():
                    cursor.execute(query)
                    stats[key] = cursor.fetchone()[0]
                
                # Calculate completion percentages
                if stats['total_products'] > 0:
                    stats['scraped_percent'] = (stats['scraped'] / stats['total_products']) * 100
                    stats['translated_percent'] = (stats['translated'] / stats['total_products']) * 100
                    stats['uploaded_percent'] = (stats['uploaded'] / stats['total_products']) * 100
                    stats['notion_updated_percent'] = (stats['notion_updated'] / stats['total_products']) * 100
                else:
                    stats['scraped_percent'] = 0
                    stats['translated_percent'] = 0
                    stats['uploaded_percent'] = 0
                    stats['notion_updated_percent'] = 0
                
                # Add processing flags
                stats['is_processing'] = (
                    stats['pending_scrape'] > 0 or 
                    stats['pending_translation'] > 0 or
                    stats['pending_upload'] > 0 or
                    stats['pending_notion'] > 0
                )
                
                return stats
                
        except Exception as e:
            self.logger.log_exception(e, "getting processing stats")
            return {
                'total_products': 0, 'scraped': 0, 'translated': 0, 
                'uploaded': 0, 'notion_updated': 0, 'failed': 0,
                'pending_scrape': 0, 'pending_translation': 0,
                'pending_upload': 0, 'pending_notion': 0,
                'scraped_percent': 0, 'translated_percent': 0,
                'uploaded_percent': 0, 'notion_updated_percent': 0,
                'is_processing': False
            }
    
    def reset_product_status(self, product_url: str) -> bool:
        """Reset all status columns for a specific product"""
        try:
            # Reset all *status columns to 0
            status_updates = [
                ("scraped_status", 0),
                ("translated_status", 0),
                ("uploaded_to_gd_status", 0),
                ("updated_on_notion_status", 0),
                ("title_chn", None),  # Clear the 404 status
                ("title_en", None),
                ("product_attributes_chn", None),
                ("product_attributes_en", None),
                ("text_details_chn", None),
                ("text_details_en", None),
                ("gd_file_url", None),
                ("gd_product_images_folder_id", None)
            ]
            
            update_row(
                db=self.db_path,
                table=TABLE_PRODUCT_DATA,
                column_with_value=status_updates,
                where=[("product_url", "=", product_url)]
            )
            
            self.logger.info(f"Reset status for product: {product_url}")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, f"resetting status for product {product_url}")
            return False
    
    def reset_all_failed_products(self) -> int:
        """Reset status for all products with '404' status"""
        try:
            failed_products = self.get_failed_products()
            reset_count = 0
            
            for product in failed_products:
                product_url = product[1]  # URL is at index 1
                if self.reset_product_status(product_url):
                    reset_count += 1
            
            self.logger.info(f"Reset status for {reset_count} failed products")
            return reset_count
            
        except Exception as e:
            self.logger.log_exception(e, "resetting all failed products")
            return 0
    
    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent database activity within specified hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recently created/updated products
                cursor.execute(f"""
                    SELECT id, product_url, title_chn, title_en, 
                           scraped_status, translated_status, 
                           uploaded_to_gd_status, updated_on_notion_status,
                           created_at
                    FROM {TABLE_PRODUCT_DATA}
                    WHERE created_at >= datetime('now', '-{hours} hours')
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                
                recent_products = cursor.fetchall()
                
                activity = []
                for product in recent_products:
                    activity.append({
                        'id': product[0],
                        'product_url': product[1],
                        'title_chn': product[2],
                        'title_en': product[3],
                        'scraped_status': product[4],
                        'translated_status': product[5],
                        'uploaded_to_gd_status': product[6],
                        'updated_on_notion_status': product[7],
                        'created_at': product[8],
                        'type': 'product_update'
                    })
                
                return activity
                
        except Exception as e:
            self.logger.log_exception(e, "getting recent activity")
            return []
    
    def get_products_by_status(self, status_column: str, status_value: Any) -> List[Tuple]:
        """Get products filtered by specific status column"""
        try:
            valid_status_columns = [
                'scraped_status', 'translated_status', 
                'uploaded_to_gd_status', 'updated_on_notion_status'
            ]
            
            if status_column not in valid_status_columns:
                raise ValueError(f"Invalid status column: {status_column}")
            
            products = fetch_many(
                db=self.db_path,
                table=TABLE_PRODUCT_DATA,
                columns_list=[
                    "id", "product_url", "title_chn", "title_en",
                    "scraped_status", "translated_status",
                    "uploaded_to_gd_status", "updated_on_notion_status",
                    "created_at"
                ],
                where=[(status_column, "=", status_value)],
                order_by=[("id", "DESC")],
                limit=500,
                logger=self.logger
            )
            
            return products or []
            
        except Exception as e:
            self.logger.log_exception(e, f"getting products by status {status_column}={status_value}")
            return []
    
    def search_products(self, search_term: str, search_columns: List[str] = None) -> List[Tuple]:
        """Search products by term in specified columns"""
        try:
            if not search_columns:
                search_columns = ['product_url', 'title_chn', 'title_en']
            
            # Build WHERE clause for search
            where_conditions = []
            for column in search_columns:
                where_conditions.append(f"{column} LIKE ?")
            
            where_clause = " OR ".join(where_conditions)
            search_params = [f"%{search_term}%" for _ in search_columns]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = f"""
                    SELECT id, product_url, title_chn, title_en,
                           scraped_status, translated_status,
                           uploaded_to_gd_status, updated_on_notion_status,
                           created_at
                    FROM {TABLE_PRODUCT_DATA}
                    WHERE {where_clause}
                    ORDER BY id DESC
                    LIMIT 100
                """
                
                cursor.execute(query, search_params)
                results = cursor.fetchall()
                
                return results
                
        except Exception as e:
            self.logger.log_exception(e, f"searching products with term: {search_term}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get database file size
                db_file = Path(self.db_path)
                file_size_mb = db_file.stat().st_size / (1024 * 1024) if db_file.exists() else 0
                
                # Get table info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get product data table info
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA}")
                total_products = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE_PRODUCT_IMAGES}")
                total_images = cursor.fetchone()[0]
                
                # Get recent activity count
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA}
                    WHERE created_at >= datetime('now', '-24 hours')
                """)
                recent_products = cursor.fetchone()[0]
                
                return {
                    'database_path': str(self.db_path),
                    'file_size_mb': round(file_size_mb, 2),
                    'tables': tables,
                    'total_products': total_products,
                    'total_images': total_images,
                    'recent_products_24h': recent_products,
                    'last_updated': Path(self.db_path).stat().st_mtime
                }
                
        except Exception as e:
            self.logger.log_exception(e, "getting database info")
            return {
                'database_path': str(self.db_path),
                'file_size_mb': 0,
                'tables': [],
                'total_products': 0,
                'total_images': 0,
                'recent_products_24h': 0,
                'last_updated': 0
            }
    
    def validate_database_integrity(self) -> Dict[str, bool]:
        """Validate database structure and integrity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                checks = {}
                
                # Check if main tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_PRODUCT_DATA,))
                checks['product_data_table_exists'] = bool(cursor.fetchone())
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_PRODUCT_IMAGES,))
                checks['product_images_table_exists'] = bool(cursor.fetchone())
                
                # Check required columns in product_data table
                if checks['product_data_table_exists']:
                    cursor.execute(f"PRAGMA table_info({TABLE_PRODUCT_DATA})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    required_columns = [
                        'id', 'product_url', 'title_chn', 'title_en',
                        'scraped_status', 'translated_status',
                        'uploaded_to_gd_status', 'updated_on_notion_status'
                    ]
                    
                    checks['required_columns_exist'] = all(col in columns for col in required_columns)
                else:
                    checks['required_columns_exist'] = False
                
                # Check for orphaned records or data consistency
                if checks['product_data_table_exists']:
                    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_PRODUCT_DATA} WHERE product_url IS NULL")
                    null_urls = cursor.fetchone()[0]
                    checks['no_null_urls'] = (null_urls == 0)
                else:
                    checks['no_null_urls'] = False
                
                return checks
                
        except Exception as e:
            self.logger.log_exception(e, "validating database integrity")
            return {
                'product_data_table_exists': False,
                'product_images_table_exists': False,
                'required_columns_exist': False,
                'no_null_urls': False
            }