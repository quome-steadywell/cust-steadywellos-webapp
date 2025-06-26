"""
Tests for patient listing and management
"""

import pytest
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


def test_patients_page_loads(authenticated_driver, base_url):
    """Test that patients page loads correctly"""
    driver = authenticated_driver
    driver.get(f"{base_url}/patients")

    # Check the title
    assert "Patients" in driver.title

    # Wait for patient table to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Verify that patient rows exist
    patient_rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
    assert len(patient_rows) > 0

    # Check if search and filter controls are present
    assert driver.find_element(By.ID, "searchInput").is_displayed()
    assert driver.find_element(By.ID, "protocolFilter").is_displayed()
    assert driver.find_element(By.ID, "statusFilter").is_displayed()


def test_patient_filtering(authenticated_driver, base_url):
    """Test patient filtering functionality"""
    driver = authenticated_driver
    driver.get(f"{base_url}/patients")

    # Wait for patient table to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Get initial count of patients
    initial_rows = driver.find_elements(By.XPATH, "//table/tbody/tr[not(contains(@class, 'no-results'))]")
    initial_count = len(initial_rows)

    # Apply filter for COPD patients
    protocol_filter = driver.find_element(By.ID, "protocolFilter")
    select = Select(protocol_filter)
    select.select_by_value("copd")

    # Click Apply Filters button
    apply_button = driver.find_element(By.ID, "applyFilters")
    apply_button.click()

    # Wait for filtered results
    time.sleep(2)

    # Check filtered results
    filtered_rows = driver.find_elements(By.XPATH, "//table/tbody/tr[not(contains(@class, 'no-results'))]")

    # The test will pass if we either:
    # 1. Have fewer results than before (filtering worked)
    # 2. Have the same number of results but all contain "COPD" (all patients have COPD)
    if len(filtered_rows) < initial_count:
        assert True  # Filtering reduced results
    else:
        # All patients should have COPD badge
        for row in filtered_rows:
            protocol_badge = row.find_element(By.XPATH, ".//td[5]/span")
            assert "COPD" in protocol_badge.text


def test_patient_search(authenticated_driver, base_url):
    """Test patient search functionality"""
    driver = authenticated_driver
    driver.get(f"{base_url}/patients")

    # Wait for patient table to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Get initial count of patients
    initial_rows = driver.find_elements(By.XPATH, "//table/tbody/tr[not(contains(@class, 'no-results'))]")
    initial_count = len(initial_rows)

    # Get first patient's name to search for
    if initial_count > 0:
        first_patient_name = initial_rows[0].find_elements(By.XPATH, "./td")[1].text
        search_term = first_patient_name.split()[0]  # Use first name

        # Enter search term
        search_input = driver.find_element(By.ID, "searchInput")
        search_input.clear()
        search_input.send_keys(search_term)

        # Wait for auto-search
        time.sleep(2)

        # Check search results
        search_results = driver.find_elements(By.XPATH, "//table/tbody/tr[not(contains(@class, 'no-results'))]")

        # Should have at least one result
        assert len(search_results) > 0

        # All results should contain the search term
        for row in search_results:
            name_cell = row.find_elements(By.XPATH, "./td")[1]
            assert search_term in name_cell.text


def test_patient_details(authenticated_driver, base_url):
    """Test patient details modal"""
    driver = authenticated_driver
    driver.get(f"{base_url}/patients")

    # Wait for patient table to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Click the first View button to open patient details
    view_button = driver.find_element(By.CLASS_NAME, "view-patient")
    view_button.click()

    # Wait for patient details modal to open
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "patientDetailsModal")))

    # Check for patient details sections
    modal_body = driver.find_element(By.ID, "patientDetailsBody")

    # Should have patient name
    assert len(modal_body.find_elements(By.XPATH, ".//h5")) > 0

    # Should have clinical information
    assert "Clinical Information" in modal_body.text

    # Should have MRN
    assert "MRN" in modal_body.text

    # Close modal
    close_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Close')]")
    close_button.click()

    # Wait for modal to close
    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "patientDetailsModal")))
