# streamlit_app/__init__.py

"""
Streamlit Health Chat Application package.

Expose main entry-point and sub-modules.
"""

__version__ = "0.1.0"

# Optional: import top-level application function
from .main import main  # si vous souhaitez lancer via `streamlit run -m streamlit_app`

# Expose utilities for convenience
# from .utils.history       import load_history, save_history
# from .utils.llm_api       import get_llm_response
# from .utils.rag_utils     import init_collection, get_rag_context, get_rag_context_adaptatif
# from .utils.viz           import get_graph_data, generate_graph_filename
# from .utils.pdf_generator import make_report_pdf
