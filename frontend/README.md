# Mainframe Command & Agent Platform

A production-ready, multi-page React frontend for an AI-driven Mainframe Command & Agent Platform with a distinctive retro-futuristic terminal aesthetic.

## 🎨 Design Philosophy

This application features a **retro-futuristic terminal aesthetic** combining:
- Modern glassmorphism and depth
- Terminal-inspired color scheme (CRT-style amber/green but modernized)
- Clean, functional layouts with unexpected visual details
- Dark theme with neon accents (#00ff88 accent, #00d4ff blue, #ffb000 amber)
- Grid patterns and scan line effects
- Monospace typography with JetBrains Mono

## 🏗️ Tech Stack

- **Framework:** React 18 + TypeScript
- **Routing:** React Router v6
- **Styling:** Tailwind CSS + Custom CSS
- **UI Components:** Headless UI for accessible components
- **Icons:** Heroicons
- **Animations:** Framer Motion
- **Build Tool:** Vite

## 📁 Project Structure

```
mainframe-ui/
├── src/
│   ├── components/
│   │   ├── common/           # Reusable components
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── Modal.tsx
│   │   ├── catalog/          # Catalog-specific components
│   │   ├── agents/           # Agent-specific components
│   │   ├── logs/             # Log viewer components
│   │   └── chat/             # Chat interface components
│   ├── pages/
│   │   ├── CatalogPage.tsx          # Main catalog dashboard
│   │   ├── CommandsPage.tsx         # Commands list
│   │   ├── JobsPage.tsx             # Jobs list
│   │   ├── WorkflowsPage.tsx        # Workflows list
│   │   ├── DatasetsPage.tsx         # Datasets list
│   │   ├── ReasoningLogsPage.tsx    # Live reasoning stream
│   │   ├── ExecutionPage.tsx        # Chatbot interface
│   │   ├── IBMAgentPage.tsx         # IBM z/OS agent dashboard
│   │   └── UnisysAgentPage.tsx      # Unisys MCP agent dashboard
│   ├── services/
│   │   ├── api.ts            # API service layer (STUBBED)
│   │   └── mockData.ts       # Mock data for development
│   ├── types/
│   │   └── index.ts          # TypeScript type definitions
│   ├── styles/
│   │   └── index.css         # Global styles + Tailwind
│   ├── App.tsx               # Main app component with routing
│   └── main.tsx              # Application entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 🚀 Getting Started

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📄 Pages Overview

### 1. Catalog (/)
- **Statistical Overview:** Summary cards showing total commands, jobs, workflows, and datasets
- **Navigation Cards:** Quick access to all catalog sections
- **Route:** `/catalog`

### 2. Commands List
- **Features:** Sortable/filterable table, search functionality
- **Columns:** Name, Type, Family, Preconditions, Output Type, Output File, Description
- **Actions:** View (JSON/TEXT) or Download (FILE) outputs
- **Route:** `/catalog/commands`

### 3. Jobs
- **Features:** View and manage JCL jobs
- **Columns:** Name, Scope, Mainframe, Type, Access Level, Status, Last Run, Download
- **Route:** `/catalog/jobs`

### 4. Workflows
- **Features:** Manage multi-step workflows
- **Columns:** Name, Scope, Mainframe, Type, Steps, Dependencies, Access Level, Status
- **Route:** `/catalog/workflows`

### 5. Datasets
- **Features:** Access mainframe datasets
- **Columns:** Name, Scope, Mainframe, Type, Size, Records, Access Level, Download
- **Route:** `/catalog/datasets`

### 6. Reasoning Agent Logs
- **Features:**
  - Live streaming terminal-style interface
  - Auto-scrolling with pause/resume controls
  - Color-coded log levels (Thought, Action, Observation, Decision)
  - Clear logs functionality
- **Route:** `/reasoning-logs`

### 7. Execution Panel
- **Features:**
  - Chatbot interface for command execution
  - Message history with timestamps
  - Canonical output display (JSON, Table, File, Text)
  - Voice input button (UI only)
  - Typing indicators and loading states
- **Route:** `/execution`

### 8. IBM Agent Dashboard
- **Features:**
  - Agent status monitoring
  - Capabilities list
  - Configuration panel (read-only)
  - Recent executions table
  - Uptime and task completion metrics
- **Route:** `/ibm-agent`

### 9. Unisys Agent Dashboard
- **Features:**
  - Similar to IBM Agent but with MCP-specific details
  - Command compatibility matrix
  - Environment metadata
  - Execution history timeline
- **Route:** `/unisys-agent`

## 🔌 Backend Integration Points

All backend calls are **STUBBED** and clearly marked with comments. To integrate with your backend:

### API Service (`src/services/api.ts`)

Each function includes a commented-out backend integration example:

```typescript
// Example: Fetch Commands
export const fetchCommandsCatalog = async (): Promise<Command[]> => {
  // TODO: Implement backend call
  // const response = await fetch('/api/catalog/commands');
  // return await response.json();
  
  // Currently returns mock data
  return new Promise((resolve) => {
    setTimeout(() => resolve(mockCommands), 500);
  });
};
```

### Integration Checklist

1. **Catalog Service** (`/api/catalog/*`)
   - [ ] `GET /api/catalog/commands` - fetchCommandsCatalog()
   - [ ] `GET /api/catalog/jobs` - fetchJobs()
   - [ ] `GET /api/catalog/workflows` - fetchWorkflows()
   - [ ] `GET /api/catalog/datasets` - fetchDatasets()
   - [ ] `GET /api/catalog/stats` - fetchCatalogStats()

2. **Reasoning Service** (`/ws/reasoning` or `/api/reasoning/stream`)
   - [ ] WebSocket/SSE connection - subscribeToAgentReasoningStream()

3. **Chat/Execution Service** (`/api/chat/*`)
   - [ ] `POST /api/chat/message` - sendUserQuery()
   - [ ] `POST /api/commands/execute` - executeCommand()
   - [ ] `GET /api/commands/{id}/output` - getCanonicalOutput()

4. **IBM Agent Service** (`/api/agents/ibm/*`)
   - [ ] `GET /api/agents/ibm/status` - getIBMAgentStatus()
   - [ ] `POST /api/agents/ibm/tasks` - sendTaskToIBMAgent()
   - [ ] `GET /api/agents/ibm/executions` - getIBMAgentExecutions()
   - [ ] `GET /api/agents/ibm/config` - getIBMAgentConfig()

5. **Unisys Agent Service** (`/api/agents/unisys/*`)
   - [ ] `GET /api/agents/unisys/status` - getUnisysAgentStatus()
   - [ ] `POST /api/agents/unisys/tasks` - sendTaskToUnisysAgent()
   - [ ] `GET /api/agents/unisys/executions` - getUnisysAgentExecutions()
   - [ ] `GET /api/agents/unisys/config` - getUnisysAgentConfig()

## 🎯 Key Features

### Reusable Components

- **Table Component:** Generic, sortable, searchable table with column customization
- **StatCard:** Dashboard metric cards with trends and icons
- **Modal:** Accessible modal dialogs using Headless UI
- **Layout:** Consistent layout with sidebar navigation and header
- **LoadingSpinner:** Consistent loading states

### Responsive Design

- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Collapsible sidebar on mobile (can be implemented)

### Accessibility

- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus management in modals
- Screen reader friendly

### Type Safety

- Full TypeScript coverage
- Strongly typed API responses
- Type-safe component props
- No `any` types in production code

## 🎨 Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme:

```javascript
colors: {
  terminal: {
    bg: '#0a0e1a',
    panel: '#111827',
    border: '#1f2937',
    accent: '#00ff88',   // Primary accent
    amber: '#ffb000',    // Warning/attention
    blue: '#00d4ff',     // Secondary accent
    purple: '#a855f7',   // Tertiary accent
    red: '#ff3366',      // Errors/alerts
  },
}
```

### Typography

Fonts are loaded from Google Fonts in `src/styles/index.css`:
- Display: Space Grotesk
- Body: Inter
- Mono: JetBrains Mono

## 🐛 Development Notes

### Mock Data

All data is currently mocked in `src/services/mockData.ts`. This includes:
- Sample commands, jobs, workflows, datasets
- Agent statuses and configurations
- Execution history
- Chat messages

### Streaming Simulation

The reasoning logs page simulates a live stream using `setInterval`. Replace with actual WebSocket/SSE connection when backend is ready.

### File Downloads

Download functionality is currently mocked with `alert()` calls. Implement actual file download logic when backend endpoints are available.

## 📝 TODO / Future Enhancements

- [ ] Implement actual backend integration
- [ ] Add authentication/authorization
- [ ] Implement voice input functionality
- [ ] Add real-time notifications
- [ ] Implement advanced filtering and sorting
- [ ] Add export functionality (CSV, PDF)
- [ ] Implement dark/light theme toggle
- [ ] Add user preferences/settings page
- [ ] Implement command scheduling
- [ ] Add execution history graphs/charts

## 🤝 Contributing

When adding new features:

1. Follow the existing component structure
2. Maintain TypeScript type safety
3. Keep API calls in the service layer
4. Use mock data for development
5. Document backend integration points
6. Follow the established design system

## 📄 License

[Your License Here]

## 🎉 Acknowledgments

Built with modern web technologies and a focus on developer experience and production readiness.
