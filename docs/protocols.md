# SteadywellOS Clinical Protocols

This document describes the clinical protocols implemented in the SteadywellOS palliative care coordination platform.

## Protocol Structure

Each protocol in SteadywellOS consists of:

1. **Assessment Questions**: Structured symptom assessment questions with severity ratings
2. **Decision Tree**: Logic for determining interventions based on symptom severity
3. **Interventions**: Recommended clinical actions based on assessment findings
4. **Educational Materials**: Patient and caregiver education resources

## Implemented Protocols

### 1. Cancer Palliative Care Protocol

Designed for patients with advanced cancer to address pain, nausea, fatigue, and other common symptoms.

#### Assessment Areas

| Symptom | Assessment Scale | Intervention Threshold |
|---------|------------------|------------------------|
| Pain | 0-10 NRS | ≥7 Severe, 4-6 Moderate, <4 Mild |
| Pain Location | Text response | N/A |
| Nausea | 0-10 NRS | ≥7 Severe, 4-6 Moderate, <4 Mild |
| Vomiting | Frequency count | ≥3 episodes/24hrs Severe |
| Constipation | Days since BM | ≥3 days Intervention needed |
| Appetite | 0-10 NRS | ≤3 Poor appetite |
| Fatigue | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Dyspnea | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Anxiety/Depression | 0-10 NRS | ≥7 Severe, 4-6 Moderate |

#### Example Interventions

- **Severe Pain (≥7/10)**: Urgent review of medication regimen, consider opioid rotation or dose adjustment, breakthrough medication review
- **Moderate Pain (4-6/10)**: Review current analgesics, consider adjuvant medications, non-pharmacological approaches
- **Severe Nausea (≥7/10)**: Review antiemetic regimen, consider different class of antiemetics, evaluate for underlying causes

### 2. Heart Failure Palliative Care Protocol

Designed for patients with advanced heart failure to address dyspnea, edema, and activity intolerance.

#### Assessment Areas

| Symptom | Assessment Scale | Intervention Threshold |
|---------|------------------|------------------------|
| Dyspnea | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Orthopnea | Number of pillows | ≥3 pillows Severe |
| Edema | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Weight Change | Pounds gained | ≥3 lbs/week Intervention needed |
| Fatigue | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Chest Pain | Present/Absent | Present - Requires evaluation |
| Activity Tolerance | Minutes/Distance | <5 minutes - Severe limitation |

#### Example Interventions

- **Severe Dyspnea (≥7/10)**: Review diuretic dosage, consider supplemental oxygen assessment, position changes, anxiety management
- **Severe Edema (≥7/10)**: Increase diuretic dose, fluid restriction, daily weight monitoring, elevation of extremities
- **Chest Pain (Present)**: Evaluate for cardiac causes, consider nitroglycerin if prescribed, urgent medical review if new or changed

### 3. COPD Palliative Care Protocol

Designed for patients with advanced COPD to address respiratory symptoms, oxygen use, and anxiety related to breathing.

#### Assessment Areas

| Symptom | Assessment Scale | Intervention Threshold |
|---------|------------------|------------------------|
| Dyspnea | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Cough | 0-10 NRS | ≥7 Severe, 4-6 Moderate |
| Sputum Production | Amount description | Change in color or increase in amount |
| Sputum Color | Clear/White/Yellow/Green | Yellow/Green - Possible infection |
| Oxygen Use | Hours per day | >16 hours - High dependency |
| Activity Tolerance | Minutes/Distance | <5 minutes - Severe limitation |
| Respiratory Anxiety | 0-10 NRS | ≥7 Severe, 4-6 Moderate |

#### Example Interventions

- **Severe Dyspnea (≥7/10)**: Review bronchodilator use, breathing techniques, consider rescue medications if prescribed
- **Sputum Color Change (Yellow/Green)**: Evaluate for infection, consider antibiotic protocol
- **Severe Respiratory Anxiety (≥7/10)**: Breathing retraining, relaxation techniques, consider anxiolytic if severe

## Protocol Implementation Details

### JSON Structure

Protocols are stored in the database as JSON structures with the following format:

```json
{
  "name": "Cancer Palliative Care Protocol",
  "description": "Protocol for managing symptoms in patients with advanced cancer",
  "protocol_type": "cancer",
  "version": "1.0",
  "questions": [
    {
      "id": "pain_level",
      "text": "On a scale of 0 to 10, how would you rate your pain?",
      "type": "numeric",
      "required": true,
      "symptom_type": "pain",
      "min_value": 0,
      "max_value": 10
    },
    // Additional questions...
  ],
  "decision_tree": [
    {
      "id": "pain_assessment",
      "symptom_type": "pain",
      "condition": ">=7",
      "intervention_ids": ["severe_pain"]
    },
    // Additional decision nodes...
  ],
  "interventions": [
    {
      "id": "severe_pain",
      "title": "Severe Pain Management",
      "description": "Urgent review of pain medication...",
      "symptom_type": "pain",
      "severity_threshold": 7
    },
    // Additional interventions...
  ]
}
```

### Decision Tree Logic

The decision tree uses a simple condition-based system to evaluate symptoms and recommend interventions:

1. Each decision node specifies a symptom type (e.g., "pain")
2. The condition defines a comparison (e.g., ">=7")
3. If the condition is met, the specified interventions are recommended

Multiple decision nodes can apply to a single assessment, resulting in multiple intervention recommendations.

## Customizing Protocols

New protocols can be added through the admin interface or directly in the database. To create a new protocol:

1. Define the set of assessment questions
2. Create the decision tree logic
3. Define the intervention recommendations
4. Add the protocol to the database

## Protocol References

The protocols in SteadywellOS are based on established palliative care guidelines:

- NCCN Clinical Practice Guidelines in Oncology: Palliative Care
- American College of Cardiology/American Heart Association Heart Failure Guidelines
- Global Initiative for Chronic Obstructive Lung Disease (GOLD) Guidelines
- Telephone Triage Protocols for Nurses (5th Edition, Julie Briggs)

For clinical guidance on implementing these protocols, please consult with a palliative care specialist.
