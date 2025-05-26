import streamlit as st
import os
from dotenv import load_dotenv
from core import ClientManager, ResearchEngine, ChatEngine
from config import (
    APP_TITLE,
    APP_CAPTION,
    WELCOME_MESSAGE,
    DEFAULT_RESEARCH_DEPTH,
    DEFAULT_TIME_LIMIT,
    DEFAULT_MAX_URLS,
)

# Load environment variables
load_dotenv()


# Initialize core components
@st.cache_resource
def get_core_components():
    """Initialize and return core application components."""
    try:
        client_manager = ClientManager()
        research_engine = ResearchEngine(client_manager)
        chat_engine = ChatEngine(client_manager, research_engine)
        return client_manager, research_engine, chat_engine
    except ValueError as e:
        st.error(f"Configuration error: {str(e)}")
        st.error("Please set your API keys in the environment variables or .env file")
        st.stop()


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Claude 4 Deep Research Assistant", page_icon="🔍", layout="wide"
    )

    # Initialize core components
    client_manager, research_engine, chat_engine = get_core_components()

    # Minimal CSS for footer only
    st.markdown(
        """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(240, 242, 246, 0.9);
        color: #262730;
        text-align: center;
        padding: 3px;
        font-size: 12px;
        z-index: 999;
        border-top: 1px solid #e6e9ef;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)

    # Sidebar with controls
    with st.sidebar:
        st.header("🛠️ Settings")

        # Research parameters
        st.subheader("Research Parameters")
        max_depth = st.slider(
            "Research Depth",
            1,
            10,
            DEFAULT_RESEARCH_DEPTH,
            help="Maximum number of research iterations",
        )
        time_limit = st.slider(
            "Time Limit (seconds)",
            30,
            300,
            DEFAULT_TIME_LIMIT,
            help="Maximum time for research",
        )
        max_urls = st.slider(
            "Max URLs",
            1,
            100,
            DEFAULT_MAX_URLS,
            help="Maximum number of URLs to analyze",
        )

        st.divider()

        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Instructions
        st.subheader("💡 How to Use")
        st.markdown(
            """
        1. **General Questions**: Ask any question for immediate responses
        2. **Deep Research**: Request research on topics for comprehensive analysis
        3. **Current Information**: Ask about recent events or developments
        
        **Example prompts:**
        - "Research the latest developments in quantum computing"
        - "What are the current trends in renewable energy?"
        - "Analyze the impact of AI on healthcare"
        """
        )

        # API Status
        st.subheader("🔧 API Status")
        api_status = client_manager.check_api_keys()
        anthropic_key = "✅ Connected" if api_status["anthropic"] else "❌ Missing"
        firecrawl_key = "✅ Connected" if api_status["firecrawl"] else "❌ Missing"
        st.write(f"Anthropic: {anthropic_key}")
        st.write(f"Firecrawl: {firecrawl_key}")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append(
            {"role": "assistant", "content": WELCOME_MESSAGE}
        )

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask me anything or request deep research on a topic...")

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare messages for Claude
        claude_messages = chat_engine.prepare_claude_messages(
            st.session_state.messages[:-1], st.session_state.messages[0]["content"]
        )
        # Add the current user message
        claude_messages.append({"role": "user", "content": user_input})

        # Show processing status
        with st.container():
            st.info("🤔 **Thinking...**")

            # Check if this might be a research request
            might_need_research = research_engine.is_research_request(user_input)

            if might_need_research:
                st.info(
                    "🔍 **This looks like a research request. I may use deep research tools...**"
                )

            # Clear status messages
            st.empty()

            # Stream the response using chat message
            with st.chat_message("assistant"):
                # Create placeholder for streaming response
                response_placeholder = st.empty()

                # Stream the response with official Anthropic streaming
                full_response = chat_engine.stream_text_response(
                    claude_messages,
                    [research_engine.get_tool_definition()],
                    response_placeholder,
                )

            # Add assistant response to session state
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

            # Rerun to update the display
            st.rerun()

    # Footer
    st.markdown(
        """
    <div class="footer">
        <p style="margin: 0;">🔍 Powered by Claude 4 & Firecrawl Deep Research | 
        <a href="https://docs.firecrawl.dev/features/alpha/deep-research" target="_blank">Learn more about Deep Research</a></p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
