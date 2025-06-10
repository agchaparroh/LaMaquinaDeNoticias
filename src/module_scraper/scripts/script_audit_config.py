import os
import importlib
import sys
from pathlib import Path

# Path Setup will be done in the main block, as per instructions
# to allow conditional import of get_project_settings

def get_class_from_path(class_path_str: str):
    """
    Attempts to import a class given its full path string.
    e.g., 'mypackage.mymodule.MyClass'
    Returns the class object or None if import fails.
    """
    if not class_path_str:
        print(f"  [!] Error: Empty class path string provided.")
        return None
    try:
        module_path, class_name = class_path_str.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        print(f"  [!] Error importing module from path '{class_path_str}': {e}")
        return None
    except AttributeError:
        print(f"  [!] Error: Class '{class_name}' not found in module '{module_path}'.")
        return None
    except ValueError as e:
        print(f"  [!] Error splitting class path string '{class_path_str}': {e}")
        return None

def analyze_component_settings(settings_dict, component_type_name: str):
    """
    Analyzes component settings like ITEM_PIPELINES, DOWNLOADER_MIDDLEWARES, etc.
    Checks for duplicate priorities and verifies class importability.
    """
    print(f"\n--- Analyzing {component_type_name} ---")
    if not settings_dict:
        print(f"  [*] No {component_type_name} configured or dictionary is empty.")
        return

    priorities = {}
    for component_path, priority in settings_dict.items():
        # Check for duplicate priorities
        if priority in priorities:
            print(f"  [!] Warning: Duplicate priority '{priority}' for {component_path} (already assigned to {priorities[priority]}).")
        else:
            priorities[priority] = component_path

        # Verify class importability
        print(f"  Verifying {component_type_name[:-1]}: {component_path} (Priority: {priority})")
        klass = get_class_from_path(component_path)
        if klass:
            print(f"    [+] Successfully imported: {klass.__name__}")
        else:
            print(f"    [-] Failed to import.")

def check_environment_variables():
    """
    Checks for the presence of expected environment variables and prints their status.
    """
    print("\n--- Checking Environment Variables ---")
    critical_vars = [
        'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_KEY',
        'SUPABASE_HTML_BUCKET', 'LOG_LEVEL', 'SCRAPY_SETTINGS_MODULE'
    ]
    optional_vars = [
        'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD',
        'LOG_FILE', 'PLAYWRIGHT_MAX_RETRIES', 'PLAYWRIGHT_TIMEOUT',
        'PLAYWRIGHT_ENABLE_FALLBACK', 'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT',
        'TENACITY_STOP_AFTER_ATTEMPT', 'TENACITY_WAIT_MULTIPLIER',
        'TENACITY_WAIT_MIN', 'TENACITY_WAIT_MAX'
    ]

    all_vars = critical_vars + optional_vars

    print("  Critical Variables:")
    for var_name in critical_vars:
        value = os.getenv(var_name)
        if value:
            if 'KEY' in var_name.upper() or 'PASSWORD' in var_name.upper():
                print(f"    [+] {var_name}: SET (value hidden)")
            else:
                print(f"    [+] {var_name}: SET (Value: '{value}')")
        else:
            print(f"    [-] {var_name}: NOT SET")

    print("\n  Optional Variables:")
    for var_name in optional_vars:
        value = os.getenv(var_name)
        if value:
            if 'KEY' in var_name.upper() or 'PASSWORD' in var_name.upper():
                print(f"    [+] {var_name}: SET (value hidden)")
            else:
                print(f"    [+] {var_name}: SET (Value: '{value}')")
        else:
            print(f"    [ ] {var_name}: NOT SET (Optional)")


