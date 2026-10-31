# %% [markdown]
# # SecureLife - Renewed vs Non-renewed customers
# Compares policies that renewed ("Yes") with those that did not ("No") on
# premium change, claims experience and city.
# "Pending" renewals are due on/after 1 Nov 2026, so they are excluded from comparisons.

# %% Setup
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

FILE = "SecureLife_Cleaned_Dataset.xlsx"
OUT = Path("charts")
OUT.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"] = 110
PAL = {"Yes": "#2a9d8f", "No": "#e76f51"}
inr = mtick.FuncFormatter(lambda x, _: f"₹{x:,.0f}")


def save(name):
    plt.tight_layout()
    plt.savefig(OUT / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.show()


# %% Build one row per policy
policies = pd.read_excel(FILE, "Policies")
claims = pd.read_excel(FILE, "Claims")
renewals = pd.read_excel(FILE, "Renewals")

per_policy = claims.groupby("policy_id").agg(
    n_claims=("claim_id", "count"),
    total_claimed=("claim_amount", "sum"),
    total_approved=("approved_amount", "sum"),
    n_rejected=("claim_status", lambda s: (s == "Rejected").sum()),
)

df = (policies.merge(renewals, on="policy_id")
      .merge(per_policy, on="policy_id", how="left"))
for c in ["n_claims", "total_claimed", "total_approved", "n_rejected"]:
    df[c] = df[c].fillna(0)

df["has_claim"] = df.n_claims > 0
df["rejection_rate"] = (df.n_rejected / df.n_claims).where(df.has_claim)
df["approval_ratio"] = (df.total_approved / df.total_claimed).where(df.has_claim)

print(df.renewed.value_counts(), "\n")
cmp = df[df.renewed.isin(["Yes", "No"])].copy()      # renewed vs non-renewed only
cmp["renewed_flag"] = (cmp.renewed == "Yes").astype(int)
base_rate = cmp.renewed_flag.mean()
print(f"Overall renewal rate (excl. pending): {base_rate:.1%}")


def mwu(col):
    a = cmp.loc[cmp.renewed == "Yes", col].dropna()
    b = cmp.loc[cmp.renewed == "No", col].dropna()
    return stats.mannwhitneyu(a, b).pvalue


# =====================================================================
# 1. PREMIUM CHANGE
# =====================================================================
# %% 1a. Premium change distribution by outcome
fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
sns.kdeplot(cmp, x="premium_change_percent", hue="renewed", palette=PAL,
            fill=True, common_norm=False, alpha=0.35, ax=ax[0])
ax[0].set(title="Premium change at renewal (%)", xlabel="Premium change %")
sns.boxplot(cmp, x="renewed", y="premium_change_percent", order=["Yes", "No"],
            palette=PAL, hue="renewed", legend=False, ax=ax[1])
ax[1].set(title="Premium change % by renewal outcome", xlabel="Renewed")
save("13_renewal_premium_change_by_outcome")

print(cmp.groupby("renewed").premium_change_percent.describe().round(2))
print("Mann-Whitney p (premium change):", f"{mwu('premium_change_percent'):.2e}")

# %% 1b. Renewal rate by premium-change band
bins = [-6, 0, 5, 10, 15, 26]
labels = ["≤0%", "0-5%", "5-10%", "10-15%", ">15%"]
cmp["pc_band"] = pd.cut(cmp.premium_change_percent, bins, labels=labels)

band = (cmp.groupby("pc_band", observed=True).renewed_flag
        .agg(rate="mean", n="size").reset_index())
band["se"] = np.sqrt(band.rate * (1 - band.rate) / band.n)

fig, ax = plt.subplots(figsize=(8.5, 5))
ax.bar(band.pc_band.astype(str), band.rate * 100, yerr=band.se * 196,
       color="#264653", capsize=4)
ax.axhline(base_rate * 100, ls="--", color="grey", label=f"Overall {base_rate:.1%}")
for i, r in band.iterrows():
    ax.text(i, r.rate * 100 + 4.5, f"{r.rate:.0%}\n(n={r.n:,})", ha="center", fontsize=9)
ax.set(title="Renewal rate by size of premium increase", xlabel="Premium change at renewal",
       ylabel="% renewed", ylim=(0, 100))
ax.legend()
save("14_renewal_rate_by_premium_change_band")
print(band.round(3))

# =====================================================================
# 2. CLAIMS
# =====================================================================
# %% 2a. Claims experience comparison
fig, ax = plt.subplots(2, 2, figsize=(13, 9))

share = cmp.groupby("renewed").has_claim.mean().reindex(["Yes", "No"]) * 100
ax[0, 0].bar(share.index, share.values, color=[PAL[k] for k in share.index])
for i, v in enumerate(share.values):
    ax[0, 0].text(i, v + 1, f"{v:.1f}%", ha="center")
ax[0, 0].set(title="% of policies with at least one claim", ylabel="%", ylim=(0, 80))

cmp["claims_bucket"] = cmp.n_claims.clip(upper=4).astype(int).astype(str).replace("4", "4+")
cnt = (pd.crosstab(cmp.renewed, cmp.claims_bucket, normalize="index")
       .stack().rename("share").reset_index().rename(columns={"claims_bucket": "n_claims"}))
sns.barplot(cnt, x="n_claims", y="share", hue="renewed", hue_order=["Yes", "No"],
            palette=PAL, ax=ax[0, 1])
ax[0, 1].set(title="Number of claims per policy", xlabel="Claims", ylabel="Share of policies")
ax[0, 1].yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

with_claims = cmp[cmp.has_claim]
sns.boxplot(with_claims, x="renewed", y="total_claimed", order=["Yes", "No"],
            palette=PAL, hue="renewed", legend=False, showfliers=False, ax=ax[1, 0])
ax[1, 0].set(title="Total claimed per policy (policies with claims; outliers hidden)",
             xlabel="Renewed", ylabel="Total claimed")
ax[1, 0].yaxis.set_major_formatter(inr)

sns.boxplot(with_claims, x="renewed", y="approval_ratio", order=["Yes", "No"],
            palette=PAL, hue="renewed", legend=False, ax=ax[1, 1])
ax[1, 1].set(title="Approved ÷ claimed (policies with claims)",
             xlabel="Renewed", ylabel="Approval ratio")
save("15_claims_by_renewal_outcome")

# %% 2b. Summary table + tests
summary = cmp.groupby("renewed").agg(
    policies=("policy_id", "count"),
    pct_with_claim=("has_claim", "mean"),
    avg_claims=("n_claims", "mean"),
    avg_total_claimed=("total_claimed", "mean"),
    median_total_claimed_if_any=("total_claimed", lambda s: s[s > 0].median()),
    avg_rejection_rate=("rejection_rate", "mean"),
    avg_approval_ratio=("approval_ratio", "mean"),
    avg_premium=("annual_premium", "mean"),
    avg_premium_change=("premium_change_percent", "mean"),
).T.round(3)
print(summary, "\n")

chi_claim = stats.chi2_contingency(pd.crosstab(cmp.has_claim, cmp.renewed))[1]
print(f"p-values  has_claim (chi2): {chi_claim:.3f}")
for col in ["n_claims", "total_claimed", "rejection_rate", "approval_ratio", "annual_premium"]:
    print(f"          {col} (Mann-Whitney): {mwu(col):.3f}")

# %% 2c. Does a bad claims experience (rejections) change renewal?
exp = with_claims.copy()
exp["rejection_group"] = pd.cut(exp.rejection_rate, [-0.01, 0, 0.5, 1.0],
                                labels=["No rejections", "Some rejected", "Mostly rejected"])
rj = exp.groupby("rejection_group", observed=True).renewed_flag.agg(["mean", "size"])
fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.bar(rj.index.astype(str), rj["mean"] * 100, color="#264653")
ax.axhline(base_rate * 100, ls="--", color="grey", label="Overall")
for i, (m, n) in enumerate(zip(rj["mean"], rj["size"])):
    ax.text(i, m * 100 + 1.5, f"{m:.0%} (n={n:,})", ha="center")
ax.set(title="Renewal rate by claim-rejection experience", ylabel="% renewed", ylim=(0, 90))
ax.legend()
save("16_renewal_by_rejection_experience")

# =====================================================================
# 3. CITY
# =====================================================================
# %% 3a. Renewal rate by city (with 95% CI)
city = (cmp.groupby("city").renewed_flag.agg(rate="mean", n="size").reset_index()
        .sort_values("rate"))
city["ci"] = 1.96 * np.sqrt(city.rate * (1 - city.rate) / city.n)

fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
ax[0].barh(city.city, city.rate * 100, xerr=city.ci * 100, color="#264653", capsize=3)
ax[0].axvline(base_rate * 100, ls="--", color="grey", label=f"Overall {base_rate:.1%}")
ax[0].set(title="Renewal rate by city (95% CI)", xlabel="% renewed", xlim=(50, 80))
ax[0].legend(loc="lower right")

cm = cmp.groupby("city").agg(
    avg_premium_change=("premium_change_percent", "mean"),
    avg_premium=("annual_premium", "mean"),
    pct_with_claim=("has_claim", "mean"),
    avg_claimed=("total_claimed", "mean"),
    renewal_rate=("renewed_flag", "mean"),
)
z = (cm - cm.mean()) / cm.std()
sns.heatmap(z.loc[city.city[::-1]], annot=cm.loc[city.city[::-1]].round(2).values,
            fmt="", cmap="RdBu_r", center=0, cbar_kws={"label": "z-score across cities"},
            ax=ax[1])
ax[1].set(title="City profile (values shown, colour = relative to other cities)", ylabel="")
ax[1].tick_params(axis="x", rotation=30)
save("17_city_renewal")

chi_city = stats.chi2_contingency(pd.crosstab(cmp.city, cmp.renewed))[1]
print(f"City vs renewal chi2 p-value: {chi_city:.3f}")
print(city.sort_values("rate", ascending=False)[["city", "rate", "n"]].round(3).to_string(index=False))

# %% 3b. Is the city effect just a premium-change effect?
fig, ax = plt.subplots(figsize=(9, 4.8))
order = cm.sort_values("avg_premium_change").index
sns.boxplot(cmp, y="city", x="premium_change_percent", hue="renewed", hue_order=["Yes", "No"],
            palette=PAL, order=order, showfliers=False, ax=ax)
ax.set(title="Premium change % by city and renewal outcome", ylabel="", xlabel="Premium change %")
save("18_city_premium_change_by_outcome")

# =====================================================================
# 4. All drivers together
# =====================================================================
# %% 4. Logistic regression: which factors matter once controlled for each other?
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

X = pd.get_dummies(
    cmp[["premium_change_percent", "annual_premium", "n_claims", "total_claimed",
         "has_claim", "plan_type", "city"]],
    columns=["plan_type", "city"], drop_first=True).astype(float)
Xs = pd.DataFrame(StandardScaler().fit_transform(X), columns=X.columns)
model = LogisticRegression(max_iter=1000).fit(Xs, cmp.renewed_flag)
coefs = pd.Series(model.coef_[0], index=X.columns).sort_values()

fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(coefs.index, coefs.values, color=np.where(coefs < 0, "#e76f51", "#2a9d8f"))
ax.axvline(0, color="black", lw=0.8)
ax.set(title="Logistic regression: effect on renewal (standardised coefficients)",
       xlabel="← less likely to renew        more likely to renew →")
save("19_renewal_drivers_logit")
print(coefs.round(3).to_string())