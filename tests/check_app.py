#!/usr/bin/env python3
"""
Simple script to check if the SteadwellOS application is up and running.
This script doesn't require pytest, just selenium and webdriver-manager.
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def check_app(base_url="http://0.0.0.0:8080"):
    """Check if the application is up and running"""
    print(f"Checking if the application is running at {base_url}...")

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        # Initialize WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

        # Set timeout
        driver.implicitly_wait(10)

        # Check login page
        print("Checking login page...")
        driver.get(f"{base_url}/login")
        time.sleep(2)

        if "Login" in driver.title or "Sign In" in driver.title:
            print("✅ Login page loaded successfully")
        else:
            print("❌ Could not verify login page")
            return False

        # Try to login
        print("Attempting to login...")
        try:
            username_field = driver.find_element("id", "username")
            password_field = driver.find_element("id", "password")
            submit_button = driver.find_element("xpath", "//button[@type='submit']")

            username_field.send_keys("admin")
            password_field.send_keys("password123")
            submit_button.click()

            time.sleep(3)

            if "/dashboard" in driver.current_url:
                print("✅ Login successful, dashboard loaded")
            else:
                print("❌ Login failed or dashboard not loaded")
                return False

        except Exception as e:
            print(f"❌ Login failed with error: {e}")
            return False

        # Check protocols page
        print("Checking protocols page...")
        driver.get(f"{base_url}/protocols")
        time.sleep(3)

        if "Protocols" in driver.title:
            print("✅ Protocols page loaded successfully")
        else:
            print("❌ Could not verify protocols page")
            return False

        # Check patients page
        print("Checking patients page...")
        driver.get(f"{base_url}/patients")
        time.sleep(3)

        if "Patients" in driver.title:
            print("✅ Patients page loaded successfully")
        else:
            print("❌ Could not verify patients page")
            return False

        print("\n🎉 Application is up and running!")
        return True

    except Exception as e:
        print(f"❌ Application check failed with error: {e}")
        return False
    finally:
        if "driver" in locals():
            driver.quit()


if __name__ == "__main__":
    success = check_app()
    if not success:
        sys.exit(1)
