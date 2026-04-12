import { useState } from 'react';
import './GroundingPanel.css';

export default function GroundingPanel({ grounding }) {
  const [expanded, setExpanded] = useState(false);

  if (!grounding) return null;

  const { plan, pinecone = [], tavily = [] } = grounding;
  const totalChunks = pinecone.length + tavily.length;

  if (totalChunks === 0 && !plan?.reasoning) return null;

  return (
    <div className="grounding-panel">
      <div
        className="grounding-header"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="grounding-icon">&#x1f50d;</span>
        <span className="grounding-title">
          Grounding Context
          <span className="grounding-count">
            {totalChunks} source{totalChunks !== 1 ? 's' : ''} retrieved
            {pinecone.length > 0 && tavily.length > 0
              ? ` (${pinecone.length} KB + ${tavily.length} web)`
              : pinecone.length > 0
                ? ` (knowledge base)`
                : tavily.length > 0
                  ? ` (web/news)`
                  : ''}
          </span>
        </span>
        <span className={`grounding-chevron ${expanded ? 'open' : ''}`}>
          &#x25B6;
        </span>
      </div>

      {expanded && (
        <div className="grounding-body">
          {plan?.reasoning && (
            <div className="grounding-plan">
              <strong>Planner:</strong> {plan.reasoning}
              {plan.use_tavily && plan.tavily_query && (
                <span className="grounding-search-query">
                  {' '}| Search: &quot;{plan.tavily_query}&quot; ({plan.tavily_topic})
                </span>
              )}
            </div>
          )}

          {pinecone.length > 0 && (
            <div className="grounding-section">
              <h4>Knowledge Base</h4>
              {pinecone.map((chunk, i) => (
                <div key={`kb-${i}`} className="grounding-chunk">
                  <div className="chunk-header">
                    <span className="chunk-label">KB {i + 1}</span>
                    {chunk.source && (
                      <span className="chunk-source">{chunk.source}</span>
                    )}
                    <span className="chunk-score">
                      {(chunk.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="chunk-text">{chunk.text}</div>
                </div>
              ))}
            </div>
          )}

          {tavily.length > 0 && (
            <div className="grounding-section">
              <h4>Web / News</h4>
              {tavily.map((chunk, i) => (
                <div key={`web-${i}`} className="grounding-chunk">
                  <div className="chunk-header">
                    <span className="chunk-label">Web {i + 1}</span>
                    {chunk.title && (
                      <span className="chunk-title">{chunk.title}</span>
                    )}
                    {chunk.source && (
                      <a
                        className="chunk-source-link"
                        href={chunk.source}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {new URL(chunk.source).hostname}
                      </a>
                    )}
                  </div>
                  <div className="chunk-text">{chunk.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
