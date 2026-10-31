# %% [markdown]
# # SecureLife Health Insurance - EDA
# Focus: premiums, claim amounts, outliers.
# Run top to bottom as a script, or cell by cell in VS Code / Jupyter (the `# %%` markers).

# %% Setup
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

FILE = "SecureLife_Cleaned_Dataset.xlsx"   # change path if needed
OUT = Path("charts")
OUT.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"] = 110
inr = mtick.FuncFormatter(lambda x, _: f"₹{x:,.0f}")


def save(name):
    plt.tight_layout()
    plt.savefig(OUT / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.show()


# %% Load
policies = pd.read_excel(FILE, "Policies")
claims = pd.read_excel(FILE, "Claims")
members = pd.read_excel(FILE, "Members")
renewals = pd.read_excel(FILE, "Renewals")
hospitals = pd.read_excel(FILE, "Hospitals")

print(policies.shape, claims.shape, members.shape, renewals.shape, hospitals.shape)
print(policies.describe().T, "\n")
print(claims[["claim_amount", "approved_amount"]].describe().T)

# Helper: IQR outlier bounds
def iqr_bounds(s, k=1.5):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


# =====================================================================
# 1. PREMIUMS
# =====================================================================
# %% 1a. Premium distribution + by plan type
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.histplot(policies, x="annual_premium", hue="plan_type", bins=50,
             kde=True, element="step", ax=ax[0])
ax[0].set(title="Annual premium distribution", xlabel="Annual premium")
ax[0].xaxis.set_major_formatter(inr)

sns.boxplot(policies, x="plan_type", y="annual_premium", ax=ax[1])
ax[1].set(title="Premium by plan type", xlabel="", ylabel="Annual premium")
ax[1].yaxis.set_major_formatter(inr)
save("01_premium_distribution")

# %% 1b. Premium vs sum insured
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.boxplot(policies, x="sum_insured", y="annual_premium", hue="plan_type", ax=ax[0])
ax[0].set(title="Premium by sum insured", xlabel="Sum insured", ylabel="Annual premium")
ax[0].yaxis.set_major_formatter(inr)
ax[0].set_xticks(range(policies.sum_insured.nunique()))
ax[0].set_xticklabels([f"{v/1e5:g}L" for v in sorted(policies.sum_insured.unique())])

sns.scatterplot(policies.sample(3000, random_state=1), x="sum_insured",
                y="annual_premium", hue="plan_type", alpha=0.4, ax=ax[1])
ax[1].set(title="Premium vs sum insured (3,000 sampled)")
ax[1].yaxis.set_major_formatter(inr)
save("02_premium_vs_sum_insured")

# %% 1c. Premium by city + trend by policy start year
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
order = policies.groupby("city").annual_premium.median().sort_values().index
sns.boxplot(policies, y="city", x="annual_premium", order=order, ax=ax[0])
ax[0].set(title="Premium by city (sorted by median)", ylabel="")
ax[0].xaxis.set_major_formatter(inr)

policies["start_year"] = policies.start_date.dt.year
trend = policies.groupby(["start_year", "plan_type"]).annual_premium.mean().reset_index()
sns.lineplot(trend, x="start_year", y="annual_premium", hue="plan_type", marker="o", ax=ax[1])
ax[1].set(title="Mean premium by policy start year", xlabel="Start year")
ax[1].yaxis.set_major_formatter(inr)
ax[1].set_xticks(sorted(policies.start_year.unique()))
save("03_premium_city_trend")

# %% 1d. Renewal premium change
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.histplot(renewals, x="premium_change_percent", bins=40, kde=True, ax=ax[0])
ax[0].set(title="Premium change at renewal (%)")
sns.boxplot(renewals, x="renewed", y="premium_change_percent",
            order=["Yes", "No", "Pending"], ax=ax[1])
ax[1].set(title="Premium change % by renewal outcome", xlabel="Renewed")
save("04_renewal_premium_change")

# =====================================================================
# 2. CLAIM AMOUNTS
# =====================================================================
# %% 2a. Claim amount distribution (raw vs log)
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.histplot(claims.claim_amount, bins=60, ax=ax[0])
ax[0].set(title="Claim amount (raw) - heavy right skew", xlabel="Claim amount")
ax[0].xaxis.set_major_formatter(inr)

sns.histplot(np.log10(claims.claim_amount), bins=60, kde=True, ax=ax[1])
ax[1].set(title="Claim amount (log10 scale)", xlabel="log10(claim amount)")
save("05_claim_amount_distribution")

print("Skew:", claims.claim_amount.skew().round(2),
      "| mean:", int(claims.claim_amount.mean()),
      "| median:", int(claims.claim_amount.median()))

# %% 2b. Claims by treatment category
fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
order = claims.groupby("treatment_category").claim_amount.median().sort_values().index
sns.boxplot(claims, y="treatment_category", x="claim_amount", order=order,
            showfliers=False, ax=ax[0])
ax[0].set(title="Claim amount by treatment (outliers hidden)", ylabel="")
ax[0].xaxis.set_major_formatter(inr)

cat = (claims.groupby("treatment_category")
       .agg(claims=("claim_id", "count"), total=("claim_amount", "sum"))
       .sort_values("total"))
ax[1].barh(cat.index, cat.total / 1e6, color=sns.color_palette()[0])
ax[1].set(title="Total claimed by treatment (₹ millions)")
save("06_claims_by_treatment")

# %% 2c. Claim vs approved, and status
claims["approval_ratio"] = claims.approved_amount / claims.claim_amount

fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
sns.countplot(claims, y="claim_status",
              order=claims.claim_status.value_counts().index, ax=ax[0])
ax[0].set(title="Claim status", ylabel="")

sns.scatterplot(claims.sample(4000, random_state=1), x="claim_amount",
                y="approved_amount", hue="claim_status", alpha=0.5, ax=ax[1])
ax[1].set(title="Claimed vs approved (4,000 sampled)")
ax[1].xaxis.set_major_formatter(inr)
ax[1].yaxis.set_major_formatter(inr)

sns.boxplot(claims, x="claim_status", y="claim_amount", showfliers=False, ax=ax[2],
            order=["Approved", "Partially Approved", "Pending", "Rejected"])
ax[2].set(title="Claim amount by status", xlabel="")
ax[2].yaxis.set_major_formatter(inr)
ax[2].tick_params(axis="x", rotation=20)
save("07_claim_vs_approved_status")

# %% 2d. Monthly claim volume & value
monthly = (claims.set_index("claim_date")
           .resample("MS")
           .agg(count=("claim_id", "count"), total=("claim_amount", "sum")))
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.plot(monthly.index, monthly["count"], marker="o", ms=3, label="Claim count")
ax.set(title="Monthly claims", ylabel="Count")
ax2 = ax.twinx()
ax2.plot(monthly.index, monthly.total / 1e6, color="C1", label="Total claimed (₹M)")
ax2.set_ylabel("₹ millions")
ax2.grid(False)
fig.legend(loc="upper left", bbox_to_anchor=(0.07, 0.88))
save("08_monthly_claims")

# =====================================================================
# 3. OUTLIERS
# =====================================================================
# %% 3a. Compare the dataset's outlier flags with a fresh IQR check
rows = []
for col, flag in [("claim_amount", "claim_amount_outlier"),
                  ("approved_amount", "approved_amount_outlier")]:
    lo, hi = iqr_bounds(claims[col])
    iqr_flag = (claims[col] < lo) | (claims[col] > hi)
    rows.append({"column": col,
                 "IQR upper bound": int(hi),
                 "IQR outliers": int(iqr_flag.sum()),
                 "flagged in dataset": int(claims[flag].sum()),
                 "flag == IQR": bool((iqr_flag == claims[flag]).all()),
                 "min flagged value": int(claims.loc[claims[flag], col].min())})
print(pd.DataFrame(rows).to_string(index=False))

lo, hi = iqr_bounds(policies.annual_premium)
policies["premium_outlier"] = (policies.annual_premium < lo) | (policies.annual_premium > hi)
print(f"\nPremium IQR bounds: {lo:,.0f} - {hi:,.0f}  "
      f"-> {policies.premium_outlier.sum()} outlier policies")

# %% 3b. Outlier boxplots (premium, claim, approved)
fig, ax = plt.subplots(1, 3, figsize=(16, 5))
for a, (df, col, title) in zip(ax, [
    (policies, "annual_premium", "Annual premium"),
    (claims, "claim_amount", "Claim amount"),
    (claims, "approved_amount", "Approved amount")]):
    sns.boxplot(df, y=col, ax=a, flierprops=dict(marker="o", ms=3, alpha=0.4))
    a.set(title=title, ylabel="")
    a.yaxis.set_major_formatter(inr)
save("09_outlier_boxplots")

# %% 3c. Claim amount outliers highlighted
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8))
sns.histplot(claims, x="claim_amount", hue="claim_amount_outlier", bins=70,
             multiple="stack", ax=ax[0])
