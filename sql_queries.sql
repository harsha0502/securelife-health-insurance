CREATE DATABASE insurance;
USE insurance;

SHOW DATABASES;
show tables;

desc policies;

SELECT 'Policies' AS table_name, COUNT(*) AS total_rows FROM policies
UNION ALL
SELECT 'Members', COUNT(*) FROM members
UNION ALL
SELECT 'Claims', COUNT(*) FROM claims
UNION ALL
SELECT 'Hospitals', COUNT(*) FROM hospitals
UNION ALL
SELECT 'Renewals', COUNT(*) FROM renewals;

select * from policies;

-- Problem 1

WITH member_counts AS (
    SELECT
        policy_id,
        COUNT(*) AS total_members
    FROM members
    GROUP BY policy_id
),
member_premiums AS (
    SELECT
        p.policy_id,
        m.member_id,
        p.plan_type,
        m.age_group,
        p.annual_premium / mc.total_members AS allocated_premium
    FROM policies p
    JOIN members m
        ON p.policy_id = m.policy_id
    JOIN member_counts mc
        ON p.policy_id = mc.policy_id
),
member_claims AS (
    SELECT
        policy_id,
        member_id,
        SUM(approved_amount) AS total_approved_claims
    FROM claims
    GROUP BY policy_id, member_id
)
SELECT
    mp.plan_type,
    mp.age_group,
    ROUND(SUM(COALESCE(mcl.total_approved_claims, 0)), 2)
        AS total_approved_claims,
    ROUND(SUM(mp.allocated_premium), 2)
        AS allocated_premium,
    ROUND(
        SUM(COALESCE(mcl.total_approved_claims, 0))
        / NULLIF(SUM(mp.allocated_premium), 0) * 100,
        2
    ) AS claim_ratio_percent
FROM member_premiums mp
LEFT JOIN member_claims mcl
    ON mp.policy_id = mcl.policy_id
    AND mp.member_id = mcl.member_id
GROUP BY
    mp.plan_type,
    mp.age_group
ORDER BY
    claim_ratio_percent DESC;

-- problem 2

WITH hospital_averages AS (
    SELECT
        h.hospital_id,
        h.city,
        h.tier,
        c.treatment_category,
        COUNT(c.claim_id) AS total_claims,
        AVG(c.claim_amount) AS hospital_avg_claim
    FROM claims c
    JOIN hospitals h
        ON c.hospital_id = h.hospital_id
    GROUP BY
        h.hospital_id,
        h.city,
        h.tier,
        c.treatment_category
),
treatment_averages AS (
    SELECT
        treatment_category,
        AVG(claim_amount) AS treatment_avg_claim
    FROM claims
    GROUP BY treatment_category
)
SELECT
    ha.hospital_id,
    ha.city,
    ha.tier,
    ha.treatment_category,
    ha.total_claims,
    ROUND(ha.hospital_avg_claim, 2) AS hospital_avg_claim,
    ROUND(ta.treatment_avg_claim, 2) AS treatment_avg_claim,
    ROUND(
        (ha.hospital_avg_claim / ta.treatment_avg_claim - 1) * 100,
        2
    ) AS percentage_above_average
FROM hospital_averages ha
JOIN treatment_averages ta
    ON ha.treatment_category = ta.treatment_category
WHERE ha.hospital_avg_claim > ta.treatment_avg_claim * 1.5
  AND ha.total_claims >= 5
ORDER BY percentage_above_average DESC;

-- problem 3

SELECT
    p.plan_type,
    p.city,
    YEAR(r.renewal_due_date) AS policy_year,
    COUNT(*) AS total_eligible_policies,
    SUM(
        CASE
            WHEN r.renewed = 'Yes' THEN 1
            ELSE 0
        END
    ) AS renewed_policies,
    SUM(
        CASE
            WHEN r.renewed = 'No' THEN 1
            ELSE 0
        END
    ) AS not_renewed_policies,
    ROUND(
        SUM(CASE WHEN r.renewed = 'Yes' THEN 1 ELSE 0 END)
        /
        NULLIF(
            SUM(CASE WHEN r.renewed IN ('Yes', 'No') THEN 1 ELSE 0 END),
            0
        ) * 100,
        2
    ) AS renewal_rate_percent
FROM policies p
INNER JOIN renewals r
    ON p.policy_id = r.policy_id
WHERE r.renewed IN ('Yes', 'No')
GROUP BY
    p.plan_type,
    p.city,
    YEAR(r.renewal_due_date)
ORDER BY
    renewal_rate_percent DESC;

-- problem 4

SELECT
    treatment_category,
    COUNT(claim_id) AS total_claims,
    ROUND(SUM(claim_amount), 2)
        AS total_claim_amount,
    ROUND(AVG(claim_amount), 2)
        AS average_claim_amount,
    ROUND(
        SUM(claim_amount) * 100.0 /
        (SELECT SUM(claim_amount) FROM claims),
        2
    ) AS percentage_of_total_claims
FROM claims
GROUP BY treatment_category
ORDER BY total_claim_amount DESC
LIMIT 10;
