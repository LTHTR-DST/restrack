# sql server CDM DDL Specification for OMOP Common Data Model 5.4

from datetime import date, datetime
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


# HINT DISTRIBUTE ON KEY (person_id)
class PERSON(SQLModel, table=True):
    person_id: int = Field(default=None, primary_key=True)
    gender_concept_id: int
    year_of_birth: int
    month_of_birth: Optional[int]
    day_of_birth: Optional[int]
    birth_datetime: Optional[datetime]
    race_concept_id: int
    ethnicity_concept_id: int
    location_id: Optional[int]
    provider_id: Optional[int]
    care_site_id: Optional[int]
    person_source_value: Optional[str] = Field(max_length=50)
    gender_source_value: Optional[str] = Field(max_length=50)
    gender_source_concept_id: Optional[int]
    race_source_value: Optional[str] = Field(max_length=50)
    race_source_concept_id: Optional[int]
    ethnicity_source_value: Optional[str] = Field(max_length=50)
    ethnicity_source_concept_id: Optional[int]


# HINT DISTRIBUTE ON KEY (person_id)
class OBSERVATION_PERIOD(SQLModel, table=True):
    observation_period_id: int = Field(default=None, primary_key=True)
    person_id: int
    observation_period_start_date: date
    observation_period_end_date: date
    period_type_concept_id: int


# HINT DISTRIBUTE ON KEY (person_id)
class VISIT_OCCURRENCE(SQLModel, table=True):
    visit_occurrence_id: int = Field(default=None, primary_key=True)
    person_id: int
    visit_concept_id: int
    visit_start_date: date
    visit_start_datetime: Optional[datetime]
    visit_end_date: date
    visit_end_datetime: Optional[datetime]
    visit_type_concept_id: int
    provider_id: Optional[int]
    care_site_id: Optional[int]
    visit_source_value: Optional[str] = Field(max_length=50)
    visit_source_concept_id: Optional[int]
    admitted_from_concept_id: Optional[int]
    admitted_from_source_value: Optional[str] = Field(max_length=50)
    discharged_to_concept_id: Optional[int]
    discharged_to_source_value: Optional[str] = Field(max_length=50)
    preceding_visit_occurrence_id: Optional[int]


# HINT DISTRIBUTE ON KEY (person_id)
class VISIT_DETAIL(SQLModel, table=True):
    visit_detail_id: int = Field(default=None, primary_key=True)
    person_id: int
    visit_detail_concept_id: int
    visit_detail_start_date: date
    visit_detail_start_datetime: Optional[datetime]
    visit_detail_end_date: date
    visit_detail_end_datetime: Optional[datetime]
    visit_detail_type_concept_id: int
    provider_id: Optional[int]
    care_site_id: Optional[int]
    visit_detail_source_value: Optional[str] = Field(max_length=50)
    visit_detail_source_concept_id: Optional[int]
    admitted_from_concept_id: Optional[int]
    admitted_from_source_value: Optional[str] = Field(max_length=50)
    discharged_to_source_value: Optional[str] = Field(max_length=50)
    discharged_to_concept_id: Optional[int]
    preceding_visit_detail_id: Optional[int]
    parent_visit_detail_id: Optional[int]
    visit_occurrence_id: int


# HINT DISTRIBUTE ON KEY (person_id)
class CONDITION_OCCURRENCE(SQLModel, table=True):
    condition_occurrence_id: int = Field(default=None, primary_key=True)
    person_id: int
    condition_concept_id: int
    condition_start_date: date
    condition_start_datetime: Optional[datetime]
    condition_end_date: Optional[date]
    condition_end_datetime: Optional[datetime]
    condition_type_concept_id: int
    condition_status_concept_id: Optional[int]
    stop_reason: Optional[str] = Field(max_length=20)
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    condition_source_value: Optional[str] = Field(max_length=50)
    condition_source_concept_id: Optional[int]
    condition_status_source_value: Optional[str] = Field(max_length=50)


