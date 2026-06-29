# A/B Test Significance Analyser

A lightweight Python tool for running and planning A/B tests. Covers two-proportion z-test significance testing, confidence intervals, and minimum sample size calculation.

Built as a working proof of understanding A/B testing mechanics — scoped to be functionally complete rather than architecturally impressive. The goal was to build until I could confidently set up, run, and interpret a real experiment.

---

## What it does

**Analyse a result (Tab 1)**
- Takes visitor and conversion counts for control and test variants
- Runs a two-proportion z-test
- Returns p-value, z-statistic, relative uplift, and 95% confidence interval on the difference
- Clear verdict: significant or not — with a note on whether the CI excludes zero

**Plan a test (Tab 2)**
- Takes a baseline conversion rate and minimum detectable effect (MDE)
- Calculates required sample size per variant
- Estimates runtime in days given your daily traffic
- Flags tests that are too short to be trusted (novelty effect risk)

---

## Run locally

```bash
git clone https://github.com/rafeeahmed1999-beep/A-B-test-significance-analyser.git
cd A-B-test-significance-analyser
pip install -r requirements.txt
streamlit run app.py
```

---

## Run the core stats without the UI

```bash
python analysis.py
```

This runs a sanity check against the Cookie Cats mobile game dataset (gate_30 vs gate_40, 7-day retention, ~90k users) — a well-documented public A/B test with published results to validate against.

---

## Stats reference

| Concept | What it means in practice |
|---|---|
| p-value | Probability of seeing this result if there were truly no difference. p < 0.05 = significant at 95% confidence. |
| Confidence interval | Range within which the true difference in conversion rates likely falls. If it excludes zero, there's a real effect. |
| Statistical power | Probability of detecting a real effect if one exists. Standard is 80% — below this, you risk missing genuine improvements. |
| MDE | The smallest uplift worth detecting. Setting this too small means you need enormous sample sizes for marginal gains. |

**Key rule:** Calculate your required sample size before the test starts and commit to it. Stopping early because it "looks significant" inflates false positive rates.

---

## Stack

Python · SciPy · statsmodels · Streamlit · Matplotlib
