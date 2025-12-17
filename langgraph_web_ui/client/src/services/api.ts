export interface ChatRequest {
    message: string;
    thread_id: string;
}

export type EventCallback = (event: any) => void;

export async function streamChat(
    request: ChatRequest,
    onEvent: EventCallback,
    onError: (err: any) => void,
    onFinish: () => void
) {
    try {
        const response = await fetch("http://localhost:8000/chat/stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            const lines = buffer.split("\n\n");
            // Keep the last partial line in buffer
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const jsonStr = line.slice(6);
                    if (jsonStr.trim() === "[DONE]") { // OpenAI style, though we send {"type":"end"}
                        continue;
                    }
                    try {
                        const data = JSON.parse(jsonStr);
                        if (data.type === "end") {
                            onFinish();
                            return;
                        }
                        if (data.type === "error") {
                            onError(data.content);
                            return;
                        }
                        onEvent(data);
                    } catch (e) {
                        console.warn("Failed to parse SSE JSON:", jsonStr);
                    }
                }
            }
        }

        // Process remaining buffer if any? usually SSE ends with \n\n
        onFinish();

    } catch (err) {
        onError(err);
    }
}
