# JSON to Swagger

A FastAPI-based web application for uploading, storing, and serving OpenAPI specifications (JSON or YAML) with dynamic Swagger UI documentation. The project supports persistent storage using SQLite and provides Docker support for easy deployment.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Installation Instructions](#installation-instructions)
- [Usage Guidelines](#usage-guidelines)
- [Features and Functionalities](#features-and-functionalities)
- [Dependencies](#dependencies)
- [Configuration Options](#configuration-options)
- [Contribution Guidelines](#contribution-guidelines)
- [Troubleshooting Tips](#troubleshooting-tips)
- [License Information](#license-information)

---

## Project Overview

**JSON to Swagger** enables users to upload OpenAPI specifications in either JSON or YAML format, stores them in a local SQLite database, and serves each spec with a dedicated Swagger UI route. This streamlines API documentation management and sharing for teams and projects.

---

## Installation Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/newpaw/json_to_swagger.git
cd json_to_swagger
```

### 2. Install Dependencies

#### Using Poetry (Recommended)

```bash
poetry install
```

#### Using pip

```bash
pip install -r requirements.txt
```

### 3. (Optional) Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## Usage Guidelines

### 1. Run the Application

#### Using Poetry

```bash
poetry run uvicorn main:app --reload
```

#### Using pip

```bash
uvicorn main:app --reload
```

#### Using Docker

```bash
docker build -t jsonORyaml-to-swagger .
docker run -p 8000:8000 json-to-swagger
```

### 2. Upload OpenAPI Specs

- Access the upload endpoint (e.g., `POST /upload`) via Swagger UI or API client.
- Upload your OpenAPI spec file in JSON or YAML format.

### 3. Access Swagger UI Documentation

- After uploading, each spec is available at a unique Swagger UI route (e.g., `/docs/{spec_id}`).
- Visit `http://localhost:8000/docs/{spec_id}` in your browser to view the documentation.

---

## Features and Functionalities

- **Upload OpenAPI Specs:** Supports both JSON and YAML formats.
- **Persistent Storage:** All specs are stored in a local SQLite database.
- **Dynamic Swagger UI:** Each uploaded spec is served at a unique Swagger UI route.
- **Docker Support:** Easily build and run the application in a container.
- **Simple REST API:** FastAPI-powered endpoints for uploading and managing specs.

---

## Dependencies

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework for building APIs.
- [Uvicorn](https://www.uvicorn.org/) - ASGI server for running FastAPI apps.
- [PyYAML](https://pyyaml.org/) - YAML parsing for OpenAPI specs.
- [SQLite](https://www.sqlite.org/) - Lightweight database for persistent storage.

Other dependencies may be listed in `pyproject.toml` or `requirements.txt`.

---

## Configuration Options

- **Database Path:**  
  Set the path to the SQLite database using the `DATABASE_URL` environment variable.  
  Example:
  ```bash
  export DATABASE_URL=sqlite:///./openapi_specs.db
  ```

- **Port and Host:**  
  Configure Uvicorn with `--host` and `--port` options as needed.

---

## Contribution Guidelines

1. Fork the repository and create your feature branch (`git checkout -b feature/your-feature`).
2. Commit your changes (`git commit -am 'Add new feature'`).
3. Push to the branch (`git push origin feature/your-feature`).
4. Open a pull request describing your changes.

Please ensure your code follows the existing style and includes appropriate tests and documentation.

---

## Troubleshooting Tips

- **App won't start:**  
  Ensure all dependencies are installed and the correct Python version is used.

- **Database errors:**  
  Check that the `DATABASE_URL` is set correctly and the SQLite file is accessible.

- **Spec not appearing in Swagger UI:**  
  Confirm the spec was uploaded successfully and the correct route is used.

- **Docker issues:**  
  Make sure Docker is running and ports are not in use.

---

## License Information

This project is licensed under the [MIT License](LICENSE).

---