from fastapi.templating import Jinja2Templates

# Esta es la instancia única de templates para toda la app
templates = Jinja2Templates(directory="app/templates")