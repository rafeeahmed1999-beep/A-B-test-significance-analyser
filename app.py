"""
app.py — Streamlit front-end for the A/B test significance analyser.
Run with: streamlit run app.py
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from analysis import run_ab_test, calculate_sample_size

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A/B Test Analyser",
    page_icon="🧪",
    layout="centered",
)

st.title("A/B Test Significance Analyser")
st.caption("Two-proportion z-test · 95% confidence by default · Two-tailed")

tab1, tab2 = st.tabs(["📊 Analyse a Result", "📐 Plan a Test"])


# ── Tab 1: Analyse a Result ───────────────────────────────────────────────────
with tab1:
    st.subheader("Enter your experiment results")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Control (existing)**")
        ctrl_visitors = st.number_input(
            "Visitors", min_value=1, value=10000, step=100, key="ctrl_v"
        )
        ctrl_conversions = st.number_input(
            "Conversions", min_value=0, value=300, step=10, key="ctrl_c"
        )
        if ctrl_visitors > 0:
            st.caption(f"Rate: {ctrl_conversions / ctrl_visitors:.2%}")

    with col2:
        st.markdown("**Test (variant)**")
        test_visitors = st.number_input(
            "Visitors", min_value=1, value=10000, step=100, key="test_v"
        )
        test_conversions = st.number_input(
            "Conversions", min_value=0, value=340, step=10, key="test_c"
        )
        if test_visitors > 0:
            st.caption(f"Rate: {test_conversions / test_visitors:.2%}")

    alpha_map = {"90%": 0.10, "95%": 0.05, "99%": 0.01}
    confidence = st.select_slider(
        "Confidence level", options=["90%", "95%", "99%"], value="95%"
    )
    alpha = alpha_map[confidence]

    if st.button("Run test", type="primary", use_container_width=True):
        try:
            r = run_ab_test(
                int(ctrl_visitors),
                int(ctrl_conversions),
                int(test_visitors),
                int(test_conversions),
                alpha=alpha,
            )

            st.divider()

            # Verdict banner
            if r["significant"]:
                st.success(
                    f"✅ Statistically significant at {confidence} confidence — "
                    f"safe to make a decision on this result."
                )
            else:
                st.error(
                    f"❌ Not significant at {confidence} confidence — "
                    f"do not ship based on this result alone."
                )

            # Key metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Control rate", f"{r['control_rate']:.2%}")
            m2.metric(
                "Test rate",
                f"{r['test_rate']:.2%}",
                delta=f"{r['relative_uplift']:+.1f}% uplift",
            )
            m3.metric("p-value", f"{r['p_value']:.4f}", delta=f"threshold {alpha:.2f}", delta_color="off")
            m4.metric("Z-statistic", f"{r['z_stat']:.3f}")

            # Confidence interval
            ci_sign = "excludes" if (r["ci_lower"] > 0 or r["ci_upper"] < 0) else "includes"
            st.info(
                f"**{confidence} CI on difference:** "
                f"[{r['ci_lower']:+.4f}, {r['ci_upper']:+.4f}]  —  "
                f"CI {ci_sign} zero. "
                + ("Real effect detected." if ci_sign == "excludes" else "Cannot rule out no effect.")
            )

            # Bar chart
            fig, ax = plt.subplots(figsize=(5, 3))
            bars = ax.bar(
                ["Control", "Test"],
                [r["control_rate"] * 100, r["test_rate"] * 100],
                color=["#4C72B0", "#DD8452"],
                width=0.4,
                edgecolor="white",
            )
            ax.bar_label(bars, fmt="%.2f%%", padding=3, fontsize=10)
            ax.set_ylabel("Conversion rate (%)")
            ax.set_title("Control vs Test conversion rate")
            ax.set_ylim(0, max(r["control_rate"], r["test_rate"]) * 100 * 1.3)
            ax.spines[["top", "right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        except ValueError as e:
            st.error(f"Input error: {e}")


# ── Tab 2: Plan a Test ────────────────────────────────────────────────────────
with tab2:
    st.subheader("How many visitors do you need?")

    baseline_pct = st.slider(
        "Baseline conversion rate (%)",
        min_value=0.5,
        max_value=50.0,
        value=3.0,
        step=0.5,
        format="%.1f%%",
    )
    baseline_rate = baseline_pct / 100

    mde_pct = st.slider(
        "Minimum detectable effect — relative uplift (%)",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
        format="%d%%",
        help="The smallest improvement worth detecting. Smaller = more users needed.",
    )
    mde = mde_pct / 100

    col_a, col_b = st.columns(2)
    with col_a:
        conf_plan = st.select_slider(
            "Confidence level", options=["90%", "95%", "99%"], value="95%", key="conf_plan"
        )
    with col_b:
        power_map = {"70%": 0.70, "80%": 0.80, "90%": 0.90}
        power_sel = st.select_slider(
            "Statistical power", options=["70%", "80%", "90%"], value="80%"
        )

    daily_visitors = st.number_input(
        "Daily visitors to this page/flow (optional — for runtime estimate)",
        min_value=0,
        value=5000,
        step=500,
    )

    if st.button("Calculate sample size", type="primary", use_container_width=True):
        try:
            s = calculate_sample_size(
                baseline_rate=baseline_rate,
                mde=mde,
                alpha=alpha_map[conf_plan],
                power=power_map[power_sel],
            )

            st.divider()

            c1, c2, c3 = st.columns(3)
            c1.metric("Per variant", f"{s['per_variant']:,}")
            c2.metric("Total visitors needed", f"{s['total']:,}")
            c3.metric(
                "Target rate",
                f"{s['target_rate']:.2%}",
                delta=f"+{mde_pct}% vs baseline",
            )

            if daily_visitors > 0:
                days_needed = s["total"] / daily_visitors
                weeks = days_needed / 7
                st.info(
                    f"⏱ At **{daily_visitors:,} daily visitors**, this test would need "
                    f"approximately **{days_needed:.0f} days ({weeks:.1f} weeks)** to reach "
                    f"the required sample size."
                )
                if days_needed < 3:
                    st.warning(
                        "⚠️ Runtime under 3 days risks novelty effects — "
                        "consider running longer to let behaviour stabilise."
                    )

            st.info(
                f"**How to read this:** You need {s['per_variant']:,} users per variant "
                f"to detect a {mde_pct}% relative uplift over your {baseline_pct:.1f}% baseline "
                f"with {power_sel} power at {conf_plan} confidence. "
                f"Stopping early risks false positives — commit to this number before you start."
            )

        except ValueError as e:
            st.error(f"Input error: {e}")