# HINT DISTRIBUTE ON KEY (person_id)
class DRUG_EXPOSURE(SQLModel, table=True):
    drug_exposure_id: int = Field(default=None, primary_key=True)
    person_id: int
    drug_concept_id: int
    drug_exposure_start_date: date
    drug_exposure_start_datetime: Optional[datetime]
    drug_exposure_end_date: date
    drug_exposure_end_datetime: Optional[datetime]
    verbatim_end_date: Optional[date]
    drug_type_concept_id: int
    stop_reason: Optional[str] = Field(max_length=20)
    refills: Optional[int]
    quantity: Optional[float]
    days_supply: Optional[int]
    sig: Optional[str]
    route_concept_id: Optional[int]
    lot_number: Optional[str] = Field(max_length=50)
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    drug_source_value: Optional[str] = Field(max_length=50)
    drug_source_concept_id: Optional[int]
    route_source_value: Optional[str] = Field(max_length=50)
    dose_unit_source_value: Optional[str] = Field(max_length=50)


# HINT DISTRIBUTE ON KEY (person_id)
class PROCEDURE_OCCURRENCE(SQLModel, table=True):
    procedure_occurrence_id: int = Field(default=None, primary_key=True)
    person_id: int
    procedure_concept_id: int
    procedure_date: date
    procedure_datetime: Optional[datetime]
    procedure_end_date: Optional[date]
    procedure_end_datetime: Optional[datetime]
    procedure_type_concept_id: int
    modifier_concept_id: Optional[int]
    quantity: Optional[int]
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    procedure_source_value: Optional[str] = Field(max_length=50)
    procedure_source_concept_id: Optional[int]
    modifier_source_value: Optional[str] = Field(max_length=50)


# HINT DISTRIBUTE ON KEY (person_id)
class DEVICE_EXPOSURE(SQLModel, table=True):
    device_exposure_id: int = Field(default=None, primary_key=True)
    person_id: int
    device_concept_id: int
    device_exposure_start_date: date
    device_exposure_start_datetime: Optional[datetime]
    device_exposure_end_date: Optional[date]
    device_exposure_end_datetime: Optional[datetime]
    device_type_concept_id: int
    unique_device_id: Optional[str] = Field(max_length=255)
    production_id: Optional[str] = Field(max_length=255)
    quantity: Optional[int]
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    device_source_value: Optional[str] = Field(max_length=50)
    device_source_concept_id: Optional[int]
    unit_concept_id: Optional[int]
    unit_source_value: Optional[str] = Field(max_length=50)
    unit_source_concept_id: Optional[int]


# HINT DISTRIBUTE ON KEY (person_id)
class MEASUREMENT(SQLModel, table=True):
    measurement_id: int = Field(default=None, primary_key=True)
    person_id: int
    measurement_concept_id: int
    measurement_date: date
    measurement_datetime: Optional[datetime]
    measurement_time: Optional[str] = Field(max_length=10)
    measurement_type_concept_id: int
    operator_concept_id: Optional[int]
    value_as_number: Optional[float]
    value_as_concept_id: Optional[int]
    unit_concept_id: Optional[int]
    range_low: Optional[float]
    range_high: Optional[float]
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    measurement_source_value: Optional[str] = Field(max_length=50)
    measurement_source_concept_id: Optional[int]
    unit_source_value: Optional[str] = Field(max_length=50)
    unit_source_concept_id: Optional[int]
    value_source_value: Optional[str] = Field(max_length=50)
    measurement_event_id: Optional[int]
    meas_event_field_concept_id: Optional[int]

    model_config = ConfigDict(arbitrary_types_allowed=True)


