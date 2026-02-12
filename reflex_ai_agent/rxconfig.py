import reflex as rx

config = rx.Config(
    app_name="reflex_ai_agent",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)