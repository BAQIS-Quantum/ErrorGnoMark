"""
Hardware Topology & Calibration Data Updater

This module automates the retrieval of the latest calibration data (.csv) and
topology maps (.png) for quantum chips.

Features:
- **Dual Browser Support**: Defaults to Google Chrome; falls back to Microsoft Edge if Chrome is missing.
- Intelligent handling of dynamic UI elements (hover menus, JS-forced clicks).
- Automatic file management (download to temp, move to specific chip folders).
- Preserves original server filenames.
- Portable relative path configuration.

Dependencies:
- selenium
- webdriver-manager
"""

import os
import time
import shutil
import sys

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Chrome Imports
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# Edge Imports
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# ================= Configuration =================

# Determine the directory where this script is located to ensure portability.
BASE_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DOWNLOAD_DIR = os.path.join(BASE_DATA_DIR, "temp_downloads")

# Mapping of Website Chip Names -> Local Folder Names
CHIP_MAPPING = {
    "Baihua": "Baihua",
    "Yudu": "Yudu",
    "Dongling": "Dongling",
    "Haituo": "Haituo",
}

TARGET_URL = "https://quafu-sqc.baqis.ac.cn/home"

# =============================================

class HardwareUpdater:
    def __init__(self):
        """Initialize the updater and setup the browser driver."""
        self.driver = self._setup_driver()

    def _get_browser_prefs(self):
        """Returns the common preference dictionary for Chromium-based browsers."""
        return {
            "download.default_directory": TEMP_DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

    def _setup_driver(self):
        """
        Attempts to initialize Google Chrome. If failed, falls back to Microsoft Edge.
        """
        # Ensure temporary download directory exists
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)

        # 1. Try initializing Google Chrome
        try:
            print(">>> Attempting to initialize Google Chrome...")
            options = ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("prefs", self._get_browser_prefs())

            # Suppress logging for cleaner output
            options.add_argument("--log-level=3")

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print(">>> Google Chrome initialized successfully.")
            return driver

        except Exception as e:
            print(f"    [Warning] Chrome initialization failed: {e}")
            print(">>> Falling back to Microsoft Edge...")

        # 2. Try initializing Microsoft Edge (Fallback)
        try:
            options = EdgeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("prefs", self._get_browser_prefs())

            options.add_argument("--log-level=3")

            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            print(">>> Microsoft Edge initialized successfully.")
            return driver

        except Exception as e:
            print(f"    [Fatal Error] Edge initialization failed: {e}")
            print(">>> No compatible browser found. Please install Google Chrome or Microsoft Edge.")
            sys.exit(1)

    def show_red_dot(self, element):
        """
        [Debug Utility] Visual indicator for element location.
        Draws a temporary red circle around the target element in the browser.
        """
        js_code = """
        var dot = document.createElement('div');
        dot.style.height = '14px';
        dot.style.width = '14px';
        dot.style.border = '3px solid red';
        dot.style.borderRadius = '50%';
        dot.style.position = 'absolute';
        dot.style.zIndex = '999999';
        dot.style.pointerEvents = 'none';
        
        // Calculate position relative to the document
        var rect = arguments[0].getBoundingClientRect();
        var x = rect.left + window.scrollX + (rect.width / 2) - 7;
        var y = rect.top + window.scrollY + (rect.height / 2) - 7;
        
        dot.style.left = x + 'px';
        dot.style.top = y + 'px';
        
        document.body.appendChild(dot);
        setTimeout(function(){ document.body.removeChild(dot); }, 2000);
        """
        try:
            self.driver.execute_script(js_code, element)
        except Exception:
            pass

    def wait_for_download(self, extension, timeout=30):
        """
        Waits for a file with a specific extension to appear in the temp directory.

        Args:
            extension (str): File extension to watch for (e.g., '.csv').
            timeout (int): Maximum wait time in seconds.

        Returns:
            str: Full path to the downloaded file, or None if timed out.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = [f for f in os.listdir(TEMP_DOWNLOAD_DIR) if f.endswith(extension)]
            if files:
                # Ensure the download is complete (no .crdownload files)
                if not any(f.endswith('.crdownload') for f in os.listdir(TEMP_DOWNLOAD_DIR)):
                    return os.path.join(TEMP_DOWNLOAD_DIR, files[0])
            time.sleep(1)
        return None

    def clear_temp_dir(self):
        """Clean up the temporary download directory."""
        if os.path.exists(TEMP_DOWNLOAD_DIR):
            for f in os.listdir(TEMP_DOWNLOAD_DIR):
                try:
                    os.unlink(os.path.join(TEMP_DOWNLOAD_DIR, f))
                except Exception:
                    pass

    def safe_click_menu_item(self, keyword):
        """
        Atomic operation: Open Menu -> JS Force Click Item.
        Matches menu items containing the keyword (e.g., '.csv').
        """
        print(f"    -> [Action] Attempting to download file containing '{keyword}'...")

        try:
            # 1. Locate the download button (identified by specific class)
            download_btn = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'page-container-icon')]"))
            )

            # 2. Trigger menu (Hover + Click backup)
            ActionChains(self.driver).move_to_element(download_btn).perform()
            time.sleep(0.5)
            download_btn.click()  # Explicit click to ensure menu opens

            # 3. Wait for item presence in DOM
            xpath_item = f"//li[contains(., '{keyword}')]"
            menu_item = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath_item))
            )

            # 4. JS Force Click (Bypasses UI obstructions)
            print(f"    -> [Lock] Menu item found. Triggering JS click...")
            self.driver.execute_script("arguments[0].click();", menu_item)

            return True

        except Exception as e:
            print(f"    -> [Failed] Operation error: {e}")
            return False

    def process_single_chip(self, web_name, local_folder):
        """
        Orchestrates the download process for a single chip.
        """
        print(f"\n--------------------------------")
        print(f"Processing Chip: {web_name}")

        target_dir = os.path.join(BASE_DATA_DIR, local_folder)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        try:
            # 1. Click Chip Card on Homepage
            xpath_chip = f"//*[contains(text(), '{web_name}')]"
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_chip))).click()

            # 2. Wait for Detail Page Load
            print("    -> Waiting for detail page to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'page-container-icon')]"))
            )
            time.sleep(1)  # Brief buffer for animations

            # ========================
            #  Action 1: Download CSV
            # ========================
            self.clear_temp_dir()
            if self.safe_click_menu_item(".csv"):
                csv_path = self.wait_for_download(".csv")
                if csv_path:
                    original_name = os.path.basename(csv_path)
                    dst_path = os.path.join(target_dir, original_name)

                    if os.path.exists(dst_path):
                        os.remove(dst_path)

                    shutil.move(csv_path, dst_path)
                    print(f"[Success] CSV Saved -> {dst_path}")
                else:
                    print("    -> [Timeout] CSV download timed out.")

            time.sleep(1)

            # ========================
            #  Action 2: Download PNG
            # ========================
            self.clear_temp_dir()
            if self.safe_click_menu_item(".png"):
                png_path = self.wait_for_download(".png")
                if png_path:
                    original_name = os.path.basename(png_path)
                    dst_path = os.path.join(target_dir, original_name)

                    if os.path.exists(dst_path):
                        os.remove(dst_path)

                    shutil.move(png_path, dst_path)
                    print(f"[Success] PNG Saved -> {dst_path}")
                else:
                    print("    -> [Timeout] PNG download timed out.")

            # 3. Return to Homepage
            self.driver.back()
            time.sleep(2)

        except Exception as e:
            print(f"[Error] Processing {web_name}: {e}")
            self.driver.save_screenshot(os.path.join(target_dir, "debug_error.png"))
            try:
                self.driver.get(TARGET_URL)
                time.sleep(3)
            except:
                pass

    def run(self):
        """Main execution flow."""
        try:
            print(f">>> Opening URL: {TARGET_URL}")
            self.driver.get(TARGET_URL)

            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            for web_name, local_folder in CHIP_MAPPING.items():
                self.process_single_chip(web_name, local_folder)

        except Exception as e:
            print(f"[Fatal Error] Script execution failed: {e}")
        finally:
            print(">>> Closing browser and cleaning up resources...")
            # Safely close driver if it exists
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
            if os.path.exists(TEMP_DOWNLOAD_DIR):
                shutil.rmtree(TEMP_DOWNLOAD_DIR)


if __name__ == "__main__":
    updater = HardwareUpdater()
    updater.run()