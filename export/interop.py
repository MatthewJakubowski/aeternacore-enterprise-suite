import json
from core.models import CompleteLabProfile

class MedicalInteroperabilityEngine:
    @staticmethod
    def generate_fhir_r4(res: dict) -> str:
        p: CompleteLabProfile = res["profile"]
        specimen_uid = "AET-2026-KL99120"
        bundle = {
            "resourceType": "Bundle",
            "id": f"BUNDLE-{specimen_uid}",
            "identifier": {"system": "https://aeternacore.med.pl/bundles", "value": specimen_uid},
            "type": "document",
            "timestamp": res["timestamp"],
            "entry": [
                {
                    "fullUrl": "urn:uuid:composition-01",
                    "resource": {
                        "resourceType": "Composition",
                        "id": "composition-01",
                        "status": "final",
                        "type": {"coding": [{"system": "http://loinc.org", "code": "11502-2", "display": "Laboratory report"}]},
                        "subject": {"display": f"Patient Age: {p.age:.0f}, Sex: {p.sex}"},
                        "date": res["timestamp"],
                        "author": [{"display": "Mateusz Jakubowski - Senior Medical Technologist"}],
                        "title": "Clinical Diagnostic & Longevity Evaluation",
                        "section": [
                            {
                                "title": "LIS ISO 15189 Quality Control",
                                "code": {"coding": [{"system": "http://loinc.org", "code": "93832-4", "display": "Quality control summary"}]},
                                "text": {"status": "generated", "div": f"<div>LIS Verdict: {res['autoval_verdict']} | HIL: {p.hil_status}</div>"}
                            },
                            {
                                "title": "Phenotypic Biomarkers",
                                "code": {"coding": [{"system": "http://loinc.org", "code": "67704-7", "display": "Biometric summary"}]},
                                "entry": [{"reference": "urn:uuid:obs-phenoage"}]
                            }
                        ]
                    }
                },
                {
                    "fullUrl": "urn:uuid:obs-phenoage",
                    "resource": {
                        "resourceType": "Observation",
                        "id": "obs-phenoage",
                        "status": "final",
                        "code": {"coding": [{"system": "http://loinc.org", "code": "99100-1", "display": "Levine PhenoAge"}]},
                        "valueQuantity": {"value": res["pheno_age"], "unit": "years", "system": "http://unitsofmeasure.org", "code": "a"}
                    }
                }
            ]
        }
        return json.dumps(bundle, indent=2, ensure_ascii=False)

    @staticmethod
    def generate_edm_xml(res: dict) -> str:
        p: CompleteLabProfile = res["profile"]
        ts_clean = res['timestamp'].replace('-', '').replace(':', '').replace(' ', '')
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" moodCode="EVN">
  <realmCode code="PL"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.3.4424.13.10.3.1"/>
  <id root="2.16.840.1.113883.3.4424.13" extension="AET-2026-KL99120"/>
  <code code="11502-2" codeSystem="2.16.840.1.113883.6.1" displayName="Sprawozdanie z badania laboratoryjnego"/>
  <title>AeternaCore Enterprise - Sprawozdanie Laboratoryjne</title>
  <effectiveTime value="{ts_clean}"/>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="93832-4" codeSystem="2.16.840.1.113883.6.1" displayName="Podsumowanie Kontroli Jakości LIS"/>
          <text>
            Status LIS: {res['autoval_verdict']}
            Wiek Metrykalny: {p.age} | PhenoAge: {res['pheno_age']} | DunedinPACE: {res['dunedin_pace']}
            eGFR (CKD-EPI 2021): {res['egfr']} ml/min | FIB-4: {res['fib4']} | ApoB: {p.apob_mg_dl} mg/dL
          </text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

    @staticmethod
    def generate_research_csv(res: dict) -> str:
        p: CompleteLabProfile = res["profile"]
        headers = "timestamp,specimen_uid,chrono_age,pheno_age,bio_delta,dunedin_pace,egfr,fib4,score2_pct,tyg_index,apob\n"
        row = f"{res['timestamp']},AET-2026-KL99120,{p.age},{res['pheno_age']},{res['age_delta']},{res['dunedin_pace']},{res['egfr']},{res['fib4']},{res['score2_pct']},{res['tyg_index']},{p.apob_mg_dl}"
        return headers + row
