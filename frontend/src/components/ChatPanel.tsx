import { useState, type SubmitEvent } from "react"

interface Message {
	id: string
	role: "user" | "assistant"
	content: string
}

function createMessageId(): string {
	return crypto.randomUUID()
}

export function ChatPanel() {
	const [input, setInput] = useState("")
	const [messages, setMessages] = useState<Message[]>([])
	const [isStreaming, setIsStreaming] = useState(false)
	const [error, setError] = useState("")

	async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
		event.preventDefault()

		const message = input.trim()

		if (!message || isStreaming) {
			return
		}

		const userMessage: Message = {
			id: createMessageId(),
			role: "user",
			content: message
		}

		const assistantMessageId = createMessageId()

		const assistantMessage: Message = {
			id: assistantMessageId,
			role: "assistant",
			content: ""
		}

		setMessages(current => [...current, userMessage, assistantMessage])

		setInput("")
		setError("")
		setIsStreaming(true)

		try {
			const response = await fetch("http://127.0.0.1:8000/api/chat/stream", {
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

			if (!response.body) {
				throw new Error("The response stream is unavailable.")
			}

			const reader = response.body.getReader()
			const decoder = new TextDecoder("utf-8")

			while (true) {
				const { value, done } = await reader.read()

				if (done) {
					break
				}

				const text = decoder.decode(value, {
					stream: true
				})

				setMessages(current =>
					current.map(item =>
						item.id === assistantMessageId
							? {
									...item,
									content: item.content + text
								}
							: item
					)
				)
			}

			const remainingText = decoder.decode()

			if (remainingText) {
				setMessages(current =>
					current.map(item =>
						item.id === assistantMessageId
							? {
									...item,
									content: item.content + remainingText
								}
							: item
					)
				)
			}
		} catch (requestError) {
			const errorMessage = requestError instanceof Error ? requestError.message : "An unknown error occurred."

			setError(errorMessage)

			setMessages(current =>
				current.map(item =>
					item.id === assistantMessageId
						? {
								...item,
								content: "Unable to generate a response."
							}
						: item
				)
			)
		} finally {
			setIsStreaming(false)
		}
	}

	return (
		<section>
			<header>
				<h2>OpsPilot Assistant</h2>
				<p>Ask questions about development and operations.</p>
			</header>

			<div>
				{messages.length === 0 ? (
					<p>No messages yet.</p>
				) : (
					messages.map(message => (
						<article key={message.id}>
							<strong>{message.role === "user" ? "You" : "OpsPilot"}</strong>

							<p style={{ whiteSpace: "pre-wrap" }}>{message.content || (message.role === "assistant" && isStreaming ? "Thinking..." : "")}</p>
						</article>
					))
				)}
			</div>

			{error && <p role='alert'>{error}</p>}

			<form onSubmit={handleSubmit}>
				<textarea
					value={input}
					onChange={event => setInput(event.target.value)}
					placeholder='Ask OpsPilot a question...'
					rows={4}
					maxLength={4000}
					disabled={isStreaming}
				/>

				<button type='submit' disabled={!input.trim() || isStreaming}>
					{isStreaming ? "Generating..." : "Send"}
				</button>
			</form>
		</section>
	)
}
