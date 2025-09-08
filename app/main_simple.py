from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# Проверяем, что папка templates существует
templates_dir = "app/templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Простой тест</title>
    </head>
    <body>
        <h1>Сервер работает!</h1>
        <p>Если вы видите эту страницу, значит FastAPI работает корректно.</p>
        <a href="/test">Тест шаблона</a>
    </body>
    </html>
    """

@app.get("/test", response_class=HTMLResponse)
async def test_template(request: Request):
    return templates.TemplateResponse("test.html", {
        "request": request,
        "message": "Шаблон работает!"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)