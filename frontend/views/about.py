"""
Cinevora About & Architecture View
Comprehensive system documentation, architectural overview,
mathematical modeling details, and dataset provenance.
"""

import streamlit as st
from frontend.components import render_header, render_metric_card


def render_about_page():
    """Renders the About Cinevora architectural and technical documentation page."""
    render_header("System Architecture & Machine Learning Foundations")

    st.markdown(
        """
        **Cinevora** is a production-grade, real-time movie recommendation service combining classical 
        machine learning matrix factorization, content-based genre modeling, conversational AI reasoning 
        via Google Gemini, and comprehensive MLOps observability.
        """
    )

    # High Level KPI Highlights
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Catalog Scale", "1,682 Movies", "GroupLens ml-100k", border_color="#3B82F6")
    with m2:
        render_metric_card("Interaction Scale", "100,000 Ratings", "943 unique users", border_color="#10B981")
    with m3:
        render_metric_card("Latent Factors", "k = 20", "Truncated SVD", border_color="#F59E0B")
    with m4:
        render_metric_card("AI Reasoning", "Gemini 3.5 Flash Lite", "Grounded catalog", border_color="#8B5CF6")

    st.write("")

    # Architecture Overview
    st.markdown("### 🏛️ System Architecture")
    st.markdown(
        """
        The platform is engineered with a decoupled service-oriented architecture:
        
        1. **Frontend (Streamlit)**: High-performance, modern streaming light-themed user interface offering interactive catalog exploration, model switching, conversational chat, watchlist management, and live Plotly MLOps telemetry.
        2. **Backend API (FastAPI)**: High-throughput asynchronous REST API exposing recommendation endpoints, catalog searches, user favorites/likes CRUD, telemetry aggregation, and Gemini assistant proxying.
        3. **Machine Learning Pipeline**:
           - **SVD Collaborative Filtering**: User-item rating matrix factorization learning 20-dimensional latent representations.
           - **Genre Content Engine**: Multi-hot 19-genre indicator vectors scored via Cosine Similarity.
           - **Popularity Baseline**: Bayesian-weighted ranking incorporating rating frequency and average score.
           - **Hybrid Ensemble**: Weighted linear combination ($0.50 \\times \\text{SVD} + 0.35 \\times \\text{Content} + 0.15 \\times \\text{Popularity}$).
        4. **AI Assistant (Google Gemini 3.5 Flash Lite)**: Natural-language request parser and narrative generator, strictly grounded against Cinevora's verified catalog with application-level genre and decade constraints.
        5. **Persistence & Observability (SQLite & Middleware)**: High-resolution telemetry capturing real HTTP duration, status codes, endpoint metrics, empty recommendation rates, and user interactions.
        """
    )

    # Technical Deep Dive: Recommendation Mathematics
    with st.expander("📐 Mathematical Formulations & Modeling", expanded=True):
        st.markdown(
            """
            #### 1. Truncated Singular Value Decomposition (SVD)
            The sparse user-item interaction matrix $R \\in \\mathbb{R}^{m \\times n}$ (where $m=943$, $n=1,682$) is centered around item means and decomposed into low-rank latent representations:
            $$R \\approx U \\Sigma V^T = P Q^T$$
            For user $u$ and item $i$, the predicted preference is estimated by:
            $$\\hat{r}_{ui} = \\mu + b_u + b_i + \\mathbf{p}_u \\cdot \\mathbf{q}_i^T$$
            where $\\mu$ is the global rating average, $b_u$ is user rating bias, $b_i$ is movie rating bias, and $\\mathbf{p}_u, \\mathbf{q}_i \\in \\mathbb{R}^{20}$ are the latent factor embeddings.

            #### 2. Multi-Label Genre Cosine Similarity
            Each movie is encoded as a binary feature vector $\\mathbf{g}_i \\in \\{0, 1\\}^{18}$ corresponding to the 18 standard MovieLens genres.
            For a target user, their profile $\\mathbf{u}_{\\text{genre}}$ is derived from the mean genre vectors of their positively rated movies ($r_{ui} \\ge 4.0$).
            Similarity is calculated via the cosine angle:
            $$\\text{Sim}(\\mathbf{u}, \\mathbf{g}_i) = \\frac{\\mathbf{u} \\cdot \\mathbf{g}_i}{\\|\\mathbf{u}\\| \\|\\mathbf{g}_i\\|}$$

            #### 3. Bayesian Popularity Scoring
            To prevent small-sample rating noise from dominating recommendations, baseline popularity incorporates empirical Bayes dampening:
            $$S_{\\text{pop}}(i) = \\frac{v_i}{v_i + m} \\cdot R_i + \\frac{m}{v_i + m} \\cdot C$$
            where $v_i$ is the number of ratings for movie $i$, $m$ is the minimum threshold (e.g. 20 ratings), $R_i$ is the movie's average rating, and $C$ is the catalog mean.
            """
        )

    # Dataset & Media Provenance
    with st.expander("📚 Dataset & Cinematic Media Provenance", expanded=False):
        st.markdown(
            """
            #### 1. GroupLens MovieLens 100K Core Catalog
            - **Origin**: Collected by the GroupLens Research Project at the University of Minnesota (September 1997 – April 1998).
            - **Content**: 100,000 ratings on a 1–5 integral scale from 943 users on 1,682 movies.
            - **Density**: Each user has rated at least 20 movies (matrix sparsity approx. 93.7%).
            - **Catalog Fields**: Release year, IMDb link, and 19 genre indicators.

            #### 2. Cinematic Media & Image Enrichment
            - **Portrait Posters (2:3 Aspect Ratio)**: 1,670 verified movie posters mapped directly to MovieLens IDs via IMDb / Amazon CDN metadata.
            - **Landscape Backdrops (16:9 Aspect Ratio)**: High-definition 1280px backdrops for catalog spotlight features sourced via The Movie Database (TMDb).
            - **Verified Synopses & Trailers**: Canonical storylines and official YouTube trailer embeds.
            - **Local Enrichment Manifest**: Cached in `data/processed/movie_enrichment.json` for zero-latency presentation without runtime external API dependencies.
            - **Extensibility**: Configurable with optional `TMDB_API_KEY` in `.env` via `scripts/enrich_movie_images.py`.
            """
        )

    # Security & MLOps Hygiene
    with st.expander("🔒 Security, Privacy & MLOps Hygiene"):
        st.markdown(
            """
            - **Secret Isolation**: `GEMINI_API_KEY` is loaded strictly via environment variables / `.env`, validated by Pydantic settings, and never printed, logged, or returned via any API response.
            - **Decoupled Architecture**: The Streamlit user interface communicates solely over HTTP REST; recommendation logic and model matrices are not duplicated in the presentation tier.
            - **Data Integrity**: Telemetry middleware measures actual request latency using monotonic nanosecond counters (`time.perf_counter()`), sanitizes client IP addresses, and flags internal health probes.
            - **Offline vs Online Separation**: Model evaluation metrics (RMSE, Precision@10, Recall@10) are preserved from held-out test splits, preventing conflation with real-time API uptime statistics.
            """
        )
