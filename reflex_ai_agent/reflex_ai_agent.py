"""
Retail_email_responder__GenAi – Production Clean Layout
Ollama-powered chatbot with:
- Left sidebar (source toggles)
- Center chat window (scrollable)
- Right sidebar (active citations)
"""

import os
import re
from pathlib import Path
from typing import Dict, List

import reflex as rx
from dotenv import load_dotenv
from ollama import Client


# ----------------------------------------------------------------------
# 1️⃣ Environment Configuration
# ----------------------------------------------------------------------
load_dotenv()

OLLAMA_API_KEY = os.getenv("ollama_api_key")
OLLAMA_URL = os.getenv("ollama_url", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")


# ----------------------------------------------------------------------
# 2️⃣ Ollama Client
# ----------------------------------------------------------------------
def create_ollama_client():
    if OLLAMA_API_KEY:
        return Client(
            host=OLLAMA_URL,
            headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
        )
    return Client(host=OLLAMA_URL)


ollama_client = create_ollama_client()


# ----------------------------------------------------------------------
# 3️⃣ Source Handling
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "sources"

SOURCE_FILES: Dict[str, Path] = {
    "Wikipedia": SOURCE_DIR / "wikipedia.txt",
    "Company Docs": SOURCE_DIR / "company_docs.txt",
    "News Articles": SOURCE_DIR / "news.txt",
}


def read_source(name: str) -> str:
    path = SOURCE_FILES.get(name)
    if path and path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def build_context(active_sources: List[str]) -> str:
    parts = []
    for src in active_sources:
        text = read_source(src)
        if text.strip():
            parts.append(f"### Source: {src}\n{text}")
    return "\n\n".join(parts)


def extract_citations(text: str) -> List[str]:
    raw = re.findall(r"\[(.*?)\]", text)
    labels = []

    for item in raw:
        labels.extend([x.strip() for x in item.split(",") if x.strip()])

    return list(dict.fromkeys(labels))


def call_ollama(user_msg: str, context: str) -> str:
    system_prompt = (
        "You are a helpful assistant. Use only the provided sources. "
        "Cite sources in square brackets, e.g. [Wikipedia]."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({"role": "system", "content": context})

    messages.append({"role": "user", "content": user_msg})

    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return f"❗ Error generating response: {e}"


# ----------------------------------------------------------------------
# 4️⃣ State Management
# ----------------------------------------------------------------------
class ChatState(rx.State):

    user_input: str = ""
    messages: List[Dict[str, str]] = [
        {
            "role": "assistant",
            "content": "👋 Hello! Ask me something and I’ll answer using the enabled sources."
        }
    ]

    citations: List[str] = []
    citation_filter: str = ""

    wiki_enabled: bool = True
    docs_enabled: bool = True
    news_enabled: bool = True

    # -------------------------
    # Computed properties
    # -------------------------
    @rx.var
    def filtered_citations(self) -> List[str]:
        f = self.citation_filter.lower()
        return [c for c in self.citations if f in c.lower()]

    @rx.var
    def has_citations(self) -> bool:
        return len(self.citations) > 0

    # -------------------------
    # Chat logic
    # -------------------------
    def send_message(self):
        user_msg = self.user_input.strip()
        if not user_msg:
            return

        self.messages.append({"role": "user", "content": user_msg})

        active = []
        if self.wiki_enabled:
            active.append("Wikipedia")
        if self.docs_enabled:
            active.append("Company Docs")
        if self.news_enabled:
            active.append("News Articles")

        context = build_context(active)

        assistant_reply = call_ollama(user_msg, context)

        self.citations = extract_citations(assistant_reply)
        self.messages.append({"role": "assistant", "content": assistant_reply})

        self.user_input = ""

    # ------------------------------------------------------------------
    # UI Components
    # ------------------------------------------------------------------

    @staticmethod
    def left_sidebar():
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.badge("📚", color_scheme="blue"),
                    rx.heading("Knowledge Chat", size="5"),
                ),

                rx.divider(),

                rx.text("Sources", font_weight="bold"),

                rx.checkbox(
                    "Wikipedia",
                    is_checked=ChatState.wiki_enabled,
                    on_change=ChatState.set_wiki_enabled,
                ),
                rx.checkbox(
                    "Company Docs",
                    is_checked=ChatState.docs_enabled,
                    on_change=ChatState.set_docs_enabled,
                ),
                rx.checkbox(
                    "News Articles",
                    is_checked=ChatState.news_enabled,
                    on_change=ChatState.set_news_enabled,
                ),

                spacing="4",
                align_items="flex-start",
            ),
            width="260px",
            height="100%",
            padding="1.5rem",
            border_right="1px solid #e5e5e5",
            bg="white",
        )

    @staticmethod
    def chat_window():
        return rx.box(
            rx.vstack(
                rx.box(
                    rx.foreach(
                        ChatState.messages,
                        lambda msg: rx.box(
                            rx.text(msg["content"], white_space="pre-wrap"),
                            bg=rx.cond(
                                msg["role"] == "assistant",
                                "#e8f0ff",
                                "#0066cc",
                            ),
                            color=rx.cond(
                                msg["role"] == "assistant",
                                "black",
                                "white",
                            ),
                            padding="1rem",
                            border_radius="0.75rem",
                            max_width="75%",
                            align_self=rx.cond(
                                msg["role"] == "assistant",
                                "flex-start",
                                "flex-end",
                            ),
                            mb="1rem",
                        ),
                    ),
                    flex="1",
                    width="100%",
                    overflow_y="auto",
                    padding="1.5rem",
                ),

                rx.hstack(
                    rx.text_area(
                        placeholder="Ask a question...",
                        value=ChatState.user_input,
                        on_change=ChatState.set_user_input,
                        flex="1",
                    ),
                    rx.button(
                        "Send",
                        on_click=ChatState.send_message,
                        color_scheme="blue",
                    ),
                    width="100%",
                    padding="1rem",
                    border_top="1px solid #e5e5e5",
                ),

                height="100%",
                width="100%",
                spacing="0",
            ),
            flex="1",
            height="100%",
            bg="#f5f7fa",
        )

    @staticmethod
    def right_sidebar():
        return rx.box(
            rx.vstack(
                rx.heading("Active Citations", size="5"),

                rx.input(
                    placeholder="Filter citations...",
                    value=ChatState.citation_filter,
                    on_change=ChatState.set_citation_filter,
                ),

                rx.cond(
                    ChatState.has_citations,
                    rx.foreach(
                        ChatState.filtered_citations,
                        lambda cite: rx.box(
                            rx.text(cite, font_weight="bold"),
                            padding="0.75rem",
                            border="1px solid #d0d7de",
                            border_radius="0.5rem",
                            width="100%",
                        ),
                    ),
                ),

                rx.cond(
                    ChatState.has_citations == False,
                    rx.text("No citations yet."),
                ),

                spacing="4",
                align_items="flex-start",
            ),
            width="300px",
            height="100%",
            padding="1.5rem",
            border_left="1px solid #e5e5e5",
            bg="white",
            overflow_y="auto",
        )

    @staticmethod
    def index():
        return rx.box(
            ChatState.left_sidebar(),
            ChatState.chat_window(),
            ChatState.right_sidebar(),
            display="flex",
            height="100vh",
            width="100%",
        )


# ----------------------------------------------------------------------
# 5️⃣ App Registration
# ----------------------------------------------------------------------
app = rx.App()
app.add_page(ChatState.index)


# ----------------------------------------------------------------------
# 6️⃣ Run
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.compile()
    app.run()
