import React, { useState, useRef } from 'react';

const TOTAL_STEPS = 13; // Updated to match the 13 fragments

function toBase64Url(b64) {
  return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// UUID generator fallback for non-HTTPS environments
function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for HTTP contexts
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function MatrixCard() {
  const [step, setStep] = useState(0);
  const [gifSrc, setGifSrc] = useState(null);
  const [message, setMessage] = useState('');
  const [completed, setCompleted] = useState(false);
  const cardRef = useRef(null);

  const handleClick = async () => {
    setMessage('');
    const payload = {
      signal: `step-${step}`,
      trace: generateUUID(),
      entropy: Math.random().toString(),
      node: 'frontend-node',
      step: step  // Send current step to backend
    };

    try {
      const response = await fetch('/api/escape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const fragment = response.headers.get('X-Matrix-Id');
        if (fragment && cardRef.current) {
          const urlSafeFragment = toBase64Url(fragment);
          cardRef.current.id += `.${urlSafeFragment}`;
        }

        const blob = await response.blob();
        const objectURL = URL.createObjectURL(blob);
        setGifSrc(objectURL);
        
        const newStep = step + 1;
        setStep(newStep);
        
        // Check if all steps are completed
        if (newStep >= TOTAL_STEPS) {
          setCompleted(true);
          setMessage('Congratulations! You have escaped the Matrix. Now it\'s time to enter the void...');
        }

      } else if (response.status === 429) {
        setMessage('Too many requests. Please wait a moment...');
      } else if (response.status === 400) {
        setMessage('Invalid step. Please reload the page.');
      } else {
        setMessage(`Error: ${response.statusText}`);
      }
    } catch (error) {
      setMessage(`Network error: ${error.message}`);
    }
  };

  return (
    <div className="matrix-card-overlay">
      <div id="matrix-card" ref={cardRef} className="card" data-testid="matrix-card-div">
        {gifSrc && <img id="matrix-gif" src={gifSrc} alt="Matrix GIF" />}
        <div className="card-controls">
          <button 
            id="escape-button" 
            onClick={handleClick} 
            disabled={completed}
            className={completed ? 'completed' : ''}
          >
            {completed ? 'Escaped!' : 'Escape Matrix'}
          </button>
        </div>
        {message && <p className="message">{message}</p>}
      </div>
    </div>
  );
}

export default MatrixCard;
