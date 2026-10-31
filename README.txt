SECURELIFE HEALTH INSURANCE - SYNTHETIC HACKATHON DATASET
==========================================================

All records in this package are synthetic and generated for educational/hackathon use.
They do not describe real people, hospitals, insurers, claims, or financial outcomes.
The simulated renewal patterns and claim distributions are illustrative, not actuarial estimates.

TABLES
------
policies.csv
  policy_id (PK), start_date, plan_type, sum_insured, annual_premium, city

members.csv
  member_id (PK), policy_id (FK), age_group, gender, pre_existing_condition
  policy_id is included to link each member to their policy.

claims.csv
  claim_id (PK), policy_id (FK), member_id (FK), claim_date, hospital_id (FK),
  treatment_category, claim_amount, approved_amount, claim_status
  policy_id and member_id are included to connect claims to policies and members.

hospitals.csv
  hospital_id (PK), city, tier, network

renewals.csv
  policy_id (PK/FK), renewal_due_date, renewed, premium_change_percent
  One latest renewal decision per policy. "Pending" means the due date is after
  the simulated data cutoff (2026-10-31).

RELATIONSHIPS
-------------
policies.policy_id 1 -> many members.policy_id
policies.policy_id 1 -> many claims.policy_id
members.member_id 1 -> many claims.member_id
hospitals.hospital_id 1 -> many claims.hospital_id
policies.policy_id 1 -> 1 renewals.policy_id

RECORD COUNTS
-------------
policies.csv: 10,000 rows, 6 columns
members.csv: 17,833 rows, 5 columns
claims.csv: 12,000 rows, 9 columns
hospitals.csv: 100 rows, 4 columns
renewals.csv: 10,000 rows, 4 columns

SUGGESTED ANALYSIS
------------------
- Claim ratio by plan, age group, city, and policy segment.
- Hospital average claim amount by treatment category (compare like-for-like treatments).
- Claim rejection rate and approved vs. requested amounts.
- Renewal rate by plan, city, and premium-change band.
- High-cost claim outlier detection.
- Premium and claim summaries by month.

IMPORTANT METRIC NOTES
----------------------
- For claim ratio, define numerator consistently (e.g. approved_amount for paid/approved
  claims) and denominator as earned/annual premium for the matching exposure period.
  This sample has annual_premium, not earned premium, so label simple comparisons clearly.
- Pending claims have approved_amount = 0 in this dataset; do not interpret that as a final
  rejection or settled claim.
- A hospital's high average should be compared within the same treatment category and
  ideally adjusted for severity; this sample does not include clinical severity.
- Fraud is not labelled. Use anomaly detection to flag unusual patterns for investigation;
  do not call every outlier fraud.
- The dataset does not contain claim rejection reasons, claim settlement dates, customer
  complaints, satisfaction scores, or competitor offers. Those analyses need extra fields.

Suggested cutoff date: 2026-10-31.
