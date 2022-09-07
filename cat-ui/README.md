# CAT UI

The configuration front end for the CAT chatbot generator using [Angular](https://angular.io).
The REST API is powered by a [Flask](https://palletsprojects.com/p/flask/) backend

## Setup

- [Node.js](https://nodejs.org/en/) and the built-in package manager [npm](https://npmjs.com)
- The required node modules in `package.json`. Run `npm install` in this directory
- Install typescript in dev mode if not already on your system to compile the sources `npm install typescript --save-dev`
- Python 3 and the dependencies found in the root directory (refer to [README](../README.md))
- The npm modules and python dependencies will be installed with the `setup.sh` [script](../setup.sh) in the root project

## Usage
- To run the frontend start the backend server first `python backend/common/server.py`
- Serve webapp locally using `npx ng serve`
