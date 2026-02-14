# Quick Start Guide

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

## Installation & Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```
   
   The app will be available at `http://localhost:5173`

3. **Open Your Browser**
   - Navigate to `http://localhost:5173`
   - You'll be redirected to the Catalog page

## Navigation

The application has 5 main sections accessible from the left sidebar:

1. **Catalog** - Browse commands, jobs, workflows, and datasets
2. **Reasoning Logs** - View live agent reasoning stream
3. **Execution Panel** - Interactive chatbot for command execution
4. **IBM Agent** - z/OS agent dashboard
5. **Unisys Agent** - MCP agent dashboard

## Key Features to Try

### 1. Browse Commands
- Go to Catalog → Commands
- Use the search bar to filter commands
- Click on output files to view (JSON/TEXT) or download (FILE)
- Sort columns by clicking on column headers

### 2. Live Reasoning Logs
- Navigate to "Reasoning Logs"
- Watch live agent reasoning stream
- Use Pause/Resume to control the stream
- Clear logs when needed

### 3. Chat with Agent
- Go to "Execution Panel"
- Type a query like "Show me all active jobs on ZPROD01"
- View the natural language response
- Check the "Latest Output" panel for structured data

### 4. Agent Dashboards
- Visit IBM Agent or Unisys Agent pages
- View agent status, capabilities, and configuration
- Browse recent execution history

## Mock Data

All data is currently mocked for development. You'll see:
- 5 sample commands
- 3 sample jobs
- 2 sample workflows
- 3 sample datasets
- Simulated agent statuses
- Mock execution history

## Backend Integration

To connect to your backend:

1. Open `src/services/api.ts`
2. Find the function you want to integrate (e.g., `fetchCommandsCatalog`)
3. Uncomment the backend call code
4. Comment out or remove the mock implementation
5. Update the endpoint URLs to match your backend

Example:
```typescript
export const fetchCommandsCatalog = async (): Promise<Command[]> => {
  // Uncomment this:
  const response = await fetch('/api/catalog/commands');
  return await response.json();
  
  // Remove this:
  // return new Promise((resolve) => {
  //   setTimeout(() => resolve(mockCommands), 500);
  // });
};
```

## Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

The production build will be in the `dist/` directory.

## Troubleshooting

### Port Already in Use
If port 5173 is already in use, Vite will automatically try the next available port (5174, 5175, etc.).

### Dependencies Not Installing
Try clearing npm cache:
```bash
npm cache clean --force
npm install
```

### TypeScript Errors
Make sure you're using Node.js 18+ and TypeScript 5+:
```bash
node --version
npx tsc --version
```

## Next Steps

1. Review the full README.md for detailed documentation
2. Explore the code structure in `src/`
3. Check out the component library in `src/components/common/`
4. Start integrating your backend endpoints
5. Customize the color scheme in `tailwind.config.js`

## Need Help?

- Check the comprehensive README.md
- Review type definitions in `src/types/index.ts`
- Look at mock data in `src/services/mockData.ts`
- Examine component examples in `src/components/`

Happy coding! 🚀
