"""
Tests for assessment functionality
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def test_assessment_creation_page_loads(authenticated_driver, base_url):
    """Test that new assessment page loads correctly"""
    driver = authenticated_driver

    # Navigate to patients page first to get a patient ID
    driver.get(f"{base_url}/patients")

    # Wait for patient data to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Get the first patient's ID from the view button
    view_button = driver.find_element(By.CLASS_NAME, "view-patient")
    patient_id = view_button.get_attribute("data-id")

    # Navigate to new assessment page for this patient
    driver.get(f"{base_url}/assessments/new?patient_id={patient_id}")

    # Check that the assessment form loads
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "assessmentForm")))

    # Verify key components are present
    assert driver.find_element(By.ID, "patientInfo").is_displayed()
    assert driver.find_element(By.ID, "protocolInfo").is_displayed()
    assert driver.find_element(By.ID, "questionContainer").is_displayed()
    assert driver.find_element(By.ID, "generateBtn").is_displayed()


def test_assessment_question_interaction(authenticated_driver, base_url):
    """Test interaction with assessment questions"""
    driver = authenticated_driver

    # Navigate to patients page first to get a patient ID
    driver.get(f"{base_url}/patients")

    # Wait for patient data to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Get the first patient's ID from the view button
    view_button = driver.find_element(By.CLASS_NAME, "view-patient")
    patient_id = view_button.get_attribute("data-id")

    # Navigate to new assessment page for this patient
    driver.get(f"{base_url}/assessments/new?patient_id={patient_id}")

    # Wait for questions to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "questionContainer")))

    # Wait a bit for the dynamic question rendering
    time.sleep(3)

    # Try to interact with range inputs
    range_inputs = driver.find_elements(By.XPATH, "//input[@type='range']")
    if range_inputs:
        # Move the slider to a value of 7 (for testing severe symptoms)
        slider = range_inputs[0]

        # Use ActionChains to move the slider
        action = ActionChains(driver)
        action.click_and_hold(slider).move_by_offset(50, 0).release().perform()

        # Check if the value display was updated
        slider_id = slider.get_attribute("id")
        value_display = driver.find_element(By.ID, f"{slider_id}_value")

        # The value should be greater than the initial value
        assert int(value_display.text) > 0

    # Try to interact with radio buttons (yes/no questions)
    radio_buttons = driver.find_elements(By.XPATH, "//input[@type='radio']")
    if radio_buttons:
        # Click the "Yes" option on the first boolean question
        radio_buttons[0].click()
        assert radio_buttons[0].is_selected()

    # Try to interact with text inputs
    text_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    if text_inputs:
        # Enter text in the first text input
        text_inputs[0].send_keys("Test symptom response")
        assert text_inputs[0].get_attribute("value") == "Test symptom response"


def test_assessment_ai_recommendations(authenticated_driver, base_url):
    """Test AI recommendations generation"""
    driver = authenticated_driver

    # Navigate to patients page first to get a patient ID
    driver.get(f"{base_url}/patients")

    # Wait for patient data to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "patientTableBody")))

    # Get the first patient's ID from the view button
    view_button = driver.find_element(By.CLASS_NAME, "view-patient")
    patient_id = view_button.get_attribute("data-id")

    # Navigate to new assessment page for this patient
    driver.get(f"{base_url}/assessments/new?patient_id={patient_id}")

    # Wait for questions to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "questionContainer")))

    # Wait a bit for the dynamic question rendering
    time.sleep(3)

    # Fill in required fields
    # Set slider values to 7+ to trigger interventions
    range_inputs = driver.find_elements(By.XPATH, "//input[@type='range']")
    for slider in range_inputs:
        # Move slider to a value of 8 (severe)
        action = ActionChains(driver)
        action.click_and_hold(slider).move_by_offset(80, 0).release().perform()

    # Set radio buttons (yes/no)
    radio_yes_buttons = driver.find_elements(By.XPATH, "//input[@value='true']")
    for radio in radio_yes_buttons:
        radio.click()

    # Fill text inputs
    text_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    for text_input in text_inputs:
        text_input.send_keys("Test symptom description")

    # Click Generate AI Recommendations button
    generate_button = driver.find_element(By.ID, "generateBtn")
    generate_button.click()

    # Wait for AI recommendations to appear
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "aiRecommendationsCard")))

    # Verify AI content and interventions are shown
    assert driver.find_element(By.ID, "aiContent").is_displayed()
    assert driver.find_element(By.ID, "interventionsList").is_displayed()

    # Check if interventions list contains content
    interventions_list = driver.find_element(By.ID, "interventionsList")
    assert interventions_list.text.strip() != ""
