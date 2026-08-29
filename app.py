"""
app.py
------
AI Revenue Recovery Agent - Streamlit Dashboard

Entry point for the application. Run with:
    streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.analyzer import analyze_failed_transactions
from agents.decision_agent import decide_for_dataframe
from agents.message_generator import generate_recovery_message
from models.recovery_model import RecoveryModel
from utils.data_processor import apply_filters, compute_summary_metrics, load_data

# --------------------------------------------------------------------------
# Page config + light custom styling
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Revenue Recovery Agent",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Sun ☀️ / Moon 🌙 Dynamic Theme Management
# --------------------------------------------------------------------------

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# Dynamic CSS Injection based on Sun ☀️ / Moon 🌙 selection
if st.session_state["theme"] == "dark":
    theme_css = """
    <style>
        .stAppDeployButton, [data-testid="stAppDeployButton"], footer {
            display: none !important;
        }
        .stApp {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
        }
        [data-testid="stSidebar"] {
            background-color: #1E293B !important;
            border-right: 1px solid #334155 !important;
        }
        [data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        .metric-card {
            background: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 12px;
            padding: 16px 20px;
            color: #FFFFFF !important;
        }
        div[data-testid="stMetric"] {
            background: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 12px;
            padding: 14px 18px 8px 18px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 800 !important;
        }
        .priority-high { color: #F43F5E; font-weight: 700; }
        .priority-medium { color: #F59E0B; font-weight: 700; }
        .priority-low { color: #10B981; font-weight: 700; }
        .explain-box {
            background: #1E293B !important;
            border-left: 4px solid #3B82F6 !important;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
            color: #E2E8F0 !important;
        }
        .synthetic-badge {
            background: #312E81;
            color: #A5B4FC;
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid #4338CA;
        }
    </style>
    """
    plotly_template = "plotly_dark"
else:
    theme_css = """
    <style>
        .stAppDeployButton, [data-testid="stAppDeployButton"], footer {
            display: none !important;
        }
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }
        [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
            color: #0F172A !important;
            font-weight: 600;
        }
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        .metric-card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px;
            padding: 16px 20px;
            color: #0F172A !important;
        }
        div[data-testid="stMetric"] {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 12px;
            padding: 14px 18px 8px 18px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: #334155 !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0F172A !important;
            font-weight: 800 !important;
        }
        .priority-high { color: #E11D48; font-weight: 700; }
        .priority-medium { color: #D97706; font-weight: 700; }
        .priority-low { color: #059669; font-weight: 700; }
        .explain-box {
            background: #F1F5F9 !important;
            border-left: 4px solid #2563EB !important;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
            color: #1E293B !important;
        }
        .synthetic-badge {
            background: #EEF2FF;
            color: #3730A3;
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid #C7D2FE;
        }
    </style>
    """
    plotly_template = "plotly_white"

st.markdown(theme_css, unsafe_allow_html=True)


def style_fig(fig):
    """Align Plotly chart backgrounds and fonts seamlessly with page theme to guarantee high contrast."""
    is_dark = st.session_state.get("theme", "dark") == "dark"
    font_color = "#F8FAFC" if is_dark else "#0F172A"
    grid_color = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.15)"

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, family="sans-serif", size=12),
        margin=dict(l=30, r=30, t=50, b=40),
        legend=dict(font=dict(color=font_color)),
        title=dict(font=dict(color=font_color, size=15))
    )
    fig.update_xaxes(
        tickfont=dict(color=font_color, size=11),
        title_font=dict(color=font_color, size=12),
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    fig.update_yaxes(
        tickfont=dict(color=font_color, size=11),
        title_font=dict(color=font_color, size=12),
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    fig.update_traces(
        textfont=dict(color=font_color)
    )
    return fig

st.markdown(theme_css, unsafe_allow_html=True)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "payments.csv")


# --------------------------------------------------------------------------
# Cached data loading + analysis pipeline
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_analyzed_data(path: str) -> pd.DataFrame:
    """Load raw data, then run it through the rule-based analyzer + decision agent."""
    df = load_data(path)
    df = analyze_failed_transactions(df)

    recovery_probabilities = None
    if RecoveryModel.model_exists():
        try:
            model = RecoveryModel.load()
            failed_mask = df["payment_status"] == "Failed"
            probs = model.predict_proba(df.loc[failed_mask])
            recovery_probabilities = pd.Series(probs, index=df.loc[failed_mask].index)
        except Exception:
            recovery_probabilities = None

    df = decide_for_dataframe(df, recovery_probabilities)

    if recovery_probabilities is not None:
        df["ml_recovery_probability"] = recovery_probabilities.reindex(df.index)
    else:
        df["ml_recovery_probability"] = None

    return df


def priority_badge(priority: str) -> str:
    if priority == "High Priority":
        return f'<span class="priority-high">🔴 {priority}</span>'
    elif priority == "Medium Priority":
        return f'<span class="priority-medium">🟠 {priority}</span>'
    elif priority == "Low Priority":
        return f'<span class="priority-low">🟢 {priority}</span>'
    return priority or "-"


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


# --------------------------------------------------------------------------
# Load data (with a friendly error if missing)
# --------------------------------------------------------------------------

if not os.path.exists(DATA_PATH):
    st.error(
        "No dataset found at data/payments.csv.\n\n"
        "Run `python data/generate_data.py` from the project root to generate the synthetic demo dataset."
    )
    st.stop()

df = get_analyzed_data(DATA_PATH)
model_ready = RecoveryModel.model_exists()

# --------------------------------------------------------------------------
# Sidebar navigation + filters
# --------------------------------------------------------------------------

col_head, col_theme = st.sidebar.columns([3.5, 1])
with col_head:
    st.markdown("### 💳 AI Recovery")
with col_theme:
    icon_btn = "☀️" if st.session_state["theme"] == "dark" else "🌙"
    if st.button(icon_btn, key="theme_icon_btn_toggle", help="Toggle Theme"):
        st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
        st.rerun()

st.sidebar.markdown('<span class="synthetic-badge">SYNTHETIC DEMO DATA</span>', unsafe_allow_html=True)
st.sidebar.caption("Built for the Razorpay AI Buildathon 2026")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🔎 Transaction Explorer", "🤖 AI Recovery Center", "📈 Analytics"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

min_date = df["transaction_date"].min().date()
max_date = df["transaction_date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

status_options = ["All"] + sorted(df["payment_status"].unique().tolist())
status_sel = st.sidebar.multiselect("Payment status", status_options, default=["All"])

method_options = ["All"] + sorted(df["payment_method"].unique().tolist())
method_sel = st.sidebar.multiselect("Payment method", method_options, default=["All"])

reason_options = ["All"] + sorted(df["failure_reason"].dropna().unique().tolist())
reason_sel = st.sidebar.multiselect("Failure reason", reason_options, default=["All"])

priority_options = ["All"] + sorted(df["priority"].dropna().unique().tolist())
priority_sel = st.sidebar.multiselect("Priority", priority_options, default=["All"])

segment_options = ["All"] + sorted(df["customer_segment"].unique().tolist())
segment_sel = st.sidebar.multiselect("Customer segment", segment_options, default=["All"])

filtered_df = apply_filters(
    df,
    date_range=date_range if isinstance(date_range, tuple) else None,
    payment_status=status_sel,
    payment_method=method_sel,
    failure_reason=reason_sel,
    priority=priority_sel,
    customer_segment=segment_sel,
)

if not model_ready:
    st.sidebar.warning(
        "ML recovery model not trained yet.\n\nRun `python models/train_model.py` to enable "
        "ML-based recovery probability. The app works fine without it (rule-based scoring only)."
    )

# ==========================================================================
# PAGE: DASHBOARD
# ==========================================================================

if page == "📊 Dashboard":
    st.title("Revenue Recovery Dashboard")
    st.caption("Overview of payment performance and AI-estimated recoverable revenue.")

    metrics = compute_summary_metrics(filtered_df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transactions", f"{metrics['total_transactions']:,}")
    c2.metric("Successful Payments", f"{metrics['successful_transactions']:,}")
    c3.metric("Failed Payments", f"{metrics['failed_transactions']:,}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Failed Revenue", format_inr(metrics["failed_revenue"]))
    c5.metric("Potential Recoverable Revenue", format_inr(metrics["potential_recoverable_revenue"]))
    c6.metric("Recovery Rate", f"{metrics['recovery_rate']}%")

    st.markdown("### ")
    col1, col2 = st.columns(2)

    with col1:
        status_counts = filtered_df["payment_status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count", title="Payment Success vs Failure",
                     color="status", color_discrete_map={"Success": "#10B981", "Failed": "#F43F5E"}, hole=0.45)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col2:
        failed_only = filtered_df[filtered_df["payment_status"] == "Failed"]
        reason_counts = failed_only["failure_reason"].value_counts().reset_index()
        reason_counts.columns = ["failure_reason", "count"]
        fig = px.bar(reason_counts, x="failure_reason", y="count", title="Failure Reasons",
                     color="count", color_continuous_scale="Reds")
        fig.update_layout(xaxis_title="", yaxis_title="Count")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        rev_by_method = filtered_df.groupby("payment_method")["amount"].sum().reset_index()
        fig = px.bar(rev_by_method.sort_values("amount", ascending=False), x="payment_method", y="amount",
                     title="Revenue by Payment Method", color="amount", color_continuous_scale="Blues")
        fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col4:
        priority_counts = failed_only["priority"].value_counts().reset_index()
        priority_counts.columns = ["priority", "count"]
        fig = px.pie(priority_counts, names="priority", values="count", title="Recovery Priority Distribution",
                     color="priority",
                     color_discrete_map={"High Priority": "#F43F5E", "Medium Priority": "#F59E0B", "Low Priority": "#10B981"},
                     hole=0.45)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    seg_failed_rev = failed_only.groupby("customer_segment")["amount"].sum().reset_index()
    fig = px.bar(seg_failed_rev.sort_values("amount", ascending=False), x="customer_segment", y="amount",
                 title="Failed Revenue by Customer Segment", color="amount", color_continuous_scale="Oranges")
    fig.update_layout(xaxis_title="", yaxis_title="Failed Revenue (₹)")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("### Failed Transactions")
    display_cols = ["transaction_id", "customer_name", "amount", "payment_method", "failure_reason",
                     "priority", "recovery_score", "recommended_action"]
    st.dataframe(
        failed_only[display_cols].sort_values("recovery_score", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ==========================================================================
# PAGE: TRANSACTION EXPLORER
# ==========================================================================

elif page == "🔎 Transaction Explorer":
    st.title("Transaction Explorer")
    st.caption("Browse every transaction and drill into a specific one for full AI analysis.")

    view_cols = ["transaction_id", "customer_name", "amount", "payment_method", "payment_status",
                 "failure_reason", "priority", "recovery_score", "recommended_action"]
    st.dataframe(filtered_df[view_cols], use_container_width=True, hide_index=True, height=350)

    st.markdown("---")
    st.subheader("Transaction Detail")

    failed_ids = filtered_df.loc[filtered_df["payment_status"] == "Failed", "transaction_id"].tolist()
    if not failed_ids:
        st.info("No failed transactions in the current filter selection.")
    else:
        selected_id = st.selectbox("Select a failed transaction to inspect", failed_ids)
        row = filtered_df.loc[filtered_df["transaction_id"] == selected_id].iloc[0]

        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### Customer Information")
            st.write(f"**Name:** {row['customer_name']}")
            st.write(f"**Customer ID:** {row['customer_id']}")
            st.write(f"**Segment:** {row['customer_segment']}")
            st.write(f"**History:** {row['customer_history']}")

        with colB:
            st.markdown("#### Transaction Information")
            st.write(f"**Transaction ID:** {row['transaction_id']}")
            st.write(f"**Amount:** {format_inr(row['amount'])} ({row['currency']})")
            st.write(f"**Payment Method:** {row['payment_method']}")
            st.write(f"**Date:** {row['transaction_date']}")
            st.write(f"**Retry Count:** {row['retry_count']}")

        st.markdown("#### Failure & Recovery Analysis")
        st.write(f"**Failure Reason:** {row['failure_reason']}")
        st.markdown(f"**Priority:** {priority_badge(row['priority'])}", unsafe_allow_html=True)
        st.write(f"**Recovery Score:** {row['recovery_score']} / 100")
        if pd.notna(row.get("ml_recovery_probability")):
            st.write(f"**ML Recovery Probability:** {row['ml_recovery_probability'] * 100:.1f}%")

        st.markdown(f'<div class="explain-box">🧠 <b>AI Analysis:</b> {row["priority_explanation"]}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="explain-box">🤖 <b>Recommended Action — {row["recommended_action"]}:</b> {row["action_explanation"]}</div>', unsafe_allow_html=True)

        st.markdown("#### Recovery Message")
        msg_key = f"msg_{selected_id}"
        if st.button("✨ Generate AI Recovery Message", key=f"gen_{selected_id}"):
            with st.spinner("Generating personalized message..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
                st.session_state[msg_key] = result

        if msg_key in st.session_state:
            result = st.session_state[msg_key]
            mode_label = "🧠 Generated by LLM" if result["mode"] == "llm" else "📋 Generated from template (fallback mode)"
            st.success(result["message"])
            st.caption(mode_label)
            if result.get("error"):
                st.caption(f"LLM call failed, used fallback. Details: {result['error']}")

# ==========================================================================
# PAGE: AI RECOVERY CENTER
# ==========================================================================

elif page == "🤖 AI Recovery Center":
    st.title("AI Recovery Center")
    st.caption("High-priority cases and AI-recommended recovery actions, ready for outreach.")

    failed_df = filtered_df[filtered_df["payment_status"] == "Failed"].copy()
    high_priority = failed_df[failed_df["priority"] == "High Priority"].sort_values("recovery_score", ascending=False)

    m1, m2, m3 = st.columns(3)
    m1.metric("High-Priority Cases", len(high_priority))
    m2.metric("High-Priority Recoverable Value", format_inr(high_priority["amount"].sum()))
    m3.metric("Avg. Recovery Score (High Priority)", f"{high_priority['recovery_score'].mean():.1f}" if len(high_priority) else "-")

    st.markdown("### High-Priority Recovery Cases")
    st.dataframe(
        high_priority[["transaction_id", "customer_name", "amount", "failure_reason",
                        "recovery_score", "recommended_action"]],
        use_container_width=True, hide_index=True,
    )

    st.markdown("### AI Recommendations Breakdown")
    action_counts = failed_df["recommended_action"].value_counts().reset_index()
    action_counts.columns = ["recommended_action", "count"]
    fig = px.bar(action_counts.sort_values("count", ascending=True), x="count", y="recommended_action",
                 orientation="h", title="Recommended Actions Across All Failed Transactions",
                 color="count", color_continuous_scale="Purples")
    fig.update_layout(yaxis_title="", xaxis_title="Number of transactions")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("### Batch Message Generation")
    st.caption("Generate recovery messages for the top High-Priority cases in one click.")

    top_n = st.slider("How many top cases to generate messages for?", 1, min(10, max(len(high_priority), 1)), min(3, max(len(high_priority), 1)))

    if st.button("Generate messages for top cases"):
        top_cases = high_priority.head(top_n)
        for _, row in top_cases.iterrows():
            with st.spinner(f"Generating message for {row['customer_name']}..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
            with st.expander(f"{row['customer_name']} — {row['transaction_id']} ({format_inr(row['amount'])})"):
                st.write(f"**Action:** {row['recommended_action']}")
                st.info(result["message"])
                st.caption("🧠 LLM-generated" if result["mode"] == "llm" else "📋 Template fallback")

# ==========================================================================
# PAGE: ANALYTICS
# ==========================================================================

elif page == "📈 Analytics":
    st.title("Analytics")
    st.caption("Deeper revenue recovery estimation and model performance.")

    metrics = compute_summary_metrics(filtered_df)

    st.markdown("### Revenue Recovery Estimation")
    est_df = pd.DataFrame(
        {
            "Metric": [
                "Total Transaction Value", "Successful Revenue", "Failed Revenue",
                "Potential Recoverable Revenue", "High-Priority Recoverable Revenue", "Recovery Rate",
            ],
            "Value": [
                format_inr(metrics["total_value"]), format_inr(metrics["successful_revenue"]),
                format_inr(metrics["failed_revenue"]), format_inr(metrics["potential_recoverable_revenue"]),
                format_inr(metrics["high_priority_recoverable_revenue"]), f"{metrics['recovery_rate']}%",
            ],
        }
    )
    st.table(est_df)

    st.markdown("### Recovery Rate Trend (by day)")
    daily = filtered_df.copy()
    daily["date"] = daily["transaction_date"].dt.date
    daily_failed = daily[daily["payment_status"] == "Failed"].groupby("date")["amount"].sum()
    daily_recoverable = (
        daily[daily["payment_status"] == "Failed"]
        .assign(recoverable=lambda d: d["amount"] * (d["recovery_score"].fillna(0) / 100))
        .groupby("date")["recoverable"].sum()
    )
    trend = pd.DataFrame({"Failed Revenue": daily_failed, "Recoverable Revenue": daily_recoverable}).fillna(0).reset_index()
    if len(trend):
        fig = px.line(trend, x="date", y=["Failed Revenue", "Recoverable Revenue"], title="Failed vs Recoverable Revenue Over Time")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    else:
        st.info("No data in the current filter range to plot a trend.")

    st.markdown("### ML Model Performance")
    if model_ready:
        try:
            model = RecoveryModel.load()
            importances = model.feature_importances().head(10)
            fig = px.bar(importances[::-1], orientation="h", title="Top Feature Importances (Recovery Likelihood Model)")
            fig.update_layout(yaxis_title="", xaxis_title="Importance", showlegend=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption(
                "This RandomForest model was trained on historical failed transactions to predict the "
                "probability that a retry/follow-up will succeed. Run `python models/train_model.py` "
                "to retrain and see evaluation metrics (accuracy, precision, recall, ROC-AUC) in the terminal."
            )
        except Exception as exc:
            st.warning(f"Could not load model details: {exc}")
    else:
        st.info("Train the model with `python models/train_model.py` to see feature importance here.")

st.markdown("---")
st.caption(
    "⚠️ All transaction and customer data shown is synthetically generated for demonstration purposes only. "
    "This project is not officially affiliated with or connected to Razorpay's live payment systems."
)