ax[0].set(title="Claim amount: normal vs flagged outliers", xlabel="Claim amount")
ax[0].xaxis.set_major_formatter(inr)

sample = claims.sample(4000, random_state=2)
sns.scatterplot(sample, x=sample.index, y="claim_amount", hue="claim_amount_outlier",
                alpha=0.6, s=14, ax=ax[1])
ax[1].set(title="Claim amount by record (4,000 sampled)", xlabel="Row index")
ax[1].yaxis.set_major_formatter(inr)
save("10_claim_outliers_highlighted")

# %% 3d. Where do outliers come from?
share_cat = (claims.groupby("treatment_category").claim_amount_outlier.mean()
             .sort_values() * 100)
share_status = (claims.groupby("claim_status").claim_amount_outlier.mean()
                .sort_values() * 100)

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
share_cat.plot.barh(ax=ax[0])
ax[0].set(title="% of claims that are outliers, by treatment", xlabel="%", ylabel="")
share_status.plot.barh(ax=ax[1], color="C1")
ax[1].set(title="% of claims that are outliers, by status", xlabel="%", ylabel="")
save("11_outlier_share")

# %% 3e. Outlier impact + top claims
tot = claims.claim_amount.sum()
out_tot = claims.loc[claims.claim_amount_outlier, "claim_amount"].sum()
print(f"Outliers: {claims.claim_amount_outlier.mean():.1%} of claims "
      f"but {out_tot / tot:.1%} of total claimed value")

