"""
Cinevora MLOps Monitoring Dashboard View
Real-time operational telemetry and offline machine learning evaluation dashboard.
Features:
- Live request throughput, p50 and p95 latency distributions
- HTTP status code breakdown
- Most active endpoints
- Recommendation telemetry (request volume, empty recommendation rate)
- AI Assistant telemetry (Gemini invocation volume, catalog fallback rate)
- Inspectable live event log table
- Offline Model Evaluation Benchmarks (Precision@10, Recall@10, NDCG@10, RMSE)
  clearly distinguished from live production metrics.
"""

import json
import os
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from frontend.api_client import api_client
from frontend.components import render_header, render_metric_card, render_empty_state
from frontend.config import COLORS


def _load_offline_benchmarks() -> Optional[Dict[str, Any]]:
    """Loads static model evaluation benchmarks from reports/recommendation_evaluation.json."""
    eval_path = os.path.join("reports", "recommendation_evaluation.json")
    if os.path.exists(eval_path):
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def render_monitoring_page():
    """Renders the comprehensive MLOps monitoring dashboard."""
    render_header("MLOps Telemetry & Service Operations Room")

    # Controls Row
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([2, 1.5, 1])
    with c_ctrl1:
        st.caption("Live metrics reflect actual HTTP requests handled by the FastAPI backend and recorded in SQLite.")
    with c_ctrl2:
        exclude_internal = st.checkbox("Filter out /health checks", value=True)
    with c_ctrl3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Fetch live telemetry from FastAPI backend
    with st.spinner("Connecting to telemetry engine"):
        metrics = api_client.get_monitoring_metrics(exclude_internal=exclude_internal) or {}
        events = api_client.get_monitoring_events(limit=50)

    total_reqs = metrics.get("total_requests", 0)
    avg_latency = metrics.get("avg_latency_ms", 0.0)
    p50_latency = metrics.get("median_latency_ms", 0.0)
    p95_latency = metrics.get("p95_latency_ms", 0.0)
    rec_reqs = metrics.get("recommendation_requests", 0)
    empty_rate = metrics.get("empty_recommendation_rate", 0.0)
    asst_reqs = metrics.get("assistant_requests", 0)
    fallback_rate = metrics.get("assistant_fallback_rate", 0.0)
    status_counts = metrics.get("status_counts", {})
    endpoint_counts = metrics.get("endpoint_counts", {})

    # Live Production Telemetry Header Banner
    st.markdown("## 📡 1. Live Production Telemetry (SQLite Backed)")

    # Latency & Throughput KPIs
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Live Throughput", f"{total_reqs:,}", "Total API Requests", border_color="#3B82F6")
    with kpi2:
        render_metric_card("P50 Median Latency", f"{p50_latency:.1f} ms", "50th percentile", border_color="#10B981")
    with kpi3:
        p95_color = "#10B981" if p95_latency < 100 else "#F59E0B" if p95_latency < 300 else "#EF4444"
        render_metric_card("P95 Latency", f"{p95_latency:.1f} ms", "95th percentile", border_color=p95_color)
    with kpi4:
        render_metric_card("Avg Response", f"{avg_latency:.1f} ms", "Mean duration", border_color="#6366F1")
    with kpi5:
        empty_pct = f"{empty_rate * 100:.1f}%"
        render_metric_card("Empty Recs Rate", empty_pct, f"{rec_reqs} rec queries", border_color="#F59E0B")

    st.write("")

    # Visualizations Row: Traffic Distribution & Status Codes
    chart_col1, chart_col2 = st.columns([1.5, 1])

    with chart_col1:
        st.markdown("#### Endpoint Traffic Distribution")
        if endpoint_counts:
            # Sort top endpoints
            sorted_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            ep_df = pd.DataFrame(sorted_endpoints, columns=["Endpoint", "Requests"])

            fig_ep = px.bar(
                ep_df,
                x="Requests",
                y="Endpoint",
                orientation="h",
                color="Requests",
                color_continuous_scale=["#1D4ED8", "#3B82F6", "#60A5FA"],
                text="Requests"
            )
            fig_ep.update_layout(
                paper_bgcolor="#141520",
                plot_bgcolor="#141520",
                font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=20, t=20, b=20),
                height=280,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed", gridcolor="#222538"),
                xaxis=dict(gridcolor="#222538")
            )
            fig_ep.update_traces(textposition="outside")
            st.plotly_chart(fig_ep, use_container_width=True)
        else:
            st.info("No endpoint traffic recorded yet.")

    with chart_col2:
        st.markdown("#### HTTP Status Code Breakdown")
        if status_counts:
            status_df = pd.DataFrame(
                list(status_counts.items()),
                columns=["Status Code", "Count"]
            )
            status_colors = {
                "200": "#10B981",
                "201": "#34D399",
                "400": "#F59E0B",
                "404": "#F97316",
                "422": "#EF4444",
                "500": "#DC2626"
            }
            colors_list = [status_colors.get(str(s), "#94A3B8") for s in status_df["Status Code"]]

            fig_status = go.Figure(
                data=[
                    go.Pie(
                        labels=[f"HTTP {s}" for s in status_df["Status Code"]],
                        values=status_df["Count"],
                        hole=0.6,
                        marker=dict(colors=colors_list, line=dict(color="#FFFFFF", width=2))
                    )
                ]
            )
            fig_status.update_layout(
                paper_bgcolor="#141520",
                plot_bgcolor="#141520",
                font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=20, b=20),
                height=280,
                showlegend=True
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No status code data available.")

    # Latency Distribution from Recent Events
    if events:
        latencies = [e["duration_ms"] for e in events if e.get("duration_ms") is not None]
        if latencies:
            st.markdown("#### Latency Distribution (Recent Sample)")
            fig_lat = px.histogram(
                latencies,
                nbins=20,
                labels={"value": "Duration (ms)"},
                title="Response Latency Histogram",
                color_discrete_sequence=["#E50914"]
            )
            fig_lat.update_layout(
                paper_bgcolor="#141520",
                plot_bgcolor="#141520",
                font=dict(color="#FFFFFF"),
                margin=dict(l=20, r=20, t=40, b=20),
                height=220,
                showlegend=False,
                xaxis_title="Latency (ms)",
                yaxis_title="Count",
                xaxis=dict(gridcolor="#222538"),
                yaxis=dict(gridcolor="#222538")
            )
            st.plotly_chart(fig_lat, use_container_width=True)

    # Inspectable Live Events Stream Table
    with st.expander(f"📋 Live Event Stream ({len(events)} Most Recent Requests)", expanded=True):
        if events:
            table_rows = []
            for ev in events:
                table_rows.append({
                    "Timestamp": ev.get("timestamp", "")[:19].replace("T", " "),
                    "Method": ev.get("method", ""),
                    "Path": ev.get("path", ""),
                    "Status": ev.get("status_code", 0),
                    "Duration (ms)": f"{ev.get('duration_ms', 0):.2f}",
                    "User ID": ev.get("user_id") or "anonymous",
                    "Internal": "Yes" if ev.get("is_internal") else "No"
                })
            df_events = pd.DataFrame(table_rows)
            st.dataframe(df_events, use_container_width=True, hide_index=True)
        else:
            st.info("No events recorded in SQLite yet.")

    st.write("---")

    # Offline Benchmark Section
    st.markdown("## 🧪 2. Offline Model Evaluation Benchmarks")
    st.caption(
        "Static benchmark computed on held-out test split (20% of MovieLens 100K ratings, random seed 42). "
        "These metrics evaluate recommendation ranking accuracy and rating prediction error before deployment."
    )

    offline_data = _load_offline_benchmarks()
    if offline_data:
        ranking = offline_data.get("ranking_metrics", {})
        rmse_data = offline_data.get("rating_prediction_rmse", {})

        # Offline KPI Summary Cards
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            collab_p10 = ranking.get("collaborative", {}).get("precision@10", 0.0)
            render_metric_card("SVD Precision@10", f"{collab_p10 * 100:.2f}%", "Top-10 relevance", border_color="#10B981")
        with b2:
            collab_ndcg = ranking.get("collaborative", {}).get("ndcg@10", 0.0)
            render_metric_card("SVD NDCG@10", f"{collab_ndcg:.4f}", "Ranking discount", border_color="#3B82F6")
        with b3:
            hybrid_p10 = ranking.get("hybrid", {}).get("precision@10", 0.0)
            render_metric_card("Hybrid Precision@10", f"{hybrid_p10 * 100:.2f}%", "Blended ranking", border_color="#F59E0B")
        with b4:
            svd_rmse = rmse_data.get("rmse_collaborative_svd", 0.0)
            render_metric_card("SVD Rating RMSE", f"{svd_rmse:.4f}", "vs Global 1.1255", border_color="#8B5CF6")

        st.write("")

        # Plotly Comparison Bar Chart: Model vs Model Ranking Metrics
        st.markdown("#### Offline Model Comparison: Precision@10, Recall@10, NDCG@10")

        model_names = ["Popularity Baseline", "Genre Content", "SVD Collaborative", "Hybrid Recommender"]
        model_keys = ["popularity", "content", "collaborative", "hybrid"]

        precisions = [ranking.get(k, {}).get("precision@10", 0.0) * 100 for k in model_keys]
        recalls = [ranking.get(k, {}).get("recall@10", 0.0) * 100 for k in model_keys]
        ndcgs = [ranking.get(k, {}).get("ndcg@10", 0.0) * 100 for k in model_keys]

        fig_benchmark = go.Figure(
            data=[
                go.Bar(name="Precision@10 (%)", x=model_names, y=precisions, marker_color="#3B82F6"),
                go.Bar(name="Recall@10 (%)", x=model_names, y=recalls, marker_color="#10B981"),
                go.Bar(name="NDCG@10 (x100)", x=model_names, y=ndcgs, marker_color="#F59E0B")
            ]
        )

        fig_benchmark.update_layout(
            barmode="group",
            paper_bgcolor="#141520",
            plot_bgcolor="#141520",
            font=dict(color="#FFFFFF"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Score (%)",
            xaxis=dict(gridcolor="#222538"),
            yaxis=dict(gridcolor="#222538")
        )
        st.plotly_chart(fig_benchmark, use_container_width=True)

        # Rating RMSE Reduction Chart
        st.markdown("#### Rating Prediction Error (RMSE Lower is Better)")
        rmse_labels = ["Global Mean Baseline", "Movie Mean Baseline", "Truncated SVD (Cinevora)"]
        rmse_values = [
            rmse_data.get("rmse_global_baseline", 1.1255),
            rmse_data.get("rmse_movie_mean_baseline", 1.0231),
            rmse_data.get("rmse_collaborative_svd", 0.9885)
        ]

        fig_rmse = px.bar(
            x=rmse_labels,
            y=rmse_values,
            color=rmse_values,
            color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
            text=[f"{v:.4f}" for v in rmse_values]
        )
        fig_rmse.update_layout(
            paper_bgcolor="#141520",
            plot_bgcolor="#141520",
            font=dict(color="#FFFFFF"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=260,
            coloraxis_showscale=False,
            yaxis_title="RMSE",
            yaxis_range=[0.8, 1.2],
            xaxis=dict(gridcolor="#222538"),
            yaxis=dict(gridcolor="#222538")
        )
        fig_rmse.update_traces(textposition="outside")
        st.plotly_chart(fig_rmse, use_container_width=True)

    else:
        st.warning("Offline evaluation benchmark file (`reports/recommendation_evaluation.json`) was not found.")