# HINT DISTRIBUTE ON KEY (person_id)
class OBSERVATION(SQLModel, table=True):
    observation_id: int = Field(default=None, primary_key=True)
    person_id: int
    observation_concept_id: int
    observation_date: date
    observation_datetime: Optional[datetime]
    observation_type_concept_id: int
    value_as_number: Optional[float]
    value_as_string: Optional[str] = Field(max_length=60)
    value_as_concept_id: Optional[int]
    qualifier_concept_id: Optional[int]
    unit_concept_id: Optional[int]
    provider_id: Optional[int]
    visit_occurrence_id: Optional[int]
    visit_detail_id: Optional[int]
    observation_source_value: Optional[str] = Field(max_length=50)
    observation_source_concept_id: Optional[int]
    unit_source_value: Optional[str] = Field(max_length=50)
    qualifier_source_value: Optional[str] = Field(max_length=50)
    value_source_value: Optional[str] = Field(max_length=50)
    observation_event_id: Optional[int]
    obs_event_field_concept_id: Optional[int]

    model_config = ConfigDict(arbitrary_types_allowed=True)


# HINT DISTRIBUTE ON KEY (person_id)
class DEATH(SQLModel, table=True):
    person_id: int = Field(default=None, primary_key=True)
    death_date: date
    death_datetime: Optional[datetime]
    death_type_concept_id: Optional[int]
    cause_concept_id: Optional[int]
    cause_source_value: Optional[str] = Field(max_length=50)
    cause_source_concept_id: Optional[int]


# # HINT DISTRIBUTE ON KEY (person_id)
# class NOTE(SQLModel, table=True):
#     note_id: int = Field(default=None, primary_key=True)
#     person_id: int
#     note_date: date
#     note_datetime: Optional[datetime]
#     note_type_concept_id: int
#     note_class_concept_id: int
#     note_title: Optional[str] = Field(max_length=250)
#     note_text: str
#     encoding_concept_id: int
#     language_concept_id: int
#     provider_id: Optional[int]
#     visit_occurrence_id: Optional[int]
#     visit_detail_id: Optional[int]
#     note_source_value: Optional[str] = Field(max_length=50)
#     note_event_id: Optional[int]
#     note_event_field_concept_id: Optional[int]

# # HINT DISTRIBUTE ON RANDOM
# class NOTE_NLP(SQLModel, table=True):
#     note_nlp_id: int = Field(default=None, primary_key=True)
#     note_id: int
#     section_concept_id: Optional[int]
#     snippet: Optional[str] = Field(max_length=250)
#     offset:  Optional[str] = Field(max_length=50)
#     lexical_variant: str = Field(max_length=250)
#     note_nlp_concept_id: Optional[int]
#     note_nlp_source_concept_id: Optional[int]
#     nlp_system: Optional[str] = Field(max_length=250)
#     nlp_date: date
#     nlp_datetime: Optional[datetime]
#     term_exists: Optional[str] = Field(max_length=1)
#     term_temporal: Optional[str] = Field(max_length=50)
#     term_modifiers: Optional[str] = Field(max_length=2000)


# HINT DISTRIBUTE ON KEY (person_id)
class SPECIMEN(SQLModel, table=True):
    specimen_id: int = Field(default=None, primary_key=True)
    person_id: int
    specimen_concept_id: int
    specimen_type_concept_id: int
    specimen_date: date
    specimen_datetime: Optional[datetime]
    quantity: Optional[float]
    unit_concept_id: Optional[int]
    anatomic_site_concept_id: Optional[int]
    disease_status_concept_id: Optional[int]
    specimen_source_id: Optional[str] = Field(max_length=50)
    specimen_source_value: Optional[str] = Field(max_length=50)
    unit_source_value: Optional[str] = Field(max_length=50)
    anatomic_site_source_value: Optional[str] = Field(max_length=50)
    disease_status_source_value: Optional[str] = Field(max_length=50)


# HINT DISTRIBUTE ON RANDOM
# class FACT_RELATIONSHIP(SQLModel, table=True):
#     domain_concept_id_1: int
#     fact_id_1: int
#     domain_concept_id_2: int
#     fact_id_2: int
#     relationship_concept_id: int


