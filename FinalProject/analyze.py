# MAKE SURE PYTHON TYPE CHECKING IS DISABLED IN YOUR IDE IF USING VSCODE
import os
from rdflib import Graph, Namespace, RDF, RDFS, Literal
from rdflib.namespace import XSD
from ucimlrepo import fetch_ucirepo

def get_iri_by_label(g, label):
    for s, p, o in g.triples((None, RDFS.label, Literal(label, lang="en"))):
        return s
    return None

# load ontology files
script_dir = os.path.dirname(os.path.abspath(__file__))
ontology_path = os.path.join(script_dir, "HeartDiseaseOntology_Reference.ttl")
application_path = os.path.join(script_dir, "HeartDiseaseOntology_Application.ttl")
g = Graph()
g.parse(ontology_path, format="turtle")
g.parse(application_path, format="turtle")
HDO_APP = Namespace("https://ontology.jhu.edu/aaronelkin/2026/3/HeartDiseaseOntology_application/")

# pull in all relevant classes
patient_in_study = get_iri_by_label(g, "patient in heart disease study")
heart_disease_present = get_iri_by_label(g, "heart disease present")
heart_disease_absent = get_iri_by_label(g, "heart disease absent")
male_patient = get_iri_by_label(g, "male patient")
female_patient = get_iri_by_label(g, "female patient")
typical_angina = get_iri_by_label(g, "typical angina")
atypical_angina = get_iri_by_label(g, "atypical angina")
non_anginal_pain = get_iri_by_label(g, "non-anginal pain")
asymptomatic = get_iri_by_label(g, "asymptomatic")
elevated_blood_sugar = get_iri_by_label(g, "elevated blood sugar")
normal_blood_sugar = get_iri_by_label(g, "normal blood sugar")
normal_ecg = get_iri_by_label(g, "normal electrocardiogram")
stt_abnormality = get_iri_by_label(g, "ST-T wave abnormality")
lv_hypertrophy = get_iri_by_label(g, "probable or definite left ventricular hypertrophy")
exercise_angina_present = get_iri_by_label(g, "exercise induced angina present")
exercise_angina_absent  = get_iri_by_label(g, "exercise induced angina absent")
upsloping = get_iri_by_label(g, "upsloping ST slope test result")
flat = get_iri_by_label(g, "flat ST slope test result")
downsloping = get_iri_by_label(g, "downsloping ST slope test result")
normal_thal = get_iri_by_label(g, "normal thallium")
fixed_defect = get_iri_by_label(g, "fixed defect thallium")
reversible_defect  = get_iri_by_label(g, "reversible defect thallium")

#Object properties
has_age = get_iri_by_label(g, "has age")
has_bp = get_iri_by_label(g, "has resting blood pressure")
has_chol = get_iri_by_label(g, "has cholesterol")
has_hr = get_iri_by_label(g, "has maximum heart rate achieved")
has_st_depression  = get_iri_by_label(g, "has ST depression")
has_diagnosis = get_iri_by_label(g, "has diagnosis")
has_symptom = get_iri_by_label(g, "has symptom")
has_clinical_result = get_iri_by_label(g, "has clinical result")

#UCI dataset
heart_disease = fetch_ucirepo(id=45)
X = heart_disease.data.features
y = heart_disease.data.targets
print(f"Dataset loaded: {len(X)} patients")

# Map classes to attribtues in the dataset
cp_map = { 1: typical_angina, 2: atypical_angina, 3: non_anginal_pain, 4: asymptomatic }
fbs_map = { 1: elevated_blood_sugar, 0: normal_blood_sugar }
restecg_map = { 0: normal_ecg, 1: lv_hypertrophy, 2: stt_abnormality }
exang_map = { 1: exercise_angina_present, 0: exercise_angina_absent }
slope_map = { 1: upsloping, 2: flat, 3: downsloping }
thal_map  = { 3: normal_thal, 6: fixed_defect, 7: reversible_defect }

