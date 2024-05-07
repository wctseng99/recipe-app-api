# Recipe App API

This repository hosts the source code for the Recipe App API, a project aimed at providing a RESTful interface for managing culinary recipes. The API allows users to create, retrieve, update, and delete recipes.

## Technologies Used
- **Git & GitHub**: For version control and source code management.
- **GitHub Actions**: Implements CI/CD to automate tests and deployments.
- **Python & Django**: The backend framework used for creating robust APIs.
- **Django REST Framework**: Provides tools for building Web APIs on top of Django.
- **Docker**: Used for containerizing the application to ensure consistency across different development and production environments.
- **PostgreSQL**: The database system chosen for reliable storage of recipe data.
- **Unit Tests (TDD)**: Test-Driven Development approach to ensure code quality and functionality.

## API Documentation

### Base URL
The API is currently being hosted on AWS EC2 and can be accessed via:
http://ec2-54-205-55-214.compute-1.amazonaws.com/api/docs/

### Endpoints

#### Ingredients
| Method   | Endpoint                                  | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| `GET`    | `/api/recipe/ingredients/`                | Retrieves a list of all ingredients.             |
| `PUT`    | `/api/recipe/ingredients/{id}/`           | Updates an existing ingredient.                  |
| `PATCH`  | `/api/recipe/ingredients/{id}/`           | Partially updates an existing ingredient.        |
| `DELETE` | `/api/recipe/ingredients/{id}/`           | Deletes a specific ingredient.                   |

#### Recipes
| Method   | Endpoint                                  | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| `GET`    | `/api/recipe/recipes/`                    | Retrieves a list of all recipes.                 |
| `POST`   | `/api/recipe/recipes/`                    | Creates a new recipe.                            |
| `GET`    | `/api/recipe/recipes/{id}/`               | Retrieves detailed information about a recipe.   |
| `PUT`    | `/api/recipe/recipes/{id}/`               | Updates a specific recipe.                       |
| `PATCH`  | `/api/recipe/recipes/{id}/`               | Partially updates a specific recipe.             |
| `DELETE` | `/api/recipe/recipes/{id}/`               | Deletes a specific recipe.                       |
| `POST`   | `/api/recipe/recipes/{id}/upload-image/`  | Uploads an image for a specific recipe.          |

#### Tags
| Method   | Endpoint                                  | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| `GET`    | `/api/recipe/tags/`                       | Retrieves a list of all tags.                    |
| `PUT`    | `/api/recipe/tags/{id}/`                  | Updates a specific tag.                          |
| `PATCH`  | `/api/recipe/tags/{id}/`                  | Partially updates a specific tag.                |
| `DELETE` | `/api/recipe/tags/{id}/`                  | Deletes a specific tag.                          |

#### Schema
| Method   | Endpoint                                  | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| `GET`    | `/api/schema/`                            | Retrieves the API schema.                        |

#### User Management
| Method   | Endpoint                                  | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| `POST`   | `/api/user/create/`                       | Registers a new user.                            |
| `GET`    | `/api/user/me/`                           | Retrieves the current user's profile information.|
| `PUT`    | `/api/user/me/`                           | Updates the current user's profile information.  |
| `PATCH`  | `/api/user/me/`                           | Partially updates the current user's profile.    |
| `POST`   | `/api/user/token/`                        | Generates a new authentication token.            |

## Development

### Setup

To set up a local development environment:
1. Clone the repository.
   ```bash
    git clone https://github.com/wctseng99/recipe-app-api.git
    cd recipe-app-api
    ```
2. Ensure Docker is installed and running on your machine.
3. Build the Docker container with:
    ```bash
    docker-compose build
    ```
4. Run the container with:
    ```bash
    docker-compose up
    ```
5. The API should now be accessible at:
    - `http://localhost:8000/api/docs/` : for the API documentation.
    - `http://localhost:8000/admin/` : for the Django admin interface.

### Testing
To run the tests, execute the following command:
```bash
docker-compose run --rm app sh -c "python manage.py test && flake8"
```
### Acknowledgements
This project is instructed by the course "Build a Backend REST API with Python & Django - Advanced".