# HINT DISTRIBUTE ON RANDOM
class LOCATION(SQLModel, table=True):
    location_id: int = Field(default=None, primary_key=True)
    address_1: Optional[str] = Field(max_length=50)
    address_2: Optional[str] = Field(max_length=50)
    city: Optional[str] = Field(max_length=50)
    state: Optional[str] = Field(max_length=2)
    zip: Optional[str] = Field(max_length=9)
    county: Optional[str] = Field(max_length=20)
    location_source_value: Optional[str] = Field(max_length=50)
    country_concept_id: Optional[int]
    country_source_value: Optional[str] = Field(max_length=80)
    latitude: Optional[float]
    longitude: Optional[float]


# HINT DISTRIBUTE ON RANDOM
class CARE_SITE(SQLModel, table=True):
    care_site_id: int = Field(default=None, primary_key=True)
    care_site_name: Optional[str] = Field(max_length=255)
    place_of_service_concept_id: Optional[int]
    location_id: Optional[int]
    care_site_source_value: Optional[str] = Field(max_length=50)
    place_of_service_source_value: Optional[str] = Field(max_length=50)


# HINT DISTRIBUTE ON RANDOM
class PROVIDER(SQLModel, table=True):
    provider_id: int = Field(default=None, primary_key=True)
    provider_name: Optional[str] = Field(max_length=255)
    npi: Optional[str] = Field(max_length=20)
    dea: Optional[str] = Field(max_length=20)
    specialty_concept_id: Optional[int]
    care_site_id: Optional[int]
    year_of_birth: Optional[int]
    gender_concept_id: Optional[int]
    provider_source_value: Optional[str] = Field(max_length=50)
    specialty_source_value: Optional[str] = Field(max_length=50)
    specialty_source_concept_id: Optional[int]
    gender_source_value: Optional[str] = Field(max_length=50)
    gender_source_concept_id: Optional[int]


# # HINT DISTRIBUTE ON KEY (person_id)
# class PAYER_PLAN_PERIOD(SQLModel, table=True):
#     payer_plan_period_id: int
#     person_id: int
#     payer_plan_period_start_date: date
#     payer_plan_period_end_date: date
#     payer_concept_id: Optional[int]
#     payer_source_value: Optional[str] = Field(max_length=50)
#     payer_source_concept_id: Optional[int]
#     plan_concept_id: Optional[int]
#     plan_source_value: Optional[str] = Field(max_length=50)
#     plan_source_concept_id: Optional[int]
#     sponsor_concept_id: Optional[int]
#     sponsor_source_value: Optional[str] = Field(max_length=50)
#     sponsor_source_concept_id: Optional[int]
#     family_source_value: Optional[str] = Field(max_length=50)
#     stop_reason_concept_id: Optional[int]
#     stop_reason_source_value: Optional[str] = Field(max_length=50)
#     stop_reason_source_concept_id: Optional[int]

# HINT DISTRIBUTE ON RANDOM
# class COST(SQLModel, table=True):
#     cost_id: int
#     cost_event_id: int
#     cost_domain_id: str = Field(max_length=20)
#     cost_type_concept_id: int
#     currency_concept_id: Optional[int]
#     total_charge: Optional[float]
#     total_cost: Optional[float]
#     total_paid: Optional[float]
#     paid_by_payer: Optional[float]
#     paid_by_patient: Optional[float]
#     paid_patient_copay: Optional[float]
#     paid_patient_coinsurance: Optional[float]
#     paid_patient_deductible: Optional[float]
#     paid_by_primary: Optional[float]
#     paid_ingredient_cost: Optional[float]
#     paid_dispensing_fee: Optional[float]
#     payer_plan_period_id: Optional[int]
#     amount_allowed: Optional[float]
#     revenue_code_concept_id: Optional[int]
#     revenue_code_source_value: Optional[str] = Field(max_length=50)
#     drg_concept_id: Optional[int]
#     drg_source_value: Optional[str] = Field(max_length=3)

