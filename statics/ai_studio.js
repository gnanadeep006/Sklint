const config = window.AI_STUDIO_CONFIG || {};
const ttsUrl = config.ttsUrl || '/ai-studio/tts/';
const sttUrl = config.sttUrl || '/ai-studio/stt/';

if (!window.isSecureContext) {
    console.warn('Microphone access requires https:// or http://localhost');
}

// --- DOM ELEMENTS ---
const modeBtns = document.querySelectorAll('.mode-btn');
const ttsSection = document.getElementById('tts-section');
const sttSection = document.getElementById('stt-section');
const ttsInput = document.getElementById('tts-input');
const voiceSelect = document.getElementById('voice-select');
const generateTtsBtn = document.getElementById('generate-tts');
const ttsResult = document.getElementById('tts-result');
const playAudioBtn = document.getElementById('play-audio');
const downloadAudioBtn = document.getElementById('download-audio');
const micBtn = document.getElementById('mic-btn');
const micStatus = document.getElementById('mic-status');
const generateSttBtn = document.getElementById('generate-stt');
const sttOutput = document.getElementById('stt-output');
const copyBtn = document.getElementById('copy-btn');

let currentAudioUrl = null;
let mediaRecorder = null;
let audioChunks = [];
let recordedBlob = null;
let isTranscribing = false;
let micPermissionRequested = false;

function setMode(mode) {
    modeBtns.forEach((b) => b.classList.remove('bg-brand-primary', 'text-white', 'shadow-lg'));
    modeBtns.forEach((b) => b.classList.add('text-white/40'));
    const active = Array.from(modeBtns).find((b) => b.dataset.mode === mode);
    if (active) {
        active.classList.add('bg-brand-primary', 'text-white', 'shadow-lg');
        active.classList.remove('text-white/40');
    }
    if (mode === 'tts') {
        ttsSection.classList.remove('hidden');
        sttSection.classList.add('hidden');
    } else {
        ttsSection.classList.add('hidden');
        sttSection.classList.remove('hidden');
        if (!micPermissionRequested) {
            micPermissionRequested = true;
            showMicStatus('Requesting microphone...');
            requestMicPermission()
                .then(() => showMicStatus('Microphone ready'))
                .catch((err) => {
                    console.error('Mic Permission Error:', err);
                    showMicStatus(err.message || 'Microphone access denied.', true);
                });
        }
    }
}

// --- MODE SWITCHING ---
modeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        setMode(mode);
    });
});

// Initialize default view
setMode('tts');

// --- TEXT TO SPEECH ---
generateTtsBtn.addEventListener('click', async () => {
    const text = (ttsInput.value || '').trim();
    if (!text) return;

    generateTtsBtn.disabled = true;
    generateTtsBtn.textContent = 'Generating...';

    try {
        const data = await postJson(ttsUrl, {
            text,
            voice: voiceSelect.value,
        });

        if (data.audio_base64) {
            if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);
            const sampleRate = data.sample_rate || 24000;
            const mimeType = data.mime_type || '';
            currentAudioUrl = createAudioUrl(data.audio_base64, mimeType, sampleRate);
            ttsResult.classList.remove('hidden');
            downloadAudioBtn.href = currentAudioUrl;
        }
    } catch (error) {
        console.error('TTS Error:', error);
        alert('Failed to generate voice. Check console for details.');
    } finally {
        generateTtsBtn.disabled = false;
        generateTtsBtn.textContent = 'Generate Voice';
    }
});

playAudioBtn.addEventListener('click', () => {
    if (currentAudioUrl) {
        const audio = new Audio(currentAudioUrl);
        audio.play();
    }
});

async function ensureMicAccess() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone not supported in this browser.');
    }

    try {
        if (navigator.permissions && navigator.permissions.query) {
            const status = await navigator.permissions.query({ name: 'microphone' });
            if (status.state === 'denied') {
                throw new Error('Microphone access is blocked. Allow it in your browser settings.');
            }
        }
    } catch (err) {
        // Ignore permission query errors; we will still attempt getUserMedia.
    }

    return navigator.mediaDevices.getUserMedia({
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
        }
    });
}

async function requestMicPermission() {
    const stream = await ensureMicAccess();
    stream.getTracks().forEach((t) => t.stop());
}


function showMicStatus(message, isError = false) {
    micStatus.textContent = message;
    if (isError) {
        micStatus.classList.add('text-red-300');
    } else {
        micStatus.classList.remove('text-red-300');
    }
}

