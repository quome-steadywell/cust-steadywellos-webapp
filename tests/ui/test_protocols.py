"""
Tests for protocol listing and details
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_protocols_page_loads(authenticated_driver, base_url):
    """Test that protocols page loads correctly"""
    driver = authenticated_driver
    driver.get(f"{base_url}/protocols")

    # Check the title
    assert "Protocols" in driver.title

    # Wait for protocol cards to load (they're loaded via AJAX)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "protocolCards"))
    )

    # Verify that multiple protocol cards exist
    protocol_cards = driver.find_elements(By.CLASS_NAME, "card")
    assert len(protocol_cards) > 0

    # Check if filter controls are present
    assert driver.find_element(By.ID, "protocolTypeFilter").is_displayed()
    assert driver.find_element(By.ID, "activeFilter").is_displayed()
    assert driver.find_element(By.ID, "applyFilters").is_displayed()


def test_protocol_filtering(authenticated_driver, base_url):
    """Test protocol filtering functionality"""
    driver = authenticated_driver
    driver.get(f"{base_url}/protocols")

    # Wait for protocol cards to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "protocolCards"))
    )

    # Get initial count of protocols
    initial_cards = driver.find_elements(By.CLASS_NAME, "card-header")
    initial_count = len(initial_cards)

    # Apply filter for Cancer protocols
    protocol_type_filter = driver.find_element(By.ID, "protocolTypeFilter")
    protocol_type_filter.click()

    # Select Cancer option from dropdown
    cancer_option = driver.find_element(By.XPATH, "//option[@value='cancer']")
    cancer_option.click()

    # Click Apply Filters button
    apply_button = driver.find_element(By.ID, "applyFilters")
    apply_button.click()

    # Wait for filtered results
    time.sleep(2)

    # Check filtered results
    filtered_cards = driver.find_elements(By.CLASS_NAME, "card-header")

    # Verify we have fewer results or at least not more
    assert len(filtered_cards) <= initial_count

    # Check if filtered results contain "Cancer" text
    for card in filtered_cards:
        assert "Cancer" in card.text


def test_protocol_details(authenticated_driver, base_url):
    """Test protocol details page"""
    driver = authenticated_driver
    driver.get(f"{base_url}/protocols")

    # Wait for protocol cards to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "protocolCards"))
    )

    # Click the first View button to open protocol details
    view_button = driver.find_element(By.XPATH, "//a[contains(text(), 'View')]")
    view_button.click()

    # Wait for protocol details page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "protocolOverview"))
    )

    # Check for protocol components
    assert driver.find_element(By.ID, "questionsContainer").is_displayed()
    assert driver.find_element(By.ID, "interventionsContainer").is_displayed()
    assert driver.find_element(By.ID, "decisionTreeContainer").is_displayed()

    # Check for back button
    back_button = driver.find_element(
        By.XPATH, "//a[contains(text(), 'Back to Protocols')]"
    )
    assert back_button.is_displayed()
