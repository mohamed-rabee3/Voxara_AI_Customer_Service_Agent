/**
 * LiveKit Utilities
 * 
 * Helper functions for LiveKit room connection and token management.
 */

export interface TokenResponse {
    token: string;
    room_name: string;
    participant_identity: string;
    livekit_url: string;
}

export interface TokenRequest {
    room_name: string;
    participant_name: string;
    participant_identity?: string;
}

/**
 * Generate a random room name for new sessions
 */
export function generateRoomName(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `voara-${timestamp}-${random}`;
}

/**
 * Fetch a LiveKit access token from the backend API
 */
export async function fetchToken(request: TokenRequest): Promise<TokenResponse> {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const response = await fetch(`${apiUrl}/api/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `Failed to fetch token: ${response.status}`);
    }

    return response.json();
}

/**
 * Get the LiveKit WebSocket URL
 */
export function getLiveKitUrl(): string {
    return process.env.NEXT_PUBLIC_LIVEKIT_URL || "";
}

/**
 * Connection state type
 */
export type ConnectionState =
    | "disconnected"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "error";

/**
 * Agent state based on activity
 */
export type AgentState =
    | "idle"
    | "listening"
    | "speaking"
    | "thinking";

/**
 * Transcript message interface
 */
export interface TranscriptMessage {
    id: string;
    role: "user" | "agent";
    text: string;
    timestamp: Date;
    isFinal: boolean;
}

/**
 * RAG context from agent metadata
 */
export interface RAGContext {
    query: string;
    context: string;
    timestamp: Date;
}

/**
 * Parse room metadata for agent state
 */
export function parseAgentMetadata(metadata: string | undefined): {
    ragContext?: RAGContext;
    agentState?: AgentState;
} {
    if (!metadata) return {};

    try {
        const data = JSON.parse(metadata);
        return {
            ragContext: data.rag_context ? {
                query: data.rag_query || "",
                context: data.rag_context,
                timestamp: new Date(),
            } : undefined,
            agentState: data.agent_state as AgentState | undefined,
        };
    } catch {
        return {};
    }
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(date: Date): string {
    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

/**
 * Detect if text is RTL (Arabic, Hebrew, etc.)
 */
export function isRTL(text: string): boolean {
    const rtlRegex = /[\u0591-\u07FF\uFB1D-\uFDFD\uFE70-\uFEFC]/;
    return rtlRegex.test(text);
}

/**
 * Get text direction based on content
 */
export function getTextDirection(text: string): "ltr" | "rtl" {
    return isRTL(text) ? "rtl" : "ltr";
}
