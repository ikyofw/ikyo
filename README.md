# ikyo
Python ikyo.

## Features
1. This framework was originally developed in 2002 using Java and JavaScript.
2. The main objective of this framework is to minimize the development effort for typical screens that do not require fancy user interfaces.
3. Only one standard UI style is provided.
4. In 2022, we migrated the framework to React and Django. This new version is numbered 2.0.
5. The backend submits the screen definition to the React frontend. The screen definition might consist of dialogues, enquiry fields, simple fields, tabular fields, button bars, etc. We call these "field groups." The frontend then renders the screen accordingly.
6. React development is usually not required unless a new type of field group is needed.
7. The tabular field group is a powerful feature in the framework. Data can be input and displayed in a tabular format. The UI is similar to a spreadsheet, allowing navigation in the table using cursor keys or the mouse. Copy and paste are also supported.
8. Menu management, user management, and permission management are already integrated.
9. Developers can define new pages or modify existing ones online and see the changes immediately after saving. These screens are also defined using the framework itself.
10. An option to define the screen in an Excel spreadsheet is also provided.
11. We have provided three sample applications: timesheet, task management, and expenses.
12. Database: SQLite3, Postgresql and all the other ones supported by Django.

## Notes
1. Python 3.10 or above.
2. Django 4.x.
3. React.
4. Django Rest Framework ([Official Website](https://www.django-rest-framework.org)).
5. Database: SQLite3.

## History
| Version | Date       | Author | Description    |
| ------- | ---------- | ------ | -------------- |
| 2.000   | 2023-12-05 | ikyo   | Initial release |
|  |  |  |  |

# Folder Structure
1. **django_backend**: Python Django backend folder.
2. **react**: React frontend folder.
3. **apps**: Demo apps folder.
4. README.md: Readme file.

# Python and Django Environment Setup

To set up your Python environment, follow these steps:

1. **Install Python 3.10.x**: Download and install Python 3.10.x from the official [Python website](https://www.python.org/downloads/).  
2. **Create a Virtual Environment**: Open a terminal in the project directory and first navigate to the backend folder:  
   ``cd django_backend``  
   Then create a virtual environment:    
   ``python -m venv .venv``
3. ***Activate the Virtual Environment**: On Windows, use:
   ``.\.venv\Scripts\activate``
   Linux:  
   ``source .\.venv\bin\activate``
4. **Install Python Modules**: Ensure you have a `requirements.txt` file in your project directory. Install the required modules using the following command:
   ``pip install -r requirements.txt``
5. **Start the Django Development Server**: Start the development server using the following command:   
   ``python manage.py runserver``

## Python Modules
| #  | Name                | Version | Description                                           |
| -- | ------------------- | ------- | ----------------------------------------------------- |
| 1  | django              | 4.x     |                                                       |
| 2  | django-cors-headers |         |                                                       |
| 3  | djangorestframework |         |                                                       |
| 4  | markdown            |         | Markdown support for the browsable API.               |
| 5  | django-filte        |         | Filtering support                                     |
| 6  | json5               |         | Convert non-standard JSON strings to JSON objects.    |
| 7  | pandas              |         | Process spreadsheets.                                 |
| 8  | openpyxl            |         | Process spreadsheets.                                 |
| 9  | pycryptodome        |         | Used for the login page.                              |

# Setting Up and Integrating React with Django

Follow these steps to set up and run your React application:

1. **Navigate to the React Directory**  
   Open a terminal and change to the React project directory:  
   ``cd react``
2. **Build the React App** 
   Compile and build your React application:  
   ``npm run build`` 
3. **Ensure the Django Templates Directory Exists**
   Create the necessary directory structure in your Django project (if it doesn't already exist):  
    ``mkdir -p ../django_backend/templates/react`` 
3. **Move the Build Folder**  
   Move the build folder to the Django templates directory:    
   ``move build ../django_backend/templates/react``  
   This step integrates the built React app with your Django project.
4. **View the App in the Browser**  
   After moving the build folder, you can view the app in the browser at http://localhost:8000.

For more information, please reference to *react/README.md* file.


# Debug django and react in Visual Studio Code
Please reference to *.vscode/launch.json* file.  
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [

        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}\\manage.py",
            "args": [
                "runserver",
                "0.0.0.0:8000"
            ],
            "django": true,
            "justMyCode": true
        },
        {
            "type": "pwa-msedge",
            "request": "launch",
            "name": "React",
            "url": "http://localhost:3000",
            "webRoot": "${workspaceFolder}"
        }
    ]
}
```

Start the react server:  
```shell
cd pyi-react
npm start
``` 

# License
MIT

# Reference
1. Django  
   https://www.djangoproject.com

2. Django REST framework    
   https://www.django-rest-framework.org

3. React  
   https://react.dev

4. React Spreadsheet (0.6.2)  
   https://iddan.github.io/react-spreadsheet
