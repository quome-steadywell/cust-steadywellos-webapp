"""
Test configuration for SteadwellOS palliative care platform
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session")
def driver():
    """
    Initialize a WebDriver instance for the tests.
    This fixture is shared across all tests in the session.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Set an implicit wait of 10 seconds
    driver.implicitly_wait(10)
    
    # Return the driver instance
    yield driver
    
    # Quit the driver when tests are done
    driver.quit()

@pytest.fixture(scope="session")
def base_url():
    """
    Return the base URL for the application.
    """
    return "http://0.0.0.0:8080"

@pytest.fixture(scope="function")
def authenticated_driver(driver, base_url):
    """
    Create a WebDriver instance that is authenticated
    """
    driver.get(f"{base_url}/login")
    
    # Wait for the login page to load
    time.sleep(2)
    
    # Enter username and password
    username_field = driver.find_element("id", "username")
    password_field = driver.find_element("id", "password")
    submit_button = driver.find_element("xpath", "//button[@type='submit']")
    
    username_field.send_keys("admin")
    password_field.send_keys("password123")
    submit_button.click()
    
    # Wait for login to complete and dashboard to load
    time.sleep(2)
    
    yield driver