## Git Clone

Url: <ssh://git@192.168.1.252:12215/ikyo2>

## Python and Django environment setup

Open folder ikyo2 in vscode. Input in backend terminal:

  *         cd django_backend
        python -m venv .venv
        .\.venv\Scripts\activate
        source .\.venv\bin\activate
        pip install -r requirements.txt
        python manage.py makemigrations core sessions
        python manage.py migrate
        python manage.py runserver
    

## Setting Up and Integrating React with Django

Input in a new terminal as front-end terminal:

  *         cd react
        npm install --force
        npm run build
        mkdir -p ../django_backend/templates/react
        move build\* ../django_backend/templates/react/
    

## Restart Backend

Input in backend terminal:

  *         python manage.py runserver
    

Open <http://localhost:8000/>

