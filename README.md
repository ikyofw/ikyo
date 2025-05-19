<div style="padding-bottom: 20px;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/ikyo2.png" style="max-height: 100%; height: 120px; margin-bottom: 20px">
    <img alt="Ikyo" src="images/ikyo2.png" height="120px">
  </picture>
</div>
# Background
The main objective of this framework is to minimize development effort for typical web-based applications that do not require complex user interfaces. It provides only one standard UI style for efficiency. Originally developed in 2002 using Java and JavaScript, the framework was migrated to React and Django in 2022, resulting in the current version 2.0. As of December 2023, the framework has been open-sourced.

# Features
* Online web screen definition: Web screens can be directly defined within the framework.
* Preview functionality: Screen layouts can be previewed immediately after saving a screen definition although the nature of the process is not WYSIWYG.
* High-level object approach: Screens are defined using high-level objects like dialogues, enquiry fields, simple fields, tabular fields, button bars, etc., which we refer to as "field groups".
* Self-referential development: The framework itself is used to build the screens that define other screens.
* Excel import option: Screen definitions can alternatively be created using an Excel spreadsheet.
* Dynamic screen rendering: Once defined, the backend can submit the screen definition to the React frontend, which will then render the screen accordingly.
* Minimal React development: React development is generally not required unless a new type of field group is needed.
* Powerful tabular field group: This feature allows data input and display in a spreadsheet-like format, including navigation using cursor keys or mouse, and supports copy and paste functionalities.
* Integrated management: Menu, user, and permission management systems are already integrated into the framework.
* Sample applications: Three sample applications are provided: a timesheet, task management, and an expense tracking system.

# Notes
1. Python 3.10 or above.
2. Django 4.x.
3. React.
4. Django Rest Framework ([Official Website](https://www.django-rest-framework.org)).
5. Database: Postgresql.

# History
| Version | Date       | Author | Description    |
| ------- | ---------- | ------ | -------------- |
| 2.000   | 2023-12-13 | ikyo   | Initial release |

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
3. **Activate the Virtual Environment**: On Windows, use:
   ``.\.venv\Scripts\activate``
   Linux:  
   ``source ./.venv/bin/activate``
4. **Install Python Modules**: Ensure you have a `requirements.txt` file in your project directory. Install the required modules using the following command:
   ``pip install -r requirements.txt``
5. **Initialize database**:  
   ``python manage.py makemigrations sessions core``  
   ``python manage.py migrate``
6. **Start the Django Development Server**: Start the development server using the following command:  
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
2. **Installing Dependencies**  
   Install all dependencies required for the project:  
   ``npm install --force``
3. **Build the React App** 
   Compile and build your React application:  
   ``npm run build`` 
4. **Ensure the Django Templates Directory Exists**
   Create the necessary directory structure in your Django project (if it doesn't already exist):  
   Linux:  
    ``mkdir -p ../django_backend/templates/react``  
    Windows:  
   ``mkdir ..\django_backend\templates\react``  
   **Please clean this folder if it's not empty.**
5. **Move the contents of the Build Folder**  
   Move the contents of the build folder to the Django templates directory:  
   Linux:  
   ``move build/* ../django_backend/templates/react/``  
   Windows:  
   ``robocopy .\build\ ..\django_backend\templates\react\ /E /MOVE``  
   This step integrates the built React app with your Django project.
6. **Delete the Build Folder**
   Delete the empty build folder.  
   Linux:  
   ``rm build``  
   Windows:  
   ``rmdir build /S /Q``
7. **View the App in the Browser**  
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
cd react
npm start
``` 

# License
MIT


# Documentation
[Documentation](docs/doc.md)

# Reference
1. Django  
   https://www.djangoproject.com

2. Django REST framework    
   https://www.django-rest-framework.org

3. React  
   https://react.dev

4. React Spreadsheet (0.6.2)  
   https://iddan.github.io/react-spreadsheet
