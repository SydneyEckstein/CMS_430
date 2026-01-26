# Wikipedia Chain Finder

A web application that finds the shortest path between two Wikipedia articles using bidirectional iterative deepening search.

## Project Structure

```
project/
├── backend/
│   ├── app.py              # Flask application and API endpoint
│   ├── wikipedia_client.py # Wikipedia API interaction
│   ├── search.py           # BIDS algorithm implementation
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── style.css           # Styling
│   └── script.js           # JavaScript logic
├── specs.md                # Project specification
├── plan.md                 # Implementation plan
└── README.md               # This file
```

## Setup

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open http://localhost:5000 in your browser.

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns: `{"status": "ok"}`

### Find Path
- **POST** `/api/find-path`
- Request body:
  ```json
  {
    "start": "Article_Title",
    "end": "Article_Title"
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "path": ["Article1", "Article2", "Article3"],
    "depth": 2,
    "pages_explored": 150
  }
  ```

## Development Status

- [x] Phase 1: Project Setup
- [ ] Phase 2: Wikipedia Client
- [ ] Phase 3: Search Algorithm
- [ ] Phase 4: Flask Backend API
- [ ] Phase 5: Frontend
- [ ] Phase 6: Integration
- [ ] Phase 7: End-to-End Testing
- [ ] Phase 8: Polish and Documentation
