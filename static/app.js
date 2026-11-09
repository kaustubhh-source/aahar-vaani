/**
 * AAHAR-VAANI (आहार-वाणी) // ULTRA-PREMIUM SPA CONTROLLER
 * Sovereign Indic Speech & ICMR-NIN Metabolic Telemetry
 * Web Audio 16kHz WAV Capture • Live HTML5 Canvas Visualizer • Timbre v3.0 Player
 */

// Global State
let activePersona = "Devansh"; // "Devansh" or "Shivani"
let isRecording = false;
let mediaStream = null;
let audioContext = null;
let analyserNode = null;
let scriptProcessor = null;
let audioChunks = [];
let visualizerAnimationId = null;
let currentReport = null;

// Audio Player State
const audioElement = document.getElementById("coachAudioElement");
let isAudioPlaying = false;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  initAudioPlayerListeners();
  await checkSystemHealth();
  
  // Run initial analysis on default canteen meal
  await analyzeCurrentMeal(false);
});


// ============================================================================
// 1. SYSTEM HEALTH & TELEMETRY
// ============================================================================
async function checkSystemHealth() {
  const t0 = performance.now();
  try {
    const res = await fetch("/api/health");
    const t1 = performance.now();
    const latency = Math.round(t1 - t0);
    
    if (res.ok) {
      const data = await res.json();
      const latencyElem = document.getElementById("telemetryLatency");
      const lexiconElem = document.getElementById("telemetryLexicon");
      if (latencyElem) latencyElem.textContent = `${latency}ms`;
      if (lexiconElem) lexiconElem.textContent = data.lexicon_items_count || "60";
    }
  } catch (err) {
    console.warn("API health check fallback:", err);
  }
}


// ============================================================================
// 2. PERSONA SELECTOR (DEVANSH vs SHIVANI)
// ============================================================================
function setPersona(persona) {
  activePersona = persona;
  const devanshBtn = document.getElementById("personaDevanshBtn");
  const shivaniBtn = document.getElementById("personaShivaniBtn");
  const coachPersonaBadge = document.getElementById("coachPersonaBadge");

  if (persona === "Devansh") {
    devanshBtn.className = "flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10";
    shivaniBtn.className = "flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all text-slate-400 hover:text-slate-200 hover:bg-white/5";
    if (coachPersonaBadge) {
      coachPersonaBadge.textContent = "Devansh (Youth Dost)";
      coachPersonaBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold";
    }
  } else {
    shivaniBtn.className = "flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-lg shadow-amber-500/10";
    devanshBtn.className = "flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all text-slate-400 hover:text-slate-200 hover:bg-white/5";
    if (coachPersonaBadge) {
      coachPersonaBadge.textContent = "Shivani (Family Care)";
      coachPersonaBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold";
    }
  }

  // If report exists, update coach script & re-synthesize speech
  if (currentReport) {
    updateCoachScriptBox();
    triggerCoachSynthesis();
  }
}


// ============================================================================
// 3. VOICE RECORDING & LIVE HTML5 CANVAS AUDIO VISUALIZER
// ============================================================================
async function toggleRecording() {
  const micBtn = document.getElementById("recordBtn");
  const micLabel = document.getElementById("micLabel");
  const micIcon = document.getElementById("micIcon");
  const statusElem = document.getElementById("recordingStatus");
  const placeholder = document.getElementById("visualizerPlaceholder");

  if (!isRecording) {
    // --- START RECORDING ---
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = audioContext.createMediaStreamSource(mediaStream);

      // Create AnalyserNode for Visualizer
      analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 256;
      source.connect(analyserNode);

      // 16kHz PCM Buffer Collection
      audioChunks = [];
      scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
      scriptProcessor.onaudioprocess = (e) => {
        if (!isRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        audioChunks.push(new Float32Array(inputData));
      };

      source.connect(scriptProcessor);
      scriptProcessor.connect(audioContext.destination);

      isRecording = true;
      micBtn.className = "w-24 h-24 rounded-full mic-btn-recording z-10 flex flex-col items-center justify-center text-white cursor-pointer select-none focus:outline-none";
      micLabel.textContent = "STOP RECORDING";
      statusElem.innerHTML = `<span class="text-rose-400 font-bold font-mono">● LISTENING TO INDIC SPEECH (16kHz)</span> — Speak naturally...`;
      if (placeholder) placeholder.style.display = "none";

      startCanvasVisualizer();
    } catch (err) {
      console.error("Microphone access error:", err);
      statusElem.innerHTML = `<span class="text-rose-400 font-semibold">Microphone permission denied.</span> Allow mic access in browser or type below.`;
    }
  } else {
    // --- STOP RECORDING ---
    isRecording = false;
    micBtn.className = "w-24 h-24 rounded-full mic-btn-idle z-10 flex flex-col items-center justify-center text-white cursor-pointer select-none focus:outline-none";
    micLabel.textContent = "TAP TO SPEAK";
    statusElem.innerHTML = `<span class="text-emerald-400 font-mono">Encoding 16kHz Mono WAV & sending to Prisma v3.0...</span>`;

    // Stop streams & visualizer
    if (visualizerAnimationId) cancelAnimationFrame(visualizerAnimationId);
    stopCanvasVisualizer();

    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
    }
    if (scriptProcessor) {
      scriptProcessor.disconnect();
    }
    if (audioContext && audioContext.state !== "closed") {
      audioContext.close();
    }

    // Encode to 16kHz 16-bit Mono WAV
    const wavBlob = encodeWAV(flattenFloat32(audioChunks), 16000);
    await sendAudioToBackend(wavBlob);
  }
}

