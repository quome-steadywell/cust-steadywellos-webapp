"""
Tests for login functionality
"""
import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_login_page_loads(driver, base_url):
    """Test that login page loads correctly"""
    driver.get(f"{base_url}/login")
    
    # Wait for the page to load
    time.sleep(2)
    
    # Check that we're on the login page
    assert "Login" in driver.title or "Sign In" in driver.title
    
    # Check for login form elements
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    
    assert username_field.is_displayed()
    assert password_field.is_displayed()
    assert submit_button.is_displayed()

def test_login_with_valid_credentials(driver, base_url):
    """Test login with valid credentials"""
    driver.get(f"{base_url}/login")
    
    # Wait for the page to load
    time.sleep(2)
    
    # Enter username and password
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    
    username_field.send_keys("admin")
    password_field.send_keys("password123")
    submit_button.click()
    
    # Wait for redirect
    time.sleep(3)
    
    # Check if we've been redirected to dashboard
    assert "/dashboard" in driver.current_url or "Dashboard" in driver.title