def analyze_requirements(requirements_file_path: Path):
    """
    Reads and parses a requirements.txt file.
    """
    print("\n--- Analyzing Requirements File ---")
    if not requirements_file_path.is_file():
        print(f"  [!] Error: Requirements file not found at '{requirements_file_path}'")
        return

    print(f"  Reading requirements from: {requirements_file_path}")
    try:
        with open(requirements_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue

                parts = line.split('==')
                if len(parts) == 2:
                    package, version = parts[0].strip(), parts[1].strip()
                    print(f"    [+] Package: {package}, Version: {version}")
                elif len(parts) == 1 and all(c not in line for c in ['<', '>', '=', '!']): # Likely just a package name
                     print(f"    [+] Package: {line} (No version specified)")
                elif any(c in line for c in ['<', '>', '!', '~']): # Version specifiers
                    print(f"    [+] Requirement: {line}")
                else:
                    print(f"    [!] Warning: Could not parse line {line_num}: '{line}'")
    except Exception as e:
        print(f"  [!] Error reading or parsing requirements file: {e}")

if __name__ == "__main__":
    print("=== Configuration Audit Script Starting ===")

    # --- Path Setup ---
    # Calculate PROJECT_BASE_PATH (should resolve to src/module_scraper)
    # The script itself is in src/module_scraper/scripts/script_audit_config.py
    # So, PROJECT_BASE_PATH is two levels up from the script's parent directory.
    SCRIPT_PATH = Path(__file__).resolve()
    PROJECT_BASE_PATH = SCRIPT_PATH.parent.parent

    # Add PROJECT_BASE_PATH to sys.path
    sys.path.insert(0, str(PROJECT_BASE_PATH.parent)) # src directory
    sys.path.insert(0, str(PROJECT_BASE_PATH)) # src/module_scraper directory

    # Set SCRAPY_SETTINGS_MODULE environment variable
    # This should point to the settings module relative to a path in sys.path
    # e.g. if PROJECT_BASE_PATH (src/module_scraper) is in sys.path,
    # then 'scraper_core.settings' should work if scraper_core is under module_scraper
    # Or, if src is in sys.path, then 'module_scraper.scraper_core.settings'
    # For this project structure, 'scraper_core.settings' relative to PROJECT_BASE_PATH.

    # Let's adjust the env var setting to be robust:
    # We need 'scraper_core.settings' to be findable.
    # The structure is likely:
    # src/
    #   module_scraper/
    #     scraper_core/
    #       settings.py
    #     scripts/
    #       script_audit_config.py
    # If PROJECT_BASE_PATH is 'src/module_scraper', then 'scraper_core.settings' is correct.

    os.environ['SCRAPY_SETTINGS_MODULE'] = 'scraper_core.settings'
    print(f"[*] PROJECT_BASE_PATH set to: {PROJECT_BASE_PATH}")
    print(f"[*] sys.path updated with: {PROJECT_BASE_PATH.parent} and {PROJECT_BASE_PATH}")
    print(f"[*] SCRAPY_SETTINGS_MODULE set to: {os.environ['SCRAPY_SETTINGS_MODULE']}")

    # Import get_project_settings after path setup
    try:
        from scrapy.utils.project import get_project_settings
        print("[*] Successfully imported get_project_settings from scrapy.utils.project.")
    except ImportError as e:
        print(f"[!] Critical Error: Could not import get_project_settings: {e}")
        print("    Please ensure Scrapy is installed and sys.path is correctly configured.")
        get_project_settings = None # Ensure it's defined for later checks
    except Exception as e:
        print(f"[!] Critical Error during import of get_project_settings: {e}")
        get_project_settings = None


    if get_project_settings:
        try:
            print("\n--- Loading Scrapy Project Settings ---")
            settings = get_project_settings()
            if settings:
                print("  [+] Scrapy settings loaded successfully.")

                # Analyze components
                analyze_component_settings(settings.getdict('ITEM_PIPELINES'), 'ITEM_PIPELINES')
                analyze_component_settings(settings.getdict('DOWNLOADER_MIDDLEWARES'), 'DOWNLOADER_MIDDLEWARES')
                analyze_component_settings(settings.getdict('SPIDER_MIDDLEWARES'), 'SPIDER_MIDDLEWARES')
                # analyze_component_settings(settings.getdict('EXTENSIONS'), 'EXTENSIONS') # Example for more components
            else:
                print("  [!] Warning: get_project_settings() returned None or empty settings.")

        except Exception as e:
            print(f"  [!] Error loading Scrapy settings: {e}")
            print(f"    Current SCRAPY_SETTINGS_MODULE: {os.getenv('SCRAPY_SETTINGS_MODULE')}")
            print(f"    Current sys.path: {sys.path}")
            print(f"    Is there a scrapy.cfg file in the project root or any parent directory of PROJECT_BASE_PATH ({PROJECT_BASE_PATH})?")
            print(f"    Does '{os.getenv('SCRAPY_SETTINGS_MODULE')}.py' (i.e. scraper_core/settings.py) exist relative to an entry in sys.path?")

    else:
        print("\n[!] Skipping Scrapy settings analysis because get_project_settings could not be imported.")

    # Check environment variables
    check_environment_variables()

    # Analyze requirements.txt
    # Assuming requirements.txt is in the PROJECT_BASE_PATH (src/module_scraper)
    # If it's in the root of the git repo (one level above src), adjust path.
    # Based on "PROJECT_BASE_PATH / "requirements.txt"", it should be in src/module_scraper
    requirements_path = PROJECT_BASE_PATH / "requirements.txt"
    analyze_requirements(requirements_path)

    # Try one level up if not found, common for requirements.txt to be at repo root
    if not requirements_path.is_file():
        print(f"  [*] Note: '{requirements_path}' not found. Trying repo root level...")
        # Assuming SCRIPT_PATH is src/module_scraper/scripts/script_audit_config.py
        # Repo root would be SCRIPT_PATH.parent.parent.parent
        repo_root_req_path = SCRIPT_PATH.parent.parent.parent / "requirements.txt"
        analyze_requirements(repo_root_req_path)


    print("\n=== Configuration Audit Script Finished ===")
