/**
 * Aahar-Vaani (आहार-वाणी) Production Frontend Application
 * Handles:
 * 1. 16kHz Mono WAV Web Audio recording for Gnani Prisma v3.0 native compatibility
 * 2. 1-Tap foolproof demo presets (Canteen, Hostel Mess, Family Home)
 * 3. Asynchronous API interactions (/api/transcribe, /api/analyze, /api/coach)
 * 4. SVG Circular macro rings and dynamic ICMR reality check rendering
 * 5. Custom audio coach player with persona toggling (Devansh vs Shivani)
 */

let audioContext = null;
let mediaStream = null;
let audioInput = null;
let scriptProcessor = null;
let audioBuffers = [];
let isRecording = false;

let currentAnalysis = null;
let currentPersona = "Devansh";
let currentAudioElement = new Audio();
let isAudioPlaying = false;

// --- Initialize App on Load ---
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkBackendHealth();
  // Run default initial analysis on Preset 1 for immediate live visuals
  selectPreset("Subah do plate poha aur ek cutting chai li canteen mein");
});

function setupEventListeners() {
  const micBtn = document.getElementById("micBtn");
  if (micBtn) {
    micBtn.addEventListener("click", toggleRecording);
  }

  const analyzeBtn = document.getElementById("analyzeBtn");
  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", () => {
      const text = document.getElementById("transcriptInput").value;
      if (text && text.trim()) {
        runAnalysis(text.trim());
      }
    });
  }

  const playPauseBtn = document.getElementById("playPauseBtn");
  if (playPauseBtn) {
    playPauseBtn.addEventListener("click", toggleAudioPlayback);
  }

  currentAudioElement.addEventListener("ended", () => {
    setAudioPlayingState(false);
  });

  currentAudioElement.addEventListener("pause", () => {
    setAudioPlayingState(false);
  });
}

// --- Health Check ---
async function checkBackendHealth() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      const statusPill = document.getElementById("systemStatusText");
      if (statusPill) {
        statusPill.textContent = `Prisma & Timbre Online (${data.boosted_keyterms_count} Keyterms)`;
      }
    }
  } catch (e) {
    console.warn("Backend health check failed:", e);
  }
}

// --- Web Audio 16kHz Mono WAV Recorder ---
async function toggleRecording() {
  const micBtn = document.getElementById("micBtn");
  const micStatus = document.getElementById("micStatusText");

  if (!isRecording) {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioInput = audioContext.createMediaStreamSource(mediaStream);
      
      // Buffer size 4096, 1 input channel, 1 output channel
      scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
      audioBuffers = [];

      scriptProcessor.onaudioprocess = (e) => {
        if (!isRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        audioBuffers.push(new Float32Array(inputData));
      };

      audioInput.connect(scriptProcessor);
      scriptProcessor.connect(audioContext.destination);

      isRecording = true;
      micBtn.classList.add("recording");
      micStatus.textContent = "Listening to Indic speech (16kHz)... Click to stop.";
    } catch (err) {
      console.error("Microphone access failed:", err);
      micStatus.textContent = "Mic access blocked. Please allow permissions or use 1-Tap Presets.";
    }
  } else {
    // Stop recording
    isRecording = false;
    micBtn.classList.remove("recording");
    micStatus.textContent = "Encoding 16kHz Mono WAV & sending to Prisma v3.0...";

    if (scriptProcessor) scriptProcessor.disconnect();
    if (audioInput) audioInput.disconnect();
    if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());

    // Encode to 16kHz WAV
    const wavBlob = encodeWAV(audioBuffers, 16000);
    sendAudioToSTT(wavBlob);
  }
}

// Helper to encode Float32Array PCM samples to 16-bit Mono WAV
function encodeWAV(buffers, sampleRate) {
  let totalLength = buffers.reduce((acc, b) => acc + b.length, 0);
  let merged = new Float32Array(totalLength);
  let offset = 0;
  for (let b of buffers) {
    merged.set(b, offset);
    offset += b.length;
  }

  let buffer = new ArrayBuffer(44 + merged.length * 2);
  let view = new DataView(buffer);

  // RIFF Chunk
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + merged.length * 2, true);
  writeString(view, 8, 'WAVE');
  
  // fmt Chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);        // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true);         // AudioFormat (1 for PCM)
  view.setUint16(22, 1, true);         // NumChannels (1 for Mono)
  view.setUint32(24, sampleRate, true);// SampleRate
  view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
  view.setUint16(32, 2, true);         // BlockAlign
  view.setUint16(34, 16, true);        // BitsPerSample (16 bits)

  // data Chunk
  writeString(view, 36, 'data');
  view.setUint32(40, merged.length * 2, true);

  // Write 16-bit PCM samples
  let index = 44;
  for (let i = 0; i < merged.length; i++) {
    let s = Math.max(-1, Math.min(1, merged[i]));
    view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    index += 2;
  }

  return new Blob([view], { type: 'audio/wav' });
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

