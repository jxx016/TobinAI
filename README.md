# TobinAI - Autonomous Property Repair Coordinator

TobinAI is an intelligent agent that helps landlords coordinate property repairs by automatically processing tenant repair requests and coordinating with service providers.

## Features

- 🤖 AI-powered repair request processing
- 💬 Natural language understanding of repair requests
- 📱 Web interface for tenants to submit requests
- 📱 SMS notifications for service providers
- 🔄 Automated repair coordination
- 📊 Repair request tracking and history

## Tech Stack

- **Frontend**: React + TypeScript
- **Backend**: Express.js + TypeScript
- **AI/ML**: LangChain, ChromaDB, Virtuals Protocol
- **Database**: PostgreSQL
- **Authentication**: JWT
- **Communication**: Twilio (SMS)

## Project Structure

```
tobin-ai/
├── frontend/           # React frontend application
├── backend/           # Express.js backend server
├── ai-agent/          # LangChain AI agent implementation
└── shared/            # Shared types and utilities
```

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- PostgreSQL
- Python 3.9+ (for AI components)
- Twilio Account (for SMS)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   # Install frontend dependencies
   cd frontend
   npm install

   # Install backend dependencies
   cd ../backend
   npm install

   # Install AI agent dependencies
   cd ../ai-agent
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env` in both frontend and backend directories
   - Fill in the required environment variables

4. Start the development servers:
   ```bash
   # Start backend
   cd backend
   npm run dev

   # Start frontend
   cd frontend
   npm run dev

   # Start AI agent
   cd ai-agent
   python main.py
   ```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/tobin_ai
JWT_SECRET=your_jwt_secret
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000
```

## License

MIT 