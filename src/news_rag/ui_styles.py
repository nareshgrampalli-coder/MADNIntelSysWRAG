"""Shared Streamlit presentation styles for the News RAG application."""


def apply_styles(st) -> None:
    """Apply the shared Bootstrap-inspired visual system."""
    st.markdown(
        """
        <style>
        :root {
            --news-surface: #ffffff;
            --news-surface-muted: #f8f9fa;
            --news-border: #dee2e6;
            --news-text: #212529;
            --news-muted: #6c757d;
            --news-primary: #0d6efd;
            --news-success: #198754;
            --news-success-hover: #157347;
            --news-radius: 0.5rem;
            --news-spacing: 0.75rem;
            --news-body-size: 0.95rem;
            --news-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
        html, body, [class*="stApp"] {
            color: var(--news-text);
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: var(--news-body-size);
            line-height: 1.5;
        }
        h1, h2, h3 {
            letter-spacing: 0;
            font-weight: 650;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--news-border);
        }
        [data-testid="stMetric"] {
            padding: 0.75rem 1rem;
            border: 1px solid var(--news-border);
            border-radius: var(--news-radius);
            background: var(--news-surface-muted);
            box-shadow: var(--news-shadow);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: var(--news-spacing);
            border-radius: var(--news-radius);
            border-color: var(--news-border);
            background: var(--news-surface);
            box-shadow: var(--news-shadow);
        }
        [data-testid="stHorizontalBlock"] > div:has([data-testid="stVerticalBlockBorderWrapper"]) {
            display: flex;
        }
        [data-testid="stHorizontalBlock"] > div:has([data-testid="stVerticalBlockBorderWrapper"]) > div {
            flex: 1 1 auto;
        }
        [data-testid="stHorizontalBlock"] > div:has([data-testid="stVerticalBlockBorderWrapper"]) [data-testid="stVerticalBlockBorderWrapper"] {
            height: 100%;
            box-sizing: border-box;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--news-border);
            border-radius: var(--news-radius);
            background: var(--news-surface);
        }
        [data-testid="stExpander"] summary {
            font-weight: 600;
        }
        [data-testid="stButton"] button,
        [data-testid="stLinkButton"] a {
            min-height: 2.25rem;
            border-radius: var(--news-radius);
            font-weight: 600;
        }
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
            background: var(--news-success);
            border-color: var(--news-success);
            color: #fff;
        }
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
            background: var(--news-success-hover);
            border-color: var(--news-success-hover);
            color: #fff;
        }
        .news-ingestion-status {
            display: block;
            font-weight: 700;
            margin: 0.25rem 0 0.5rem;
        }
        .news-ingestion-status.is-complete { color: var(--news-success); }
        .news-ingestion-status.is-required { color: #dc3545; }
        [data-testid="stChatInput"]:has(textarea:disabled) {
            position: relative;
        }
        [data-testid="stChatInput"]:has(textarea:disabled):hover::after {
            content: "Click Run ingestion to load news before asking a question.";
            position: absolute;
            left: 0;
            bottom: calc(100% + 0.4rem);
            z-index: 10;
            max-width: min(22rem, 90vw);
            padding: 0.45rem 0.65rem;
            border: 1px solid var(--news-border);
            border-radius: var(--news-radius);
            background: var(--news-text);
            color: #fff;
            font-size: 0.8rem;
            pointer-events: none;
            white-space: normal;
        }
        [data-testid="stDialog"] [role="dialog"] {
            border: 1px solid var(--news-border);
            border-radius: var(--news-radius);
            box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.15);
        }
        [data-testid="stCaptionContainer"] {
            color: var(--news-muted);
        }
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
                gap: 0.75rem;
            }
            [data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            [data-testid="stChatInput"]:has(textarea:disabled):hover::after {
                max-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
