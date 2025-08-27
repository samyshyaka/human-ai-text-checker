# Human-AI Text Checker Frontend

This React frontend connects to your FastAPI backend with Llama API integration for human vs AI text detection.

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd server
uvicorn main:app --reload
```
The backend will run at `http://127.0.0.1:8000`

### 2. Start the Frontend
```bash
cd ui
npm start
```
The frontend will run at `http://localhost:3000`

## 🔗 Integration Features

### ✅ **Real AI Analysis**
- **No more mock data** - Uses actual Llama API responses
- **Real probabilities** - Gets exact AI vs Human percentages from Llama
- **Detailed reasoning** - Shows why the AI made its decision

### ✅ **Enhanced UI**
- **Loading states** - Shows when AI is analyzing text
- **Error handling** - Displays API errors gracefully
- **Analysis details** - Expandable view of AI reasoning and source

### ✅ **API Service**
- **Health checks** - Verify backend connectivity
- **Text analysis** - Send content to Llama API
- **Error handling** - Graceful fallbacks for network issues

## 🧪 Testing the Connection

1. **Backend Health Check**: Click "Test Health Endpoint" in the sidebar
2. **API Test**: Click "Test Simple Endpoint" to test Llama connectivity
3. **Create Post**: Use the Create button to analyze real text

## 📊 What You'll See

### **Before (Mock Data)**
- Random percentages (50-100% Human)
- No real analysis
- No AI reasoning

### **After (Real API)**
- Exact probabilities from Llama (e.g., 73% AI, 27% Human)
- Detailed AI reasoning
- Source tracking (API vs fallback)
- Real-time analysis

## 🔧 Troubleshooting

### **CORS Issues**
- Ensure backend has CORS middleware enabled
- Check that frontend is running on `localhost:3000`

### **Connection Failed**
- Verify backend is running on port 8000
- Check API key configuration in `.env` file
- Use the connection test in the sidebar

### **Analysis Not Working**
- Check backend logs for Llama API errors
- Verify your API key has access to the model
- Test with the `/debug/test-simple` endpoint

## 🎯 Next Steps

1. **Test the integration** with different text types
2. **Customize the UI** styling as needed
3. **Add more features** like batch analysis or history
4. **Deploy** both frontend and backend

## 📁 File Structure

```
ui/
├── src/
│   ├── services/
│   │   └── api.js          # API communication
│   ├── components/
│   │   ├── CreatePost.js   # Text input & analysis
│   │   ├── Post.js         # Display with AI results
│   │   ├── PostList.js     # List of posts
│   │   ├── Sidebar.js      # Navigation + connection test
│   │   └── ConnectionTest.js # Backend connectivity test
│   └── App.js              # Main app with real API integration
```

The integration is now complete! Your React frontend will use the real Llama API through your FastAPI backend to provide genuine AI vs Human text analysis. 🦙✨
