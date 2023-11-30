# Getting Started

These instructions will get you a copy of the project up and running on your local machine for testing and use.

## 1. Prerequisites

* **Node.js and npm**: Before starting, you need to have Node.js installed, which includes npm (Node Package Manager), a tool to manage front-end dependencies.
  * Check Node.js and npm installation: After installing, you can check the installation by running `node -v` and `npm -v` in the command line to ensure that Node.js and npm are correctly installed.
  * Download Node.js from [here](https://nodejs.org/en) and follow the installation instructions.

* **Visual Studio Code (VSCode)**: For editing and managing your project, it's recommended to install Visual Studio Code, a popular code editor.
  * Download VSCode from [here](https://code.visualstudio.com/download) and follow the installation instructions.

## 2. Installing Dependencies

* **Navigate to the Project Root**: Open a command line tool and navigate to the project's root directory, where the package.json file is located.

* **Install Dependencies**: Install all dependencies required for the project    using below command: 

  ``npm install --force``

  This step will create a node_modules directory based on the dependencies listed in package.json

## 3. Running the Development Server

* **Start the Server**: In the project root directory using below command:

  ``npm start``

  This will start a local development server.

* **Access the App**: By default, the application usually opens automatically in the browser, or you can manually visit http://localhost:3000.

## 4. Browsing and Testing the Application

* **Explore the App**: The application should now be running in the browser. You can start exploring and testing the app's functionalities.

* **Running Tests**: If you need to run tests, using below command:

  ``npm test``

## 5. Building for Production (If Deploying)

* **Build the App**: Using below command build the app for production:

  ``npm run build``

  This typically creates a build directory containing all optimized static files.