for i, (feat_row, targ_row) in enumerate(zip(X.itertuples(), y.itertuples())):
    patient = HDO_APP[f"patient_{i}"]

    g.add((patient, RDF.type, patient_in_study))

    sex_class = male_patient if feat_row.sex == 1 else female_patient
    g.add((patient, RDF.type, sex_class))

    diag_num = targ_row.num if hasattr(targ_row, 'num') else getattr(targ_row, '_1', 0)
    diag_class = heart_disease_present if diag_num > 0 else heart_disease_absent
    g.add((patient, has_diagnosis, diag_class))

    if feat_row.age is not None:
        g.add((patient, has_age, Literal(int(feat_row.age), datatype=XSD.integer)))
    if feat_row.trestbps is not None:
        g.add((patient, has_bp, Literal(int(feat_row.trestbps), datatype=XSD.integer)))
    if feat_row.chol is not None:
        g.add((patient, has_chol, Literal(int(feat_row.chol), datatype=XSD.integer)))
    if feat_row.thalach is not None:
        g.add((patient, has_hr, Literal(int(feat_row.thalach), datatype=XSD.integer)))
    if feat_row.oldpeak is not None:
        g.add((patient, has_st_depression, Literal(float(feat_row.oldpeak), datatype=XSD.decimal)))

    if cp_class := cp_map.get(feat_row.cp):
        g.add((patient, has_symptom, cp_class))
    if fbs_class := fbs_map.get(feat_row.fbs):
        g.add((patient, has_clinical_result, fbs_class))
    if ecg_class := restecg_map.get(feat_row.restecg):
        g.add((patient, has_clinical_result, ecg_class))
    if exang_class := exang_map.get(feat_row.exang):
        g.add((patient, has_symptom, exang_class))
    if slope_class := slope_map.get(feat_row.slope):
        g.add((patient, has_clinical_result, slope_class))
    if thal_class := thal_map.get(feat_row.thal):
        g.add((patient, has_clinical_result, thal_class))


# COMPETENCY QUESTION 1
# Given a patient's clinical profile, how many similar patients had heart disease present?
# Specific test case: elevated blood sugar + typical angina
print("=" * 60)
print("Given a patient with elevated blood sugar and typical angina,")
print("how many similar patients had heart disease present vs absent?")
print("=" * 60)

query1 = f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?diagnosisLabel (COUNT(?patient) AS ?count)
WHERE {{
    ?patient rdf:type <{patient_in_study}> .
    ?patient <{has_clinical_result}> <{elevated_blood_sugar}> .
    ?patient <{has_symptom}> <{typical_angina}> .
    ?patient <{has_diagnosis}> ?diagnosis .
    ?diagnosis rdfs:label ?diagnosisLabel .
}}
GROUP BY ?diagnosisLabel
ORDER BY ?diagnosisLabel
"""

results1 = g.query(query1)
for row in results1:
    print(f"  {row.diagnosisLabel}: {int(row['count'])} patients")

# COMPETENCY QUESTION 2
# What is the relationship between a clinical result and heart disease?
# Specific test case: reversible defect thallium
print()
print("=" * 60)
print("What is the relationship between reversible defect thallium")
print("and heart disease diagnosis?")
print("=" * 60)

query2 = f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?diagnosisLabel (COUNT(?patient) AS ?count)
WHERE {{
    ?patient rdf:type <{patient_in_study}> .
    ?patient <{has_clinical_result}> <{reversible_defect}> .
    ?patient <{has_diagnosis}> ?diagnosis .
    ?diagnosis rdfs:label ?diagnosisLabel .
}}
GROUP BY ?diagnosisLabel
ORDER BY ?diagnosisLabel
"""

results2 = g.query(query2)
for row in results2:
    print(f"  {row.diagnosisLabel}: {int(row['count'])} patients")