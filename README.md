# PropagandaLens

A multilingual propaganda and rhetorical manipulation detection tool.

## Features
- **Manipulation Detection**: Detects 8 rhetorical techniques (Fear Appeal, False Dilemma, Bandwagon, etc.).
- **Multilingual**: Supports English and Hindi (automatic translation to English for classification).
- **Temporal Timeline**: Analyzes manipulation evolution across multiple time periods.
- **Explainable AI Chat**: Question the findings directly via an interactive Groq-powered chat.
- **Export to PDF**: Detailed analysis reports.

## Prerequisites
- Python 3.10+
- Node.js 18+
- [Groq API Key](https://console.groq.com)

## Setup Backend

1. Navigate to `backend/` and install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Create `backend/.env` based on `.env.example`:
   ```bash
   GROQ_API_KEY=your_key_here
   ```
3. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```
   *(Note: The first run may take a few minutes as it downloads the Helsinki-NLP translation model sizes ~300MB).*

## Setup Frontend

1. Navigate to `frontend/` and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Run Vite dev server:
   ```bash
   npm run dev
   ```

## API Testing

You can quickly test the NLP core using curl:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "If you do not vote for us, the economy will collapse and your family will be in danger!"}'
```
