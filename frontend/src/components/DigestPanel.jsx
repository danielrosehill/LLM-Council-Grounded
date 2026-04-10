import { useState } from 'react';
import { api } from '../api';
import './DigestPanel.css';

export default function DigestPanel({ conversationId, messageIndex }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [digest, setDigest] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const result = await api.generateDigest(conversationId, messageIndex);
      setDigest(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="digest-panel">
      <div className="digest-header">
        <h4>Council Digest</h4>
        {!digest && (
          <button
            className="digest-btn"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate PDF + Podcast'}
          </button>
        )}
      </div>

      {isGenerating && (
        <div className="digest-loading">
          <div className="spinner"></div>
          <span>Generating report and podcast...</span>
        </div>
      )}

      {error && (
        <div className="digest-error">
          Error: {error}
        </div>
      )}

      {digest && (
        <div className="digest-results">
          <div className="digest-item">
            <span className="digest-label">PDF Report:</span>
            {digest.pdf_path && (
              <a
                href={`http://localhost:8001/api/files/${digest.pdf_path.replace('data/', '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="digest-link"
              >
                Download PDF
              </a>
            )}
          </div>

          <div className="digest-item">
            <span className="digest-label">Podcast:</span>
            {digest.audio_path && digest.audio_path.endsWith('.mp3') ? (
              <audio controls className="digest-audio">
                <source
                  src={`http://localhost:8001/api/files/${digest.audio_path.replace('data/', '')}`}
                  type="audio/mpeg"
                />
                Your browser does not support audio.
              </audio>
            ) : (
              <span className="digest-note">
                Audio generation requires edge-tts. Script saved to file.
              </span>
            )}
          </div>

          {digest.podcast_script && (
            <details className="digest-script">
              <summary>View Podcast Script</summary>
              <pre>{digest.podcast_script}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