// Visualizer Loop
function startCanvasVisualizer() {
  const canvas = document.getElementById("visualizerCanvas");
  if (!canvas || !analyserNode) return;
  const ctx = canvas.getContext("2d");
  const bufferLength = analyserNode.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function draw() {
    if (!isRecording) return;
    visualizerAnimationId = requestAnimationFrame(draw);
    analyserNode.getByteFrequencyData(dataArray);

    ctx.fillStyle = "rgba(8, 9, 13, 0.4)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 2.2;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
      // Vibrant Emerald Neon gradient
      const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
      gradient.addColorStop(0, "rgba(5, 150, 105, 0.2)");
      gradient.addColorStop(0.5, "rgba(16, 185, 129, 0.8)");
      gradient.addColorStop(1, "#34d399");

      ctx.fillStyle = gradient;
      ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
      x += barWidth;
    }
  }

  draw();
}

function stopCanvasVisualizer() {
  const canvas = document.getElementById("visualizerCanvas");
  const placeholder = document.getElementById("visualizerPlaceholder");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (placeholder) placeholder.style.display = "block";
}

// 16kHz 16-bit Mono WAV Encoder
function encodeWAV(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // Linear PCM
  view.setUint16(22, 1, true); // Mono (1 channel)
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // Byte rate (SampleRate * NumChannels * BitsPerSample/8)
  view.setUint16(32, 2, true); // Block align
  view.setUint16(34, 16, true); // 16-bit
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  // Write PCM audio samples
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

function flattenFloat32(chunks) {
  let totalLen = 0;
  for (const c of chunks) totalLen += c.length;
  const result = new Float32Array(totalLen);
  let offset = 0;
  for (const c of chunks) {
    result.set(c, offset);
    offset += c.length;
  }
  return result;
}

// Send Audio to FastAPI /api/transcribe
async function sendAudioToBackend(wavBlob) {
  const statusElem = document.getElementById("recordingStatus");
  const transcriptBox = document.getElementById("transcriptBox");

  try {
    const formData = new FormData();
    formData.append("file", wavBlob, "live_speech.wav");
    formData.append("language_code", "hi-IN");

    const res = await fetch("/api/transcribe", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`STT failed with HTTP ${res.status}`);
    }

    const data = await res.json();
    if (data.transcript) {
      transcriptBox.value = data.transcript;
      statusElem.innerHTML = `<span class="text-emerald-400 font-semibold font-mono">Recognized with ${Math.round((data.confidence || 0.95) * 100)}% confidence!</span>`;
      await analyzeCurrentMeal(true);
    } else {
      statusElem.innerHTML = `<span class="text-amber-400">Speech transcribed as empty. Try speaking again or select a preset.</span>`;
    }
  } catch (err) {
    console.error("Transcription error:", err);
    statusElem.innerHTML = `<span class="text-rose-400 font-semibold">Transcription uplink failed.</span> Using fallback simulation.`;
  }
}


