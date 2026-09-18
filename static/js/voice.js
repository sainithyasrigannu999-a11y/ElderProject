document.addEventListener('DOMContentLoaded', () => {
  const voiceButton = document.getElementById('voiceButton');
  const voiceText = document.getElementById('voiceText');
  const analyzeVoiceBtn = document.getElementById('analyzeVoiceBtn');
  const cancelVoiceBtn = document.getElementById('cancelVoiceBtn');
  const voiceManualInput = document.getElementById('voiceManualInput');
  const useManualVoiceBtn = document.getElementById('useManualVoiceBtn');
  const clearVoiceInputBtn = document.getElementById('clearVoiceInputBtn');

  if (!voiceButton || !voiceText || !analyzeVoiceBtn || !cancelVoiceBtn) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceText.textContent = 'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari with microphone access enabled.';
    voiceButton.disabled = true;
    analyzeVoiceBtn.disabled = true;
    return;
  }

  const recognition = new SpeechRecognition();
  let currentText = '';
  let isListening = false;
  let isManuallyStopped = false;

  const syncManualInput = () => {
    if (voiceManualInput) {
      voiceManualInput.value = currentText;
    }
  };

  const updateCurrentText = (text) => {
    currentText = text.trim();
    syncManualInput();
    if (currentText) {
      setStatus(`You said: ${currentText}`);
    } else {
      setStatus('You said: ');
    }
  };

  recognition.lang = 'en-US';
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  const setStatus = (message, isError = false) => {
    voiceText.textContent = message;
    voiceText.classList.toggle('text-danger', isError);
    voiceText.classList.toggle('text-muted', !isError);
  };

  const setListeningUi = (listening) => {
    isListening = listening;
    voiceButton.textContent = listening ? '🔴 Stop Listening' : '🎙️ Start Listening';
    voiceButton.classList.toggle('btn-danger', listening);
    voiceButton.classList.toggle('btn-primary', !listening);
  };

  const stopListening = () => {
    isManuallyStopped = true;
    try {
      recognition.stop();
    } catch (error) {
      // Ignore stop errors when recognition is already inactive.
    }
    setListeningUi(false);
  };

  const startListening = async () => {
    if (isListening) {
      stopListening();
      return;
    }

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      isManuallyStopped = false;
      recognition.start();
    } catch (error) {
      setStatus('Microphone access was denied. Please allow microphone permissions and try again.', true);
      setListeningUi(false);
    }
  };

  recognition.onstart = () => {
    setListeningUi(true);
    setStatus('Listening...');
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      const text = result[0].transcript.trim();
      if (text) {
        transcript += `${text} `;
      }
      if (result.isFinal && text) {
        currentText = text;
      }
    }

    if (transcript.trim()) {
      currentText = transcript.trim();
      setStatus(`You said: ${currentText}`);
    }
  };

  recognition.onend = () => {
    if (isManuallyStopped) {
      return;
    }

    setListeningUi(false);

    if (currentText.trim()) {
      setStatus(`You said: ${currentText.trim()}`);
      return;
    }

    setStatus('No speech was detected. Please speak clearly and try again.');

    try {
      recognition.start();
    } catch (error) {
      // The browser may reject a restart while the recognition session is still resetting.
    }
  };

  recognition.onerror = (event) => {
    let message = 'Speech recognition could not understand the input. Please try again.';

    if (event.error === 'no-speech') {
      message = 'No speech was detected. Please speak clearly into the microphone.';
    } else if (event.error === 'not-allowed') {
      message = 'Microphone access was blocked. Please allow microphone access in your browser settings.';
    } else if (event.error === 'audio-capture') {
      message = 'No microphone was detected. Please check that your microphone is connected and working.';
    } else if (event.error === 'network') {
      message = 'Speech recognition is temporarily unavailable. Please try again in a moment.';
    }

    setStatus(message, true);
    setListeningUi(false);
  };

  voiceButton.addEventListener('click', async () => {
    await startListening();
  });

  cancelVoiceBtn.addEventListener('click', () => {
    currentText = '';
    stopListening();
    if (voiceManualInput) {
      voiceManualInput.value = '';
    }
    setStatus('You said: ');
  });

  if (useManualVoiceBtn && voiceManualInput) {
    useManualVoiceBtn.addEventListener('click', () => {
      const typedText = voiceManualInput.value.trim();
      if (!typedText) {
        setStatus('Please type what happened before analyzing the emergency.', true);
        return;
      }
      updateCurrentText(typedText);
    });
  }

  if (clearVoiceInputBtn && voiceManualInput) {
    clearVoiceInputBtn.addEventListener('click', () => {
      voiceManualInput.value = '';
      currentText = '';
      setStatus('You said: ');
    });
  }

  analyzeVoiceBtn.addEventListener('click', async () => {
    const typedText = voiceManualInput ? voiceManualInput.value.trim() : '';
    if (typedText && !currentText.trim()) {
      currentText = typedText;
    }

    if (!currentText.trim()) {
      setStatus('Please speak or type before analyzing the emergency.', true);
      return;
    }

    const formData = new FormData();
    formData.append('description', currentText);
    formData.append('input_type', 'voice');
    formData.append('location_text', 'Manual location');

    const response = await fetch('/elderly/dashboard/sos', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    const alertBox = document.getElementById('alertArea');
    if (alertBox) {
      alertBox.innerHTML = `<div class="alert alert-info">${data.message || 'Emergency analyzed.'}</div>`;
    }
    showConfirmationModal(data.emergency_id, currentText);
  });

  function showConfirmationModal(emergencyId, description) {
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const confirmationText = document.getElementById('confirmationText');
    confirmationText.textContent = `Emergency summary: ${description}`;

    let timerId = setTimeout(async () => {
      const payload = new FormData();
      payload.append('choice', 'timeout');
      payload.append('emergency_id', emergencyId);
      payload.append('description', description);
      const response = await fetch('/elderly/dashboard/confirm', {
        method: 'POST',
        body: payload,
      });
      const data = await response.json();
      const alertBox = document.getElementById('alertArea');
      if (alertBox) {
        alertBox.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
      }
      modal.hide();
    }, Number(window.confirmationTimeoutSeconds || 30) * 1000);

    document.querySelectorAll('[data-confirm]').forEach((button) => {
      button.onclick = async () => {
        clearTimeout(timerId);
        const choice = button.getAttribute('data-confirm');
        const payload = new FormData();
        payload.append('choice', choice);
        payload.append('emergency_id', emergencyId);
        payload.append('description', description);

        const response = await fetch('/elderly/dashboard/confirm', {
          method: 'POST',
          body: payload,
        });
        const data = await response.json();
        const alertBox = document.getElementById('alertArea');
        if (alertBox) {
          alertBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
        }
        modal.hide();
      };
    });

    modal.show();
  }
});
