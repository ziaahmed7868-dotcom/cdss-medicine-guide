import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Clinical Decision Support System (CDSS)",
    page_icon="💊",
    layout="wide",
)

# Custom Styling & Header Branding
st.markdown(
    """
    <style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
    }
    .sub-text {
        color: #4B5563;
        font-size: 14px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="main-header">💊 VALLE DEL CIELO - Clinical Decision Support System</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-text">Automated Drug Regimen & Inventory Routing System</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# Load CSV Files
@st.cache_data
def load_data():
  clinical_rules = pd.read_csv("Medicine_Guide_Master_Clinical_Rules.csv")
  brand_inv = pd.read_csv("Medicine_Guide_Brand_Inventory.csv")
  return clinical_rules, brand_inv


clinical_rules, brand_inv = load_data()

# Sidebar / Input Panel Layout
st.sidebar.header("📝 Patient Consultation Input")

# Patient Age Input
patient_age = st.sidebar.number_input(
    "Patient Age (Years)", min_value=0, max_value=120, value=25
)

# Extract unique indications for multi-select tags
all_indications = []
for ind_list in clinical_rules["Primary Indication"].dropna():
  for item in str(ind_list).split(","):
    cleaned_item = item.strip()
    if cleaned_item and cleaned_item not in all_indications:
      all_indications.append(cleaned_item)

selected_symptoms = st.sidebar.multiselect(
    "Select Symptoms / Indications", options=all_indications
)

# Risk Factors Inputs
st.sidebar.subheader("⚠️ Patient Risk Factors")
pregnancy_status = st.sidebar.selectbox("Pregnancy Status", ["No", "Yes"])
kidney_condition = st.sidebar.selectbox("Kidney Condition", ["Normal", "High Risk"])
heart_condition = st.sidebar.selectbox("Heart Condition", ["Normal", "High Risk"])

submit_btn = st.sidebar.button("Suggest Drug Regimen", type="primary")

# Main Dashboard Layout
if submit_btn:
  if not selected_symptoms:
    st.warning("Kripya kam se kam ek symptom select karein!")
  else:
    st.subheader("📋 Consultation & Regimen Results")

    # Filter rules based on symptoms, age, and safety constraints
    matched_rules = []
    for index, row in clinical_rules.iterrows():
      rule_indications = [
          i.strip().lower() for i in str(row["Primary Indication"]).split(",")
      ]

      # Check if any selected symptom matches rule indications
      match_found = any(
          any(s.lower() in ri or ri in s.lower() for ri in rule_indications)
          for s in selected_symptoms
      )

      if match_found:
        passes_safety = True

        # 1. Age Validation Check based on Min Age column
        min_age_str = str(row.get("Min Age", "0"))
        # Extract digits from string like '12 Years' or '18 Years'
        min_age_val = 0
        for part in min_age_str.split():
          if part.isdigit():
            min_age_val = int(part)
            break

        if patient_age < min_age_val:
          passes_safety = False  # Patient is too young for this drug

        # 2. Other Safety Filters
        if pregnancy_status == "Yes" and "Safe" not in str(
            row["Pregnancy Safety"]
        ):
          passes_safety = False
        if kidney_condition == "High Risk" and "Contraindicated" in str(
            row["Kidney Patient"]
        ):
          passes_safety = False
        if heart_condition == "High Risk" and "Contraindicated" in str(
            row["Heart Patient"]
        ):
          passes_safety = False

        if passes_safety:
          matched_rules.append(row)

    if matched_rules:
      result_df = pd.DataFrame(matched_rules)

      for idx, rule in result_df.iterrows():
        salt_id = rule["Salt ID"]
        generic_comp = rule["Generic Composition"]
        dosage = rule.get("Standard Dosage ", "Standard Adult Dosage")
        min_age_req = rule.get("Min Age", "N/A")

        # Fetch matching brands & rack info from Brand Inventory
        matched_brands = brand_inv[brand_inv["Salt ID (Linked)"] == salt_id]

        col1, col2 = st.columns([2, 1])

        with col1:
          st.success(f"**Recommended Salt:** {generic_comp}")
          st.write(
              f"**Standard Dosage:** {dosage if pd.notna(dosage) else 'As prescribed per clinical schedule'}"
          )
          st.write(f"**Minimum Age Requirement:** {min_age_req}")
          st.write(f"**Side Effects:** {rule['Primary Side Effects']}")

        with col2:
          st.info("**Stock & Rack Location**")
          if not matched_brands.empty:
            for _, brand in matched_brands.iterrows():
              brand_name = brand["Brand Name"]
              rack = (
                  brand["Rack Location"]
                  if pd.notna(brand["Rack Location"])
                  else "Rack-A1"
              )
              company = brand["Manufacturer / Company"]
              st.markdown(
                  f"* **{brand_name}** ({company})<br>📍 Location: **{rack}**",
                  unsafe_allow_html=True,
              )
          else:
            st.warning("No brand inventory linked.")
        st.markdown("---")
    else:
        st.error(
            "Koi bhi matching safe salt nahi mila jo di gayi age limit, risk"
            " factors aur symptoms ke anusaar safe ho."
        )
else:
  st.info(
      "Left sidebar se patient ki age, symptoms aur risk factors select karke"
      " 'Suggest Drug Regimen' button par click karein."
  )
    
