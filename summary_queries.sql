

CREATE DATABASE SecureLife;

CREATE TABLE Policies (
    policy_id VARCHAR(20) PRIMARY KEY,
    start_date DATE,
    plan_type VARCHAR(30),
    sum_insured DECIMAL(15,2),
    annual_premium DECIMAL(12,2),
    city VARCHAR(50)
);
CREATE TABLE Claims (
    claim_id VARCHAR(20) PRIMARY KEY,
    policy_id VARCHAR(20),
    member_id VARCHAR(20),
    claim_date DATE,
    hospital_id VARCHAR(20),
    treatment_category VARCHAR(50),
    claim_amount DECIMAL(15,2),
    approved_amount DECIMAL(15,2),
    claim_status VARCHAR(40),
    claim_amount_outlier BOOLEAN,
    approved_amount_outlier BOOLEAN
);

USE SecureLife;

SELECT COUNT(*) AS Total_Policies
FROM Policies_cleaned;

SELECT COUNT(*) AS Total_Claims
FROM Claims_cleaned; 


SELECT
    COUNT(*) AS Matching_Records
FROM Policies_cleaned p
INNER JOIN Claims_cleaned c
    ON TRIM(p.policy_id) = TRIM(c.policy_id);

SELECT
    p.plan_type,
    p.city,
    SUM(c.claim_amount) AS Total_Claims
FROM Policies_cleaned p
JOIN Claims_cleaned c
    ON p.policy_id = c.policy_id
GROUP BY p.plan_type, p.city
ORDER BY Total_Claims ; 
select *FROM Claims_cleaned; 
select *from policies_cleaned; 

SELECT
    policy_id,
    plan_type,
    city,
    annual_premium,
    ROUND(annual_premium / 12, 2) AS Monthly_Premium
FROM Policies_cleaned; 


SELECT
    plan_type,
    city,
    COUNT(*) AS Total_Policies,
    SUM(annual_premium) AS Total_Annual_Premium,
    ROUND(SUM(annual_premium) / 12, 2) AS Total_Monthly_Premium
FROM Policies_cleaned
GROUP BY plan_type, city
ORDER BY Total_Monthly_Premium; 

SELECT
    p.plan_type,
    p.city,
    ROUND(SUM(p.annual_premium) / 12, 2) AS Monthly_Premium,
    COUNT(c.claim_id) AS Number_of_Claims
FROM Policies_cleaned p
INNER JOIN Claims_cleaned c
    ON TRIM(p.policy_id) = TRIM(c.policy_id)
GROUP BY p.plan_type, p.city
ORDER BY Monthly_Premium DESC;