# HINT DISTRIBUTE ON KEY (person_id)
# class DRUG_ERA(SQLModel, table=True):
#     drug_era_id: int
#     person_id: int
#     drug_concept_id: int
#     drug_era_start_date: datetime
#     drug_era_end_date: datetime
#     drug_exposure_count: Optional[int]
#     gap_days: Optional[int]

# HINT DISTRIBUTE ON KEY (person_id)
# class DOSE_ERA(SQLModel, table=True):
#     dose_era_id: int
#     person_id: int
#     drug_concept_id: int
#     unit_concept_id: int
#     dose_value: float
#     dose_era_start_date: datetime
#     dose_era_end_date: datetime

# HINT DISTRIBUTE ON KEY (person_id)
# class CONDITION_ERA(SQLModel, table=True):
#     condition_era_id: int
#     person_id: int
#     condition_concept_id: int
#     condition_era_start_date: datetime
#     condition_era_end_date: datetime
#     condition_occurrence_count: Optional[int]

# HINT DISTRIBUTE ON KEY (person_id)
# class EPISODE(SQLModel, table=True):
#     episode_id: int
#     person_id: int
#     episode_concept_id: int
#     episode_start_date: date
#     episode_start_datetime: Optional[datetime]
#     episode_end_date: Optional[date]
#     episode_end_datetime: Optional[datetime]
#     episode_parent_id: Optional[int]
#     episode_number: Optional[int]
#     episode_object_concept_id: int
#     episode_type_concept_id: int
#     episode_source_value: Optional[str] = Field(max_length=50)
#     episode_source_concept_id: Optional[int]

# # HINT DISTRIBUTE ON RANDOM
# class EPISODE_EVENT(SQLModel, table=True):
#     episode_id: int
#     event_id: int
#     episode_event_field_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class METADATA(SQLModel, table=True):
#     metadata_id: int
#     metadata_concept_id: int
#     metadata_type_concept_id: int
#     name: str = Field(max_length=250)
#     value_as_string: Optional[str] = Field(max_length=250)
#     value_as_concept_id: Optional[int
#     value_as_number: Optional[float
#     metadata_date: Optional[date
#     metadata_datetime: Optional[datetime
# # HINT DISTRIBUTE ON RANDO
# class CDM_SOURCE(SQLModel, table=True)
#     cdm_source_name: str = Field(max_length=255)
#     cdm_source_abbreviation: str = Field(max_length=25)
#     cdm_holder: str = Field(max_length=255)
#     source_description: Optional[str]
#     source_documentation_reference: Optional[str] = Field(max_length=255)
#     cdm_etl_reference: Optional[str] = Field(max_length=255)
#     source_release_date: date
#     cdm_release_date: date
#     cdm_version: Optional[str] = Field(max_length=10)
#     cdm_version_concept_id: int
#     vocabulary_version: str = Field(max_length=20)


# HINT DISTRIBUTE ON RANDOM
class CONCEPT(SQLModel, table=True):
    concept_id: int = Field(default=None, primary_key=True)
    concept_name: str = Field(max_length=255)
    domain_id: str = Field(max_length=20)
    vocabulary_id: str = Field(max_length=20)
    concept_class_id: str = Field(max_length=20)
    standard_concept: Optional[str] = Field(max_length=1)
    concept_code: str = Field(max_length=50)
    valid_start_date: date
    valid_end_date: date
    invalid_reason: Optional[str] = Field(max_length=1)


# # HINT DISTRIBUTE ON RANDOM
# class VOCABULARY(SQLModel, table=True):
#     vocabulary_id: str = Field(max_length=20)  = Field(default=None, primary_key=True)
#     vocabulary_name: str = Field(max_length=255)
#     vocabulary_reference: Optional[str] = Field(max_length=255)
#     vocabulary_version: Optional[str] = Field(max_length=255)
#     vocabulary_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class DOMAIN(SQLModel, table=True):
#     domain_id: str = Field(max_length=20)  = Field(default=None, primary_key=True)
#     domain_name: str = Field(max_length=255)
#     domain_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class CONCEPT_CLASS(SQLModel, table=True):
#     concept_class_id: str = Field(max_length=20)  = Field(default=None, primary_key=True)
#     concept_class_name: str = Field(max_length=255)
#     concept_class_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class CONCEPT_RELATIONSHIP(SQLModel, table=True):
#     concept_id_1: int
#     concept_id_2: int
#     relationship_id: str = Field(max_length=20)
#     valid_start_date: date
#     valid_end_date: date
#     invalid_reason: Optional[str] = Field(max_length=1)