// --- VOICE TO TEXT ---
micBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micBtn.classList.remove('bg-red-500');
        micBtn.classList.add('bg-brand-secondary');
        micStatus.textContent = 'Processing...';
        return;
    }

    try {
        showMicStatus('Requesting microphone...');
        if (!mediaRecorder) {
            await requestMicPermission();
        }
        const stream = await ensureMicAccess();
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = () => {
            recordedBlob = new Blob(audioChunks, { type: 'audio/webm' });
            generateSttBtn.classList.remove('hidden');
            micStatus.textContent = 'Transcribing...';
            stream.getTracks().forEach((t) => t.stop());
            transcribeRecording();
        };

        mediaRecorder.start();
        micBtn.classList.add('bg-red-500');
        micBtn.classList.remove('bg-brand-secondary');
        micStatus.textContent = 'Recording...';
        generateSttBtn.classList.add('hidden');
    } catch (err) {
        console.error('Mic Error:', err);
        showMicStatus(err.message || 'Microphone access denied.', true);
        alert(err.message || 'Microphone access denied.');
    }
});

generateSttBtn.addEventListener('click', () => {
    transcribeRecording();
});

async function transcribeRecording() {
    if (!recordedBlob || isTranscribing) return;
    isTranscribing = true;

    generateSttBtn.disabled = true;
    generateSttBtn.textContent = 'Transcribing...';
    sttOutput.textContent = 'AI is thinking...';
    sttOutput.classList.add('italic', 'text-white/10');

    try {
        const base64Audio = await blobToWavBase64(recordedBlob);
        const data = await postJson(sttUrl, {
            audio_base64: base64Audio,
            mime_type: 'audio/wav',
        });

        const text = (data.text || '').trim();
        sttOutput.textContent = text || 'No speech detected.';
        sttOutput.classList.remove('italic', 'text-white/10');
        micStatus.textContent = text ? 'Transcription Ready' : 'No Speech Detected';
    } catch (error) {
        console.error('STT Error:', error);
        sttOutput.textContent = 'Error transcribing audio.';
        micStatus.textContent = 'Transcription Failed';
    } finally {
        isTranscribing = false;
        generateSttBtn.disabled = false;
        generateSttBtn.textContent = 'Generate Text';
    }
}

copyBtn.addEventListener('click', () => {
    const text = sttOutput.textContent;
    if (text && !text.includes('Your transcription')) {
        navigator.clipboard.writeText(text);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => (copyBtn.textContent = 'Copy Text'), 2000);
    }
});

// --- HELPERS ---
async function postJson(url, payload) {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(payload),
    });

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : {};

    if (!response.ok) {
        const message = data.error || 'Request failed.';
        const details = data.details ? ` ${data.details}` : '';
        throw new Error((message + details).trim());
    }

    return data;
}

async function blobToWavBase64(blob) {
    if (blob.type === 'audio/wav') {
        return readBlobAsBase64(blob);
    }
    const arrayBuffer = await blob.arrayBuffer();
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const audioCtx = new AudioCtx();
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
    const wavBytes = audioBufferToWav(audioBuffer);
    await audioCtx.close();
    return bytesToBase64(wavBytes);
}

function audioBufferToWav(audioBuffer) {
    const numChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const samples = interleaveChannels(audioBuffer, numChannels);
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * 2, true);
    view.setUint16(32, numChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i += 1) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        offset += 2;
    }

    return new Uint8Array(buffer);
}

function interleaveChannels(audioBuffer, numChannels) {
    if (numChannels === 1) {
        return audioBuffer.getChannelData(0);
    }
    const length = audioBuffer.length * numChannels;
    const result = new Float32Array(length);
    let index = 0;
    for (let i = 0; i < audioBuffer.length; i += 1) {
        for (let channel = 0; channel < numChannels; channel += 1) {
            result[index++] = audioBuffer.getChannelData(channel)[i];
        }
    }
    return result;
}

function bytesToBase64(bytes) {
    let binary = '';
    for (let i = 0; i < bytes.length; i += 1) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i += 1) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

function readBlobAsBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result || '';
            const base64 = result.toString().split(',')[1] || '';
            resolve(base64);
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });
}

function getCookie(name) {
    const value = document.cookie.split('; ').find((row) => row.startsWith(name + '='));
    return value ? decodeURIComponent(value.split('=')[1]) : '';
}

function createAudioUrl(base64, mimeType, sampleRate) {
    const lower = (mimeType || '').toLowerCase();
    if (lower.startsWith('audio/') && !lower.includes('pcm')) {
        const blob = base64ToBlob(base64, lower);
        return URL.createObjectURL(blob);
    }
    return pcmToWav(base64, sampleRate);
}

function base64ToBlob(base64, mimeType) {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i += 1) {
        bytes[i] = binary.charCodeAt(i);
    }
    return new Blob([bytes], { type: mimeType || 'application/octet-stream' });
}

function pcmToWav(pcmBase64, sampleRate = 24000) {
    const pcmData = atob(pcmBase64);
    const buffer = new ArrayBuffer(44 + pcmData.length);
    const view = new DataView(buffer);
    const writeString = (view, offset, string) => {
        for (let i = 0; i < string.length; i += 1) view.setUint8(offset + i, string.charCodeAt(i));
    };
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + pcmData.length, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, pcmData.length, true);
    for (let i = 0; i < pcmData.length; i += 1) view.setUint8(44 + i, pcmData.charCodeAt(i));
    return URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }));
}
