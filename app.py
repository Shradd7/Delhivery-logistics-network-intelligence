from pathlib import Path
import pickle

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Basic paths
# ---------------------------------------------------------------------------
# The dashboard uses lightweight result files and PNG plots only. It does not
# read the large raw CSV, which keeps deployment simple.
BASE_DIR = Path(__file__).parent
PLOTS_DIR = BASE_DIR / "assets" / "plots"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


st.set_page_config(
    page_title="Delhivery Logistics Network Intelligence",
    page_icon="DL",
    layout="wide",
)


def apply_custom_styles():
    """Add lightweight styling while keeping the app beginner-friendly."""
    st.markdown(
        """
        <style>
        :root {
            --ink: #18212f;
            --muted: #5d6678;
            --line: #d9dee8;
            --panel: #ffffff;
            --soft: #f5f7fb;
            --accent: #d9232e;
            --accent-dark: #9e1c25;
            --blue: #1f6feb;
            --green: #178a62;
        }

        .main .block-container {
            padding-top: 1.5rem;
            max-width: 1240px;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        [data-testid="stSidebar"] {
            background: #111827;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-left: 5px solid var(--accent);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            min-height: 118px;
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.86rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.8rem;
        }

        .hero {
            background: linear-gradient(135deg, #111827 0%, #263141 54%, #d9232e 100%);
            color: white;
            padding: 1.5rem 1.6rem;
            border-radius: 8px;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(255, 255, 255, 0.14);
        }

        .hero h1 {
            color: white;
            margin-bottom: 0.35rem;
            font-size: 2.15rem;
        }

        .hero p {
            color: #e5e7eb;
            max-width: 860px;
            margin-bottom: 0;
            font-size: 1rem;
        }

        .section-card {
            background: var(--soft);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.6rem 0 1rem 0;
        }

        .callout {
            border-left: 5px solid var(--blue);
            background: #f3f7ff;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            color: var(--ink);
            margin: 1rem 0;
        }

        .risk-callout {
            border-left-color: var(--accent);
            background: #fff5f5;
        }

        .small-label {
            color: var(--muted);
            font-size: 0.86rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.04rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Static summary metrics used even when pickle files are missing or unreadable.
# ---------------------------------------------------------------------------
KPI_METRICS = [
    ("Raw segments", "144,867"),
    ("Cleaned segments", "141,661"),
    ("Trips", "14,804"),
    ("Facilities", "1,657"),
    ("Corridors", "2,781"),
    ("OSRM MAE", "161.5 min"),
    ("RF MAE", "30.95 min"),
    ("Graph RF MAE", "29.85 min"),
]

ARTIFACT_FILES = {
    "Phase 1 checkpoint": "phase1_checkpoint.pkl",
    "Phase 2 checkpoint": "phase2_checkpoint.pkl",
    "Phase 3 checkpoint": "phase3_checkpoint.pkl",
    "Phase 4 results": "phase4_results.pkl",
    "Phase 5 checkpoint": "phase5_checkpoint.pkl",
    "Delay propagation results": "propagation_results.pkl",
    "Corridor risk results": "corridor_risk_results.pkl",
    "Hub simulation results": "hub_simulation_results.pkl",
}

PLOT_FILES = {
    "delay_analysis": "delay_analysis.png",
    "network_bottleneck": "network_bottleneck.png",
    "phase4_graph_advantage": "phase4_graph_advantage.png",
    "phase5_strategy": "phase5_strategy.png",
    "temporal_explainability": "temporal_explainability.png",
    "hub_intervention_simulator": "hub_intervention_simulator.png",
    "delay_propagation": "delay_propagation.png",
    "corridor_risk_ranking": "corridor_risk_ranking.png",
    "baseline_residuals": "baseline_residuals.png",
}


@st.cache_data(show_spinner=False)
def load_pickle(file_name: str):
    """Load a pickle artifact and return None if anything goes wrong."""
    file_path = ARTIFACTS_DIR / file_name
    try:
        with file_path.open("rb") as file:
            return pickle.load(file)
    except Exception:
        return None


def get_artifacts() -> dict:
    """Load all known artifacts into a dictionary."""
    return {
        label: load_pickle(file_name)
        for label, file_name in ARTIFACT_FILES.items()
    }


def plot_path(plot_key: str) -> Path:
    """Return the full path for a named plot."""
    return PLOTS_DIR / PLOT_FILES[plot_key]


def show_plot(plot_key: str, caption: str):
    """Display a PNG plot if it exists, otherwise show a friendly warning."""
    image_path = plot_path(plot_key)
    if image_path.exists():
        st.image(str(image_path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Missing plot: {image_path}")


def show_kpi_cards():
    """Render KPI cards in two rows."""
    first_row = st.columns(4)
    second_row = st.columns(4)
    for column, (label, value) in zip(first_row + second_row, KPI_METRICS):
        column.metric(label, value)


def summarize_artifact(value):
    """Create a small readable preview for common artifact types."""
    if value is None:
        return None

    if isinstance(value, pd.DataFrame):
        return value.head(10)

    if isinstance(value, dict):
        rows = []
        for key, item in list(value.items())[:12]:
            rows.append({"key": str(key), "value": str(item)[:200]})
        return pd.DataFrame(rows)

    if isinstance(value, (list, tuple, set)):
        rows = [{"value": str(item)[:200]} for item in list(value)[:12]]
        return pd.DataFrame(rows)

    return str(value)[:500]


def artifact_status(artifacts: dict):
    """Show which pickle files loaded successfully."""
    status_rows = []
    for label, file_name in ARTIFACT_FILES.items():
        file_path = ARTIFACTS_DIR / file_name
        loaded = artifacts.get(label) is not None
        status_rows.append(
            {
                "Artifact": label,
                "File": file_name,
                "Found": "Yes" if file_path.exists() else "No",
                "Loaded": "Yes" if loaded else "No",
            }
        )

    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)


def page_header(title: str, description: str):
    st.markdown(
        f"""
        <div class="hero">
            <div class="small-label">Delhivery Logistics Network Intelligence</div>
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_decision_panel(title: str, bullets: list[str], style: str = "callout"):
    """Render a compact business interpretation panel."""
    items = "".join(f"<li>{item}</li>" for item in bullets)
    st.markdown(
        f"""
        <div class="{style}">
            <strong>{title}</strong>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def executive_summary(artifacts: dict):
    page_header(
        "Executive Summary",
        "A compact operating view of shipment volume, network scale, and ETA model performance.",
    )

    show_kpi_cards()

    show_decision_panel(
        "Executive takeaways",
        [
            "Graph-enhanced ETA modeling reduced MAE from 161.5 minutes to 29.85 minutes.",
            "The analyzed network spans 1,657 facilities and 2,781 corridors.",
            "The project moves beyond prediction into hub, corridor, and intervention prioritization.",
        ],
    )

    col1, col2 = st.columns(2)
    with col1:
        show_plot(
            "phase5_strategy",
            "Business strategy summary for prioritizing interventions.",
        )
    with col2:
        show_plot(
            "delay_analysis",
            "Delay distribution and operational delay patterns.",
        )

    with st.expander("Artifact Load Status"):
        artifact_status(artifacts)


def eta_model_performance():
    page_header(
        "ETA Model Performance",
        "Comparison of baseline routing estimates, machine learning ETA predictions, and graph-enhanced features.",
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("OSRM Baseline MAE", "161.5 min")
    col2.metric("Random Forest MAE", "30.95 min")
    col3.metric("Graph RF MAE", "29.85 min", delta="-1.09 min vs RF")

    show_decision_panel(
        "Model story",
        [
            "The baseline routing estimate is useful operational context but weak as an ETA predictor.",
            "Random Forest captures most explainable structure in segment-level ETA.",
            "Graph features add incremental lift and make the model more operationally interpretable.",
        ],
    )

    col1, col2 = st.columns(2)
    with col1:
        show_plot(
            "phase4_graph_advantage",
            "Graph features improved ETA prediction accuracy.",
        )
    with col2:
        show_plot(
            "baseline_residuals",
            "Residual behavior of the baseline ETA model.",
        )

    show_plot(
        "temporal_explainability",
        "Temporal features explain time-window and scheduling effects in ETA predictions.",
    )


def network_bottlenecks():
    page_header(
        "Network Bottlenecks",
        "Facility-level network analysis highlights hubs that are central, congested, or delay-prone.",
    )

    show_plot(
        "network_bottleneck",
        "Network bottleneck ranking based on graph and operational signals.",
    )

    st.info(
        "Use these bottleneck hubs as candidates for staffing, process, dispatch, or capacity interventions."
    )
    show_decision_panel(
        "How to use this page",
        [
            "Start with high-centrality hubs where small delays can affect many downstream corridors.",
            "Prioritize hubs that combine bottleneck score, delay rate, and business volume.",
            "Use intervention simulations before proposing costly capacity changes.",
        ],
    )


def corridor_risk_ranking(artifacts: dict):
    page_header(
        "Corridor Risk Ranking",
        "Corridor-level risk scoring combines delay behavior, SLA breach tendency, volume, and graph context.",
    )

    show_plot(
        "corridor_risk_ranking",
        "Highest-risk corridors after filtering unreliable low-volume outliers.",
    )

    show_decision_panel(
        "Product analytics angle",
        [
            "Corridor ranking translates model output into a backlog of operational fixes.",
            "Volume filtering keeps the ranking from overreacting to one-off failures.",
            "This can support SLA monitoring, lane-level alerting, and partner performance reviews.",
        ],
        style="callout risk-callout",
    )

    preview = summarize_artifact(artifacts.get("Corridor risk results"))
    if isinstance(preview, pd.DataFrame):
        st.subheader("Loaded Artifact Preview")
        st.dataframe(preview, use_container_width=True, hide_index=True)


def delay_propagation(artifacts: dict):
    page_header(
        "Delay Propagation",
        "Propagation analysis separates hubs that create, amplify, or receive downstream delay.",
    )

    show_plot(
        "delay_propagation",
        "Delay propagation roles across the logistics network.",
    )

    show_decision_panel(
        "Network insight",
        [
            "Delay sources are good candidates for root-cause analysis.",
            "Delay amplifiers may need process controls because they spread disruption.",
            "Delay receivers help explain downstream customer impact.",
        ],
    )

    preview = summarize_artifact(artifacts.get("Delay propagation results"))
    if isinstance(preview, pd.DataFrame):
        st.subheader("Loaded Artifact Preview")
        st.dataframe(preview, use_container_width=True, hide_index=True)


def hub_intervention_simulator(artifacts: dict):
    page_header(
        "Hub Intervention Simulator",
        "Scenario view for estimating the impact of reducing delays at priority hubs.",
    )

    reduction = st.slider(
        "Delay reduction scenario",
        min_value=10,
        max_value=30,
        value=20,
        step=10,
        help="Matches the 10%, 20%, and 30% intervention scenarios from the analysis.",
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Scenario", f"{reduction}%")
    col2.metric("Target", "Top bottleneck hubs")
    col3.metric("Expected effect", "Lower ETA error and SLA breaches")

    show_decision_panel(
        "Simulator value",
        [
            "Frames analytics as a decision tool, not just reporting.",
            "Helps compare intervention intensity before committing operations resources.",
            "Connects model outcomes to SLA breach reduction and revenue recovery.",
        ],
    )

    show_plot(
        "hub_intervention_simulator",
        "Estimated value of hub-level delay reduction scenarios.",
    )

    preview = summarize_artifact(artifacts.get("Hub simulation results"))
    if isinstance(preview, pd.DataFrame):
        st.subheader("Loaded Artifact Preview")
        st.dataframe(preview, use_container_width=True, hide_index=True)


def methodology_and_limitations(artifacts: dict):
    page_header(
        "Methodology & Limitations",
        "A brief project map from raw shipment segments to decision-ready logistics intelligence.",
    )

    st.subheader("Methodology")
    st.markdown(
        """
        1. Cleaned shipment segment records and removed inconsistent data.
        2. Built baseline ETA and Random Forest ETA models.
        3. Constructed a facility-corridor graph using NetworkX.
        4. Added graph features such as centrality, bottleneck scores, and embeddings.
        5. Ranked corridors and hubs for operational intervention.
        6. Simulated delay reduction scenarios for business impact.
        """
    )

    st.subheader("Limitations")
    st.markdown(
        """
        - The dashboard is designed for presentation and does not retrain models.
        - It avoids loading the large raw CSV to keep the app deployable.
        - Results depend on the quality and completeness of the original shipment data.
        - Pickle artifacts are optional; static plots and hardcoded summary metrics keep the app available if they fail to load.
        """
    )

    with st.expander("Artifact Load Status"):
        artifact_status(artifacts)


def main():
    artifacts = get_artifacts()

    st.sidebar.title("Delhivery Intelligence")
    st.sidebar.caption("Logistics network analytics dashboard")
    apply_custom_styles()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Summary",
            "ETA Model Performance",
            "Network Bottlenecks",
            "Corridor Risk Ranking",
            "Delay Propagation",
            "Hub Intervention Simulator",
            "Methodology & Limitations",
        ],
    )

    st.sidebar.divider()
    st.sidebar.write("Data source")
    st.sidebar.caption("Uses PNG plots and optional pickle artifacts.")

    if page == "Executive Summary":
        executive_summary(artifacts)
    elif page == "ETA Model Performance":
        eta_model_performance()
    elif page == "Network Bottlenecks":
        network_bottlenecks()
    elif page == "Corridor Risk Ranking":
        corridor_risk_ranking(artifacts)
    elif page == "Delay Propagation":
        delay_propagation(artifacts)
    elif page == "Hub Intervention Simulator":
        hub_intervention_simulator(artifacts)
    else:
        methodology_and_limitations(artifacts)


if __name__ == "__main__":
    main()
