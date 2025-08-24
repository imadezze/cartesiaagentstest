# 🚀 Cartesia Sales Agent - Flow Visualizer

An interactive Next.js frontend for visualizing and exploring state machine flows from the Cartesia Sales Agent system. Click nodes, inspect edges, and navigate between different flows seamlessly.

## ✨ Features

### 🎯 Interactive Visualization
- **Click nodes** to see detailed information and connections  
- **Hover for tooltips** with descriptions and metadata
- **Visual flow direction** with curved arrows and clear paths
- **Hierarchical layout** showing start → process → end flows

### 🔍 Node Inspection
- **Detailed node modals** with descriptions and properties
- **Connection overview** showing incoming and outgoing edges
- **Navigation between nodes** by clicking connection references
- **Type indicators** with emoji icons and color coding

### 🌊 Flow Navigation
- **5 different flows**: Conversation, Leads Extraction, Research, Validation, System Architecture
- **Smooth transitions** between flows with preserved state
- **Flow statistics** showing node and edge counts
- **Color-coded flow cards** for easy identification

### 🎨 Enhanced UI/UX
- **Modern design** with Tailwind CSS styling
- **Responsive layout** that works on all screen sizes
- **Loading states** and error handling
- **Interactive legends** and visual guides

## 📊 Available Flows

### 💬 Conversation Flow
Main user conversation states and transitions for customer interactions.

### 📊 Leads Extraction  
Background processing for extracting user information from conversations.

### 🔍 Research Node
Company research and intelligence gathering workflow.

### ✅ Call Validation
End-call condition validation and safety checks.

### 🏗️ System Architecture
High-level overview of system component interactions.

## 🛠️ Technical Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety  
- **Tailwind CSS** for styling
- **React Hooks** for state management
- **SVG** for graph rendering
- **JSON Configuration** driven

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. **Navigate to the flow visualizer directory:**
   ```bash
   cd flow-visualizer
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

### Configuration

The visualizer automatically loads from `/public/state_machine_config.json` which contains:

- **Metadata**: Project information and versioning
- **Flow Definitions**: States, transitions, and descriptions  
- **System Architecture**: Component relationships
- **Color Schemes**: Visual styling configuration

## 📱 How to Use

### 1. **Select a Flow**
Click on any of the 5 flow cards at the top to switch between different state machines.

### 2. **Explore Nodes**  
- **Click any node** to open detailed information
- **See incoming/outgoing connections** with trigger conditions
- **Navigate between connected nodes** using the arrow buttons

### 3. **Inspect Edges**
- **Hover over edges** to see trigger conditions
- **Click edges** for more detailed information
- **Follow the flow** using visual arrows and colors

### 4. **Understand the Flow**
- **Green nodes** = START points (flow entry)
- **Red nodes** = END points (flow exit)  
- **Yellow nodes** = Decision points
- **Blue nodes** = Process states
- **Purple nodes** = Validation steps

## 🎯 Key Interactions

| Action | Result |
|--------|--------|
| Click node | Opens detailed modal with connections |
| Hover node | Shows tooltip with description |
| Click edge | Logs edge details (expandable) |
| Hover edge | Shows trigger/condition information |
| Click flow card | Switches to different state machine |
| Click connection button | Navigates to connected node |

## 🔧 Architecture

```
src/
├── app/page.tsx              # Main application page
├── components/
│   ├── FlowVisualization.tsx # SVG graph rendering
│   ├── FlowSelector.tsx      # Flow navigation cards  
│   └── NodeDetails.tsx       # Node inspection modal
├── types/index.ts            # TypeScript definitions
└── utils/graphUtils.ts       # Graph processing utilities
```

## 🎨 Customization

### Adding New Flows
1. Update `state_machine_config.json` with new flow data
2. Add flow entry to `FlowSelector.tsx` 
3. Update type definitions in `types/index.ts`

### Styling Changes
- Modify colors in `utils/graphUtils.ts`
- Update Tailwind classes in components
- Adjust SVG styling in `FlowVisualization.tsx`

### Layout Options  
- Change positioning in `calculatePositions()` function
- Modify curve calculations for edges
- Adjust node sizes and spacing

## 🐛 Troubleshooting

### Common Issues

**JSON not loading?**
- Ensure `state_machine_config.json` is in `/public/` directory
- Check browser console for fetch errors
- Verify JSON syntax is valid

**Nodes not positioning correctly?**
- Check that all nodes have valid IDs
- Ensure transitions reference existing node IDs
- Verify flow data structure matches types

**Styling issues?**
- Run `npm run build` to check for build errors
- Ensure Tailwind CSS classes are correctly applied
- Check browser console for CSS errors

## 📈 Performance

- **Optimized rendering** with React's built-in optimizations
- **Efficient layouts** using mathematical positioning  
- **Minimal re-renders** with proper state management
- **Responsive design** that scales to large graphs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Cartesia Sales Agent examples collection.

---

**🎉 Enjoy exploring your state machine flows visually!**
