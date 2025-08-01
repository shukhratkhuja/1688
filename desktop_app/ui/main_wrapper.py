import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_main_process():
    """Wrapper for main scraping process"""
    try:
        # Change to project root directory
        os.chdir(project_root)
        
        # Import and run main
        from main import main
        main()
        return True
    except Exception as e:
        print(f"Error in main process: {e}")
        return False