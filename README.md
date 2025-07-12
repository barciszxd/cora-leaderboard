# Flask API

A simple Flask API with a GET endpoint that returns a JSON response.

## Setup

1. Install Python (if not already installed)
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the API

To start the Flask API server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Endpoints

### GET /
- **Description**: Returns a simple JSON response
- **Response**: 
  ```json
  {
    "response": "Hello workd"
  }
  ```

### GET /health
- **Description**: Health check endpoint
- **Response**:
  ```json
  {
    "status": "healthy",
    "message": "Flask API is running successfully"
  }
  ```

## Testing

You can test the API using:

1. **Browser**: Navigate to `http://localhost:5000`
2. **curl**: 
   ```bash
   curl http://localhost:5000
   ```
3. **Postman**: Create a GET request to `http://localhost:5000`
