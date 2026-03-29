'use client';

import { useState, useRef, useEffect } from 'react';
import {
  XMarkIcon,
  PaperAirplaneIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, ApiError } from '@/lib/api-client';
import type {
  AgentConversationResponse,
  AgentMessageResponse,
} from '@/lib/api-types';

interface ChatPanelProps {
  conversation: AgentConversationResponse;
  onClose: () => void;
  onUpdate: () => void;
}

export function ChatPanel({ conversation, onClose, onUpdate }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation.messages]);

  async function handleSend() {
    if (!input.trim() || isSending) return;

    const message = input.trim();
    setInput('');
    setIsSending(true);
    setError(null);

    try {
      await api.agents.sendMessage(conversation.id, { content: message });
      onUpdate();
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          (err.body as Record<string, unknown>)?.detail || 'Onbekende fout';
        setError(String(detail));
      } else {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setIsSending(false);
    }
  }

  async function handleFeedback(feedback: 'positief' | 'negatief') {
    try {
      await api.agents.submitFeedback(conversation.id, { feedback });
    } catch {
      // Silent fail for feedback
    }
  }

  async function handleGenerate() {
    setIsGenerating(true);
    setError(null);
    setGenerateResult(null);

    try {
      const result = await api.agents.generateDocuments(conversation.id);
      setGenerateResult(result.message);
      onUpdate();
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          (err.body as Record<string, unknown>)?.detail || 'Generatie mislukt';
        setError(String(detail));
      } else {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setIsGenerating(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="fixed right-0 top-0 z-50 flex h-full w-[400px] flex-col border-l border-neutral-200 bg-white shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span className="text-sm font-medium text-neutral-900">
            {conversation.agent_name}
          </span>
          <Badge variant="default">AI</Badge>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {conversation.messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onFeedback={
              msg.role === 'assistant' && msg.audit_log_id
                ? handleFeedback
                : undefined
            }
          />
        ))}

        {isSending && (
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <div className="h-2 w-2 animate-pulse rounded-full bg-primary-400" />
            Agent denkt na...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Generate button */}
      {conversation.status === 'active' && conversation.messages.length > 1 && (
        <div className="mx-4 mb-2">
          {generateResult ? (
            <div className="rounded-md bg-green-50 border border-green-200 px-3 py-2 text-xs text-green-700">
              {generateResult}
            </div>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              disabled={isGenerating || isSending}
              onClick={handleGenerate}
              className="w-full"
            >
              <DocumentArrowDownIcon className="mr-1.5 h-4 w-4" />
              {isGenerating ? 'Documenten genereren...' : 'Genereer concept-documenten'}
            </Button>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mx-4 mb-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-neutral-200 px-4 py-3">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Typ een bericht..."
            rows={2}
            className="flex-1 resize-none rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            disabled={isSending || conversation.status !== 'active'}
          />
          <Button
            variant="primary"
            size="sm"
            disabled={!input.trim() || isSending}
            onClick={handleSend}
          >
            <PaperAirplaneIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function ChatMessage({
  message,
  onFeedback,
}: {
  message: AgentMessageResponse;
  onFeedback?: (feedback: 'positief' | 'negatief') => void;
}) {
  const isAssistant = message.role === 'assistant';

  return (
    <div
      className={`flex flex-col ${isAssistant ? 'items-start' : 'items-end'}`}
    >
      <div
        className={`max-w-[90%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
          isAssistant
            ? 'bg-neutral-50 text-neutral-800 border border-neutral-200'
            : 'bg-primary-600 text-white'
        }`}
      >
        {isAssistant && (
          <div className="mb-1 flex items-center gap-1.5">
            <Badge variant="default">AI CONCEPT</Badge>
          </div>
        )}
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>

      {/* Feedback buttons for assistant messages */}
      {isAssistant && onFeedback && (
        <div className="mt-1 flex gap-1">
          <button
            onClick={() => onFeedback('positief')}
            className="rounded p-1 text-neutral-300 hover:text-green-500"
            title="Goed antwoord"
          >
            <HandThumbUpIcon className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => onFeedback('negatief')}
            className="rounded p-1 text-neutral-300 hover:text-red-500"
            title="Kan beter"
          >
            <HandThumbDownIcon className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
