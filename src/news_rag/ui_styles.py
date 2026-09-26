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
            --news-radius: 0.5rem;
            --news-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
        html, body, [class*="stApp"] {
            color: var(--news-text);
            font-family: "Segoe UI", Arial, sans-serif;
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
            min-height: 170px;
            padding: 0.85rem;
            border-radius: var(--news-radius);
            border-color: var(--news-border);
            background: var(--news-surface);
            box-shadow: var(--news-shadow);
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
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
