import { ChatPanel } from "./components/ChatPanel"
import { AgentPanel } from "./components/AgentPanel"

function App() {
	return (
		<main>
			<h1>OpsPilot</h1>
			<p>AI-powered operations assistant</p>

			<AgentPanel />
		</main>
	)
}

export default App