async function sendAudioToSTT(wavBlob) {
  const micStatus = document.getElementById("micStatusText");
  const transcriptInput = document.getElementById("transcriptInput");

  try {
    const formData = new FormData();
    formData.append("file", wavBlob, "voice_log_16k.wav");
    formData.append("language_code", "hi-IN");

    const res = await fetch("/api/transcribe", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      transcriptInput.value = data.transcript;
      micStatus.textContent = `Recognized with ${Math.round(data.confidence * 100)}% confidence!`;
      runAnalysis(data.transcript);
    } else {
      micStatus.textContent = "STT Error. Try typing or use 1-Tap presets below.";
    }
  } catch (e) {
    console.error("STT network error:", e);
    micStatus.textContent = "Network error connecting to Prisma v3.0.";
  }
}

// --- 1-Tap Presets ---
window.selectPreset = function(text) {
  const transcriptInput = document.getElementById("transcriptInput");
  if (transcriptInput) {
    transcriptInput.value = text;
  }
  runAnalysis(text);
};

// --- Analysis Pipeline ---
async function runAnalysis(text) {
  const loadingOverlay = document.getElementById("analysisLoading");
  if (loadingOverlay) loadingOverlay.style.display = "block";

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, persona: currentPersona })
    });

    if (res.ok) {
      currentAnalysis = await res.json();
      renderAnalysisResults(currentAnalysis);
      // Trigger voice coach for the active persona
      fetchCoachAudio(currentPersona);
    }
  } catch (e) {
    console.error("Analysis failed:", e);
  } finally {
    if (loadingOverlay) loadingOverlay.style.display = "none";
  }
}

