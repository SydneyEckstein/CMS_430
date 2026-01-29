# Wikipedia Chain Finder - Development Guide

## Project Summary
Build a web application that finds the shortest path between two Wikipedia articles using bidirectional iterative deepening search (BIDS). Simple frontend (HTML/CSS/vanilla JS) with Python Flask backend that queries Wikipedia API dynamically. Max chain length: 7 articles (depth 3 per direction). No caching, single-threaded, 30-60 second search time acceptable.

## Core Requirements

### Technology Stack
- **Frontend**: HTML, CSS, vanilla JavaScript
- **Backend**: Python Flask
- **External API**: Wikimedia REST API or MediaWiki Action API
- **Dependencies**: Flask, requests

### Algorithm: Bidirectional Iterative Deepening Search
1. Initialize two searches: forward (from start) and backward (from end)
2. Strictly alternate expansions: expand forward → check intersection → expand backward → check intersection
3. Increase depth after both directions explored (depth 0, 1, 2, 3)
4. Maximum depth: 3 per direction (total chain ≤ 7 articles)
5. Stop and return "No path exists within depth limit" if max depth exceeded

**Key data structures**:
- `forward_visited`: dict mapping page → parent
- `backward_visited`: dict mapping page → parent  
- `forward_frontier`: set of pages at current depth
- `backward_frontier`: set of pages at current depth

## Architecture

### Design Aesthetic (Claude-inspired)
- Font: System font stack ("Inter", "SF Pro", "Segoe UI")
- Colors: Background #F5F5F4, Text #2C2C2C, Accents warm brown/copper, Borders #E5E5E5
- Layout: Centered, generous whitespace, minimal

### Key Components
- **Backend**: Flask API endpoint, Wikipedia client module, BIDS search implementation
- **Frontend**: Two input fields, submit button, loading spinner, results display with clickable Wikipedia links
- **Wikipedia filtering**: Only namespace 0 links; exclude Special:*, User:*, Wikipedia:*, Talk pages, File:*, Image:*, Category:*, Template:*

## Coding Standards

### Python Backend
- Use type hints where appropriate
- Handle all API errors gracefully
- Validate inputs before processing
- Return consistent JSON responses
- Log important events (search start, completion, errors)

### JavaScript Frontend
- Use modern ES6+ syntax
- Async/await for API calls
- Clear variable names
- Separate concerns (DOM manipulation, API calls, validation)
- Handle all promise rejections

### General
- Clear function and variable names
- Comments for complex logic (especially BIDS algorithm)
- Error handling at all boundaries (API calls, user input, edge cases)
- DRY principle: don't repeat code

### Common Pitfalls to Avoid
- Not handling Wikipedia redirects
- Including non-article namespace links
- Not checking intersection after EACH expansion
- Duplicating meeting point in reconstructed path
- Forgetting title normalization before API calls
- Missing start==end edge case