// ============================================================================
// 4. MEAL ANALYSIS & BENTO METABOLIC DASHBOARD RENDERING
// ============================================================================
async function analyzeCurrentMeal(autoPlayAudio = false) {
  const transcriptBox = document.getElementById("transcriptBox");
  const mealText = transcriptBox.value.trim();
  if (!mealText) return;

  const analyzeBtn = document.getElementById("analyzeBtn");
  const originalBtnHTML = analyzeBtn.innerHTML;
  analyzeBtn.innerHTML = `<span>⏳</span> Analyzing ICMR Telemetry...`;
  analyzeBtn.disabled = true;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: mealText,
        persona: activePersona,
        language: "hi-IN",
      }),
    });

    if (!res.ok) {
      throw new Error(`Analyze API returned status ${res.status}`);
    }

    const data = await res.json();
    currentReport = data;
    renderMetabolicDashboard(data);
    updateCoachScriptBox();

    // Trigger Timbre v3.0 Voice Synthesis
    await triggerCoachSynthesis(autoPlayAudio);

  } catch (err) {
    console.error("Meal analysis error:", err);
  } finally {
    analyzeBtn.innerHTML = originalBtnHTML;
    analyzeBtn.disabled = false;
    if (window.lucide) window.lucide.createIcons();
  }
}

