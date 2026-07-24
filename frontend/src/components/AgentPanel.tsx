import { FormEvent, useState } from "react"

interface ToolExecution {
	tool_call_id: string
	tool_name: string
	arguments: Record<string, unknown>
	result: Record<string, unknown>
}

interface AgentResponse {
	answer: string
	finish_reason: "completed" | "max_steps_reached" | "model_error"
	tool_executions: ToolExecution[]
}

export function AgentPanel() {
	const [input, setInput] = useState("")
	const [answer, setAnswer] = useState("")
	const [toolExecutions, setToolExecutions] = useState<ToolExecution[]>([])
	const [isLoading, setIsLoading] = useState(false)
	const [error, setError] = useState("")

	async function handleSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault()

		const message = input.trim()

		if (!message || isLoading) {
			return
		}

		setAnswer("")
		setToolExecutions([])
		setError("")
		setIsLoading(true)

		try {
			const response = await fetch("http://127.0.0.1:8000/api/agent/chat", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					message
				})
			})

			if (!response.ok) {
				throw new Error(`Request failed with status ${response.status}`)
			}

			const data: AgentResponse = await response.json()

			setAnswer(data.answer)
			setToolExecutions(data.tool_executions)
		} catch (requestError) {
			setError(requestError instanceof Error ? requestError.message : "Unknown request error")
		} finally {
			setIsLoading(false)
		}
	}

	return (
		<section>
			<header>
				<h2>OpsPilot Agent</h2>
				<p>Ask about a project status or a general operations topic.</p>
			</header>

			<form onSubmit={handleSubmit}>
				<textarea
					value={input}
					onChange={event => setInput(event.target.value)}
					placeholder='Is the OpsPilot Frontend running?'
					rows={4}
					maxLength={4000}
					disabled={isLoading}
				/>

				<button type='submit' disabled={!input.trim() || isLoading}>
					{isLoading ? "Running agent..." : "Send"}
				</button>
			</form>

			{error && <p role='alert'>{error}</p>}

			{answer && (
				<article>
					<h3>Answer</h3>
					<p style={{ whiteSpace: "pre-wrap" }}>{answer}</p>
				</article>
			)}

			{toolExecutions.length > 0 && (
				<section>
					<h3>Tool executions</h3>

					{toolExecutions.map(execution => (
						<details key={execution.tool_call_id}>
							<summary>{execution.tool_name}</summary>

							<h4>Arguments</h4>
							<pre>{JSON.stringify(execution.arguments, null, 2)}</pre>

							<h4>Result</h4>
							<pre>{JSON.stringify(execution.result, null, 2)}</pre>
						</details>
					))}
				</section>
			)}
		</section>
	)
}
