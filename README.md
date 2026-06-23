# CrisisNet

**⚠️ Research Prototype — Not a real crisis service. For demonstration purposes only, using synthetic test data.**

CrisisNet is a capstone/portfolio project demonstrating a multi-agent crisis-triage architecture using LangGraph. It is **not** a deployed service, and is **not validated for real-world crisis use**. All data processed by this system must be synthetic.

## Overview
CrisisNet is a real-time crisis triage platform that processes incoming text messages, classifies severity, routes cases appropriately, escalates critical cases to humans, logs outcomes, and continuously improves classification performance through feedback.

## Setup Instructions

1. Clone the repository.
2. Create a `.env` file in the `backend` directory with your Groq and Gemini API keys:
   ```env
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   ```
3. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend dashboard at `http://localhost:3000`.

## Architecture
- **Frontend**: Next.js 15, TailwindCSS, React.
- **Backend**: FastAPI, PostgreSQL, Redis, LangGraph.