function renderMetabolicDashboard(data) {
  const totals = data.totals || {};
  const rc = data.reality_check || {};

  // 1. Context Multiplier Banner
  const contextTitle = document.getElementById("contextTitle");
  const contextDesc = document.getElementById("contextDesc");
  const multiplierBadge = document.getElementById("multiplierBadge");

  const ctxName = (data.detected_context || "HOME").toUpperCase();
  if (contextTitle) contextTitle.textContent = `${ctxName} CONTEXT APPLIED`;
  if (contextDesc) contextDesc.textContent = data.context_description || "";

  if (multiplierBadge && data.context_multipliers) {
    const fatMult = data.context_multipliers.oil_fat_multiplier || 1.0;
    const carbMult = data.context_multipliers.carbs_multiplier || 1.0;
    multiplierBadge.textContent = `${fatMult}x Fat • ${carbMult}x Carbs`;
  }

  // 2. 4 Bento Metric Cards
  const calElem = document.getElementById("metricCalories");
  const proElem = document.getElementById("metricProtein");
  const carbElem = document.getElementById("metricCarbs");
  const fatElem = document.getElementById("metricFat");
  const fiberElem = document.getElementById("metricFiber");
  const ratioElem = document.getElementById("metricRatio");

  if (calElem) calElem.textContent = Math.round(totals.calories || 0);
  if (proElem) proElem.innerHTML = `${(totals.protein_g || 0).toFixed(1)}<span class="text-sm font-sans text-slate-400 ml-0.5">g</span>`;
  if (carbElem) carbElem.innerHTML = `${(totals.carbs_g || 0).toFixed(1)}<span class="text-sm font-sans text-slate-400 ml-0.5">g</span>`;
  if (fatElem) fatElem.innerHTML = `${(totals.fat_g || 0).toFixed(1)}<span class="text-sm font-sans text-slate-400 ml-0.5">g</span>`;
  if (fiberElem) fiberElem.textContent = `${(totals.fiber_g || 0).toFixed(1)}g`;

  const carbRatio = rc.carb_to_protein_ratio || 0;
  if (ratioElem) ratioElem.textContent = `${carbRatio.toFixed(1)}:1`;

  // 3. ICMR Risk Radar Banner
  const riskBanner = document.getElementById("riskBanner");
  const riskTitle = document.getElementById("riskTitle");
  const riskBadge = document.getElementById("riskBadge");
  const riskDesc = document.getElementById("riskDesc");
  const flagsContainer = document.getElementById("sugarAcidityFlags");

  const spikeRisk = rc.glycemic_spike_risk || "Low";

  if (spikeRisk === "Severe") {
    riskBanner.className = "p-4 rounded-2xl glass-panel border border-rose-500/40 bg-rose-950/25 space-y-2";
    riskTitle.textContent = "SEVERE GLYCEMIC SPIKE RISK";
    riskTitle.className = "text-sm font-bold text-rose-300 uppercase tracking-wide";
    riskBadge.textContent = "ACUTE INSULIN SURGE";
    riskBadge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-rose-500/25 text-rose-300 border border-rose-500/50";
    riskDesc.textContent = `Extreme Carb-to-Protein imbalance (${carbRatio.toFixed(1)}:1 vs ICMR benchmark ≤ 2.5:1). This meal will trigger an acute post-prandial glucose spike followed by reactive fatigue and brain fog within 90 minutes.`;
  } else if (spikeRisk === "Moderate") {
    riskBanner.className = "p-4 rounded-2xl glass-panel border border-amber-500/40 bg-amber-950/25 space-y-2";
    riskTitle.textContent = "MODERATE GLYCEMIC SPIKE RISK";
    riskTitle.className = "text-sm font-bold text-amber-300 uppercase tracking-wide";
    riskBadge.textContent = "ELEVATED GLYCEMIC LOAD";
    riskBadge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-amber-500/25 text-amber-300 border border-amber-500/50";
    riskDesc.textContent = `Carb heavy profile (${carbRatio.toFixed(1)}:1 Carb:Protein). Adding bioavailable fiber or plant protein will stabilize blood glucose.`;
  } else {
    riskBanner.className = "p-4 rounded-2xl glass-panel border border-emerald-500/40 bg-emerald-950/25 space-y-2";
    riskTitle.textContent = "BALANCED METABOLIC PROFILE";
    riskTitle.className = "text-sm font-bold text-emerald-300 uppercase tracking-wide";
    riskBadge.textContent = "SAFE GLYCEMIC INDEX";
    riskBadge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/25 text-emerald-300 border border-emerald-500/50";
    riskDesc.textContent = "Excellent macronutrient distribution adhering closely to ICMR-NIN 2024 dietary guidelines.";
  }

  // Hidden Sugars & Acidity Flags
  if (flagsContainer) {
    flagsContainer.innerHTML = "";
    const sugarFlags = rc.hidden_sugar_flags || [];
    const acidityFlags = rc.acidity_flags || [];

    sugarFlags.forEach((flag) => {
      flagsContainer.innerHTML += `
        <span class="text-[11px] px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1 font-mono">
          <i data-lucide="alert-circle" class="w-3 h-3"></i> ${flag}
        </span>
      `;
    });

    acidityFlags.forEach((flag) => {
      flagsContainer.innerHTML += `
        <span class="text-[11px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-mono">
          <i data-lucide="flame" class="w-3 h-3"></i> ${flag}
        </span>
      `;
    });
  }

  // 4. Itemized Culinary Entities Table
  const tbody = document.getElementById("itemsTableBody");
  const countBadge = document.getElementById("itemsCountBadge");
  const items = data.items || [];

  if (countBadge) countBadge.textContent = `${items.length} Items Detected`;
  if (tbody) {
    tbody.innerHTML = "";
    items.forEach((item) => {
      const spikeBadgeClass =
        item.glycemic_spike_risk === "Severe"
          ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
          : item.glycemic_spike_risk === "Moderate"
          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";

      tbody.innerHTML += `
        <tr>
          <td class="py-2.5 font-medium text-slate-100">${item.name_en} <span class="text-slate-500 font-normal">${item.name_mr || item.name_hi || ""}</span></td>
          <td class="py-2.5 font-mono">${item.quantity} ${item.unit} (${item.total_grams}g)</td>
          <td class="py-2.5 font-mono text-white font-semibold">${item.calories.toFixed(1)} kcal</td>
          <td class="py-2.5 font-mono text-emerald-400">${item.protein_g.toFixed(1)}g</td>
          <td class="py-2.5 font-mono text-rose-300">${item.carbs_g.toFixed(1)}g</td>
          <td class="py-2.5 font-mono text-cyan-300">${item.fat_g.toFixed(1)}g</td>
          <td class="py-2.5"><span class="px-1.5 py-0.5 rounded font-mono text-[10px] ${spikeBadgeClass} border">${item.glycemic_index} (${item.glycemic_spike_risk})</span></td>
        </tr>
      `;
    });
  }
}


// ============================================================================
// 5. TIMBRE v3.0 VOICE SYNTHESIS & CUSTOM AUDIO PLAYER
// ============================================================================
function updateCoachScriptBox() {
  if (!currentReport) return;
  const scriptBox = document.getElementById("coachScriptBox");
  if (!scriptBox) return;

  const spoken =
    activePersona === "Devansh"
      ? currentReport.spoken_summaries?.devansh
      : currentReport.spoken_summaries?.shivani;

  if (spoken) {
    // Format expressive audio tags with glowing badges
    let formatted = spoken
      .replace(/<excited>/g, '<span class="tag-excited">&lt;excited&gt;</span>')
      .replace(/<\/excited>/g, '<span class="tag-excited">&lt;/excited&gt;</span>')
      .replace(/<laugh>/g, '<span class="tag-laugh">&lt;laugh&gt;</span>')
      .replace(/<\/laugh>/g, '<span class="tag-laugh">&lt;/laugh&gt;</span>')
      .replace(/<sigh>/g, '<span class="tag-sigh">&lt;sigh&gt;</span>')
      .replace(/<\/sigh>/g, '<span class="tag-sigh">&lt;/sigh&gt;</span>');

    scriptBox.innerHTML = `"${formatted}"`;
  }
}

