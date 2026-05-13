// Shared types between component layers. The SSE frame shapes here must
// match what `ui/app/chat/sse.py:event_to_frame` emits — renaming fields on
// either side is a cross-cutting breaking change.

export interface ProviderConfig {
  id: string;
  display_name: string;
  credential_fields: CredentialField[];
  models: ModelInfo[];
}

export interface CredentialField {
  id: string;
  display_name: string;
  secret: boolean;
}

export interface ModelInfo {
  id: string;
  display_name: string;
}

// Messages as rendered in the transcript. Mirrors the shape of
// `ChatMessage.content` in the DB so server-rendered and in-flight messages
// look identical to React.
export type MessageRole = "user" | "assistant" | "tool" | "tool_result";

export interface TranscriptMessage {
  id: string;
  role: MessageRole;
  text: string;
  tool_activity?: ToolActivity[];
  error?: string | null;
  created_at?: string;
  /** Set on in-flight messages that haven't been committed yet. */
  pending?: boolean;
}

export type ToolActivity =
  | { type: "tool_call"; name: string; input: unknown; tool_use_id: string | null }
  | {
      type: "tool_result";
      tool_use_id: string | null;
      content: unknown;
      is_error: boolean;
    };

// SSE frame payloads from the backend. One interface per `event:` kind.
export interface SessionInitializedData {
  sdk_session_id: string;
}
export interface TextDeltaData {
  text: string;
}
export interface ToolCallData {
  name: string;
  input: unknown;
  tool_use_id: string | null;
}
export interface ToolResultData {
  tool_use_id: string | null;
  content: unknown;
  is_error: boolean;
}
export interface ErrorData {
  message: string;
}
export interface TurnCompleteData {
  result_subtype: string | null;
}
export interface TurnPersistedData {
  assistant_message_id: string;
}

export type SSEFrame =
  | { event: "session_initialized"; data: SessionInitializedData }
  | { event: "text_delta"; data: TextDeltaData }
  | { event: "tool_call"; data: ToolCallData }
  | { event: "tool_result"; data: ToolResultData }
  | { event: "error"; data: ErrorData }
  | { event: "turn_complete"; data: TurnCompleteData }
  | { event: "turn_persisted"; data: TurnPersistedData };
