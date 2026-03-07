from fasthtml.common import *

app, rt = fast_app(
    hdrs=(Link(rel="stylesheet", href="/static/uno.css", type="text/css"),)
)


@rt("/")
def get():
    return Titled(
        "计数器示例",
        Div(
            H1("计数器", cls="text-3xl font-bold text-center my-8"),
            Div(
                Span("0", id="count", cls="text-5xl font-bold text-blue-600"),
                cls="text-center my-8",
            ),
            Div(
                Button(
                    "点击 +1",
                    hx_post="/increment",
                    hx_target="#count",
                    cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
                ),
                cls="flex justify-center gap-4 mt-4",
            ),
            cls="max-w-2xl mx-auto mt-16 p-8 bg-white rounded-lg shadow-lg",
        ),
        cls="bg-gray-100 min-h-screen",
    )


@rt("/increment", methods=["POST"])
def post(request):
    session = request.session
    count = session.get("count", 0) + 1
    session["count"] = count
    return Span(str(count), cls="text-5xl font-bold text-blue-600")


serve(port=5020)