async function triggerCoachSynthesis(autoPlay = false) {
  if (!currentReport) return;
  const statusElem = document.getElementById("audioStatusText");
  const playBtn = document.getElementById("audioPlayBtn");

  if (statusElem) statusElem.textContent = "SYNTHESIZING TIMBRE v3.0 VOICE...";

  try {
    const res = await fetch("/api/coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        persona: activePersona,
        language: "hi-IN",
        meal_text: document.getElementById("transcriptBox").value.trim(),
      }),
    });

    if (!res.ok) throw new Error("Coach TTS failed");
    const data = await res.json();

    if (data.audio_url) {
      audioElement.src = data.audio_url;
      audioElement.load();
      if (statusElem) statusElem.textContent = "VOICE LOADED (TIMBRE v3.0)";

      if (autoPlay) {
        audioElement.play().then(() => {
          setAudioPlayingState(true);
        }).catch((e) => console.log("Autoplay blocked by browser:", e));
      }
    }
  } catch (err) {
    console.error("Coach synthesis error:", err);
    if (statusElem) statusElem.textContent = "TTS PLAYBACK READY";
  }
}

// Audio Player Listeners & Controls
function initAudioPlayerListeners() {
  if (!audioElement) return;

  audioElement.addEventListener("timeupdate", () => {
    const current = audioElement.currentTime;
    const duration = audioElement.duration || 1;
    const progress = (current / duration) * 100;

    const scrubber = document.getElementById("audioScrubber");
    const currentTimeElem = document.getElementById("audioCurrentTime");
    const totalTimeElem = document.getElementById("audioTotalTime");

    if (scrubber) scrubber.value = progress;
    if (currentTimeElem) currentTimeElem.textContent = formatTime(current);
    if (totalTimeElem && !isNaN(duration)) totalTimeElem.textContent = formatTime(duration);
  });

  audioElement.addEventListener("ended", () => {
    setAudioPlayingState(false);
    const scrubber = document.getElementById("audioScrubber");
    if (scrubber) scrubber.value = 0;
  });

  audioElement.addEventListener("loadedmetadata", () => {
    const totalTimeElem = document.getElementById("audioTotalTime");
    if (totalTimeElem && !isNaN(audioElement.duration)) {
      totalTimeElem.textContent = formatTime(audioElement.duration);
    }
  });
}

function toggleAudioPlayback() {
  if (!audioElement.src) {
    triggerCoachSynthesis(true);
    return;
  }

  if (audioElement.paused) {
    audioElement.play();
    setAudioPlayingState(true);
  } else {
    audioElement.pause();
    setAudioPlayingState(false);
  }
}

function setAudioPlayingState(playing) {
  isAudioPlaying = playing;
  const playIcon = document.getElementById("audioPlayIcon");
  const statusElem = document.getElementById("audioStatusText");

  if (playIcon) {
    playIcon.setAttribute("data-lucide", playing ? "pause" : "play");
    if (window.lucide) window.lucide.createIcons();
  }
  if (statusElem) {
    statusElem.textContent = playing ? "PLAYING INDIC AUDIO" : "READY FOR PLAYBACK";
  }
}

function onScrubAudio(val) {
  if (!audioElement || !audioElement.duration) return;
  audioElement.currentTime = (val / 100) * audioElement.duration;
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m < 10 ? "0" : ""}${m}:${s < 10 ? "0" : ""}${s}`;
}


// ============================================================================
// 6. PRESET LOADERS & HELPERS
// ============================================================================
function loadPreset(phrase) {
  const box = document.getElementById("transcriptBox");
  if (box) {
    box.value = phrase;
    analyzeCurrentMeal(false);
  }
}

function clearTranscript() {
  const box = document.getElementById("transcriptBox");
  if (box) {
    box.value = "";
    box.focus();
  }
}