# Mean with vs without outliers
clean = claims[~claims.claim_amount_outlier]
print(f"Mean claim: {claims.claim_amount.mean():,.0f} (all) vs "
      f"{clean.claim_amount.mean():,.0f} (without outliers); "
      f"median {claims.claim_amount.median():,.0f}")

# Do the biggest claims exceed the policy's sum insured?
merged = claims.merge(policies[["policy_id", "sum_insured", "annual_premium", "plan_type"]],
                      on="policy_id")
merged["over_sum_insured"] = merged.claim_amount > merged.sum_insured
print("Claims above sum insured:", int(merged.over_sum_insured.sum()))
print("Approved above sum insured:", int((merged.approved_amount > merged.sum_insured).sum()))
print("\nTop 10 claims:")
print(merged.nlargest(10, "claim_amount")[
    ["claim_id", "policy_id", "treatment_category", "claim_amount",
     "approved_amount", "claim_status", "sum_insured"]].to_string(index=False))

# %% 3f. Claim amount vs the policy's premium (high-claim policies)
pol_claims = (merged.groupby("policy_id")
              .agg(total_claimed=("claim_amount", "sum"),
                   premium=("annual_premium", "first"),
                   plan=("plan_type", "first")).reset_index())
pol_claims["claim_to_premium"] = pol_claims.total_claimed / pol_claims.premium

fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(pol_claims, x="premium", y="total_claimed", hue="plan", alpha=0.5, ax=ax)
ax.set(yscale="log", title="Total claimed vs annual premium per policy (log y)")
ax.xaxis.set_major_formatter(inr)
save("12_claims_vs_premium_by_policy")

print("\nPolicies with claims:", len(pol_claims))
print("Claim-to-premium ratio quantiles:\n",
      pol_claims.claim_to_premium.quantile([.5, .9, .99]).round(1))