# # HINT DISTRIBUTE ON RANDOM
# class RELATIONSHIP(SQLModel, table=True):
#     relationship_id: str = Field(max_length=20)
#     relationship_name: str = Field(max_length=255)
#     is_hierarchical: str = Field(max_length=1)
#     defines_ancestry: str = Field(max_length=1)
#     reverse_relationship_id: str = Field(max_length=20)
#     relationship_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class CONCEPT_SYNONYM(SQLModel, table=True):
#     concept_id: int
#     concept_synonym_name: str = Field(max_length=1000)
#     language_concept_id: int

# # HINT DISTRIBUTE ON RANDOM
# class CONCEPT_ANCESTOR(SQLModel, table=True):
#     ancestor_concept_id: int
#     descendant_concept_id: int
#     min_levels_of_separation: int
#     max_levels_of_separation: int

# # HINT DISTRIBUTE ON RANDOM
# class SOURCE_TO_CONCEPT_MAP(SQLModel, table=True):
#     source_code: str = Field(max_length=50)
#     source_concept_id: int
#     source_vocabulary_id: str = Field(max_length=20)
#     source_code_description: Optional[str] = Field(max_length=255)
#     target_concept_id: int
#     target_vocabulary_id: str = Field(max_length=20)
#     valid_start_date: date
#     valid_end_date: date
#     invalid_reason: Optional[str] = Field(max_length=1)

# # HINT DISTRIBUTE ON RANDOM
# class DRUG_STRENGTH(SQLModel, table=True):
#     drug_concept_id: int
#     ingredient_concept_id: int
#     amount_value: Optional[float]
#     amount_unit_concept_id: Optional[int]
#     numerator_value: Optional[float]
#     numerator_unit_concept_id: Optional[int]
#     denominator_value: Optional[float]
#     denominator_unit_concept_id: Optional[int]
#     box_size: Optional[int]
#     valid_start_date: date
#     valid_end_date: date
#     invalid_reason: Optional[str] = Field(max_length=1)


class ORDER(SQLModel, table=True):
    __table_args__ = {"schema": "alan"}
    __tablename__ = "restrack_orders"
    order_id: int = Field(default=None, primary_key=True)
    visit_id: int
    event_id: int
    patient_id: Optional[int]
    proc_id: int
    proc_name: Optional[str] = Field(max_length=175)
    order_entered_by: Optional[int]
    order_requested_by: Optional[int]
    event_event_id: Optional[int]
    current_status: Optional[int]
    order_datetime: Optional[datetime]
    event_datetime: Optional[datetime]
    cancelled: Optional[datetime]
    in_progress: Optional[datetime]
    partial: Optional[datetime]
    complete: Optional[datetime]
    supplemental: Optional[datetime]
    last_edit_time: Optional[datetime]
    updated_at: Optional[datetime]


class Order(BaseModel):
    order_id: int
    visit_id: int
    event_id: int
    patient_id: Optional[int]
    proc_id: int
    proc_name: Optional[str]
    order_entered_by: Optional[int]
    order_requested_by: Optional[int]
    event_event_id: Optional[int]
    current_status: Optional[int]
    order_datetime: Optional[datetime]
    event_datetime: Optional[datetime]
    cancelled: Optional[datetime]
    in_progress: Optional[datetime]
    partial: Optional[datetime]
    complete: Optional[datetime]
    supplemental: Optional[datetime]
    last_edit_time: Optional[datetime]
    updated_at: Optional[datetime]
