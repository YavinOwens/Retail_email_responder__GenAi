import reflex as rx

config = rx.Config(
    app_name="Retail_email_responder__GenAi",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)