// --- Render Visualizer Results ---
function renderAnalysisResults(data) {
  // 1. Preparation Context Badge
  const ctxElem = document.getElementById("contextBadge");
  const ctxDesc = document.getElementById("contextDescription");
  if (ctxElem) {
    const ctx = data.detected_context || "home";
    let badgeClass = "badge-home";
    let label = "Home Cooked (1.0x Oil)";

    if (ctx === "canteen_thela") {
      badgeClass = "badge-thela";
      label = "Canteen / Tapri (1.5x Reheated Oil, 1.3x Carbs)";
    } else if (ctx === "mess") {
      badgeClass = "badge-mess";
      label = "Hostel Mess (1.25x Oil, Lower Protein)";
    }

    ctxElem.className = `context-tag ${badgeClass}`;
    ctxElem.textContent = label;
  }
  if (ctxDesc) {
    ctxDesc.textContent = data.context_description || "";
  }

  // 2. Glycemic Spike Risk Badge
  const spikeElem = document.getElementById("spikeRiskBadge");
  if (spikeElem) {
    const risk = data.reality_check?.glycemic_spike_risk || "Low";
    spikeElem.className = `spike-badge spike-${risk.toLowerCase()}`;
    spikeElem.innerHTML = risk === "Severe" 
      ? `🔥 Severe Spike Risk` 
      : (risk === "Moderate" ? `⚠️ Moderate Spike Risk` : `✅ Low Spike Risk`);
  }

  // 3. Macro Circular Progress Rings
  const totals = data.totals || {};
  updateRing("ringCal", totals.calories || 0, 650, "ringCalVal", "kcal");
  updateRing("ringProt", totals.protein_g || 0, 25, "ringProtVal", "g");
  updateRing("ringCarb", totals.carbs_g || 0, 65, "ringCarbVal", "g");
  updateRing("ringFat", totals.fat_g || 0, 20, "ringFatVal", "g");

  // 4. ICMR Reality Check Alert Box
  const rc = data.reality_check || {};
  const ratioText = document.getElementById("icmrRatioText");
  const ratioBarProt = document.getElementById("ratioBarProt");
  const ratioBarCarb = document.getElementById("ratioBarCarb");

  if (ratioText) {
    ratioText.textContent = rc.ratio_status || "Evaluating...";
  }

  const cToP = rc.carb_to_protein_ratio || 5.0;
  // Calculate relative proportion for the visual meter
  const protShare = Math.max(5, Math.min(50, Math.round((1 / (cToP + 1)) * 100)));
  const carbShare = 100 - protShare;
  if (ratioBarProt) ratioBarProt.style.width = `${protShare}%`;
  if (ratioBarCarb) ratioBarCarb.style.width = `${carbShare}%`;

  // 5. Warnings and Flags
  const flagsContainer = document.getElementById("flagsContainer");
  if (flagsContainer) {
    flagsContainer.innerHTML = "";
    const sugarFlags = rc.hidden_sugar_flags || [];
    const acidityFlags = rc.acidity_flags || [];
    const allFlags = [...sugarFlags, ...acidityFlags];

    if (allFlags.length === 0) {
      flagsContainer.innerHTML = `<div style="font-size:0.8rem; color:#a1a1aa;">No acute acidity or hidden sugar alerts detected.</div>`;
    } else {
      for (let flag of allFlags) {
        const div = document.createElement("div");
        div.className = "flag-card";
        div.textContent = flag;
        flagsContainer.appendChild(div);
      }
    }
  }

  // 6. Budget Protein & Healthy Swaps
  const swapsContainer = document.getElementById("swapsContainer");
  if (swapsContainer) {
    swapsContainer.innerHTML = "";
    const swaps = rc.budget_protein_swaps || [];
    for (let swap of swaps) {
      const div = document.createElement("div");
      div.className = "swap-card";
      div.innerHTML = `<span>⚡</span><span>${swap}</span>`;
      swapsContainer.appendChild(div);
    }
  }

  // 7. Itemized Food Table
  const tableBody = document.getElementById("itemsTableBody");
  if (tableBody) {
    tableBody.innerHTML = "";
    const items = data.items || [];
    for (let item of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${item.name_en}</strong><div style="font-size:0.75rem; color:#71717a;">${item.name_mr || item.name_hi}</div></td>
        <td>${item.quantity} ${item.unit} (${Math.round(item.total_grams)}g)</td>
        <td>${Math.round(item.calories)} kcal</td>
        <td>${item.protein_g}g</td>
        <td>${item.carbs_g}g</td>
        <td>${item.fat_g}g</td>
        <td><span style="font-size:0.75rem; color:${item.glycemic_spike_risk === 'Severe' ? '#f43f5e' : '#10b981'}; font-weight:700;">${item.glycemic_index}</span></td>
      `;
      tableBody.appendChild(tr);
    }
  }
}

// Helper to update SVG Circle Progress
function updateRing(circleId, currentVal, targetVal, labelId, unit) {
  const circle = document.getElementById(circleId);
  const label = document.getElementById(labelId);
  if (!circle || !label) return;

  label.textContent = `${Math.round(currentVal)}${unit}`;
  // SVG circle circumference: 2 * PI * r = 2 * 3.14159 * 32 ≈ 201.06
  const circumference = 201.06;
  const ratio = Math.min(1.5, currentVal / targetVal);
  const offset = circumference - (circumference * Math.min(1.0, ratio));
  circle.style.strokeDashoffset = offset;
}

// --- Voice Coach & Timbre v3.0 Audio ---
window.setPersona = function(personaName) {
  currentPersona = personaName;
  document.querySelectorAll(".persona-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.persona === personaName);
  });
  if (currentAnalysis) {
    fetchCoachAudio(personaName);
  }
};

async function fetchCoachAudio(personaName) {
  const coachScript = document.getElementById("coachScriptText");
  const scriptText = personaName.toLowerCase() === "devansh"
    ? currentAnalysis?.spoken_summaries?.devansh
    : currentAnalysis?.spoken_summaries?.shivani;

  if (coachScript) {
    coachScript.textContent = scriptText ? `"${scriptText}"` : "Synthesizing Timbre v3.0 coach advice...";
  }

  try {
    const res = await fetch("/api/coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: scriptText,
        persona: personaName,
        language: "hi-IN"
      })
    });

    if (res.ok) {
      const data = await res.json();
      currentAudioElement.src = data.audio_url;
      // Auto-play the synthesized feedback
      playCoachAudio();
    }
  } catch (e) {
    console.error("TTS fetch error:", e);
  }
}

function playCoachAudio() {
  currentAudioElement.play()
    .then(() => setAudioPlayingState(true))
    .catch(err => {
      // Browser autoplay policy might require a click
      console.log("Autoplay prevented:", err);
      setAudioPlayingState(false);
    });
}

function toggleAudioPlayback() {
  if (isAudioPlaying) {
    currentAudioElement.pause();
    setAudioPlayingState(false);
  } else {
    currentAudioElement.play()
      .then(() => setAudioPlayingState(true))
      .catch(e => console.error("Play failed:", e));
  }
}

function setAudioPlayingState(playing) {
  isAudioPlaying = playing;
  const playBtn = document.getElementById("playPauseBtn");
  const waveBars = document.querySelectorAll(".wave-bar");

  if (playBtn) {
    playBtn.textContent = playing ? "⏸" : "▶";
  }
  waveBars.forEach(bar => {
    bar.classList.toggle("playing", playing);
  });
}
