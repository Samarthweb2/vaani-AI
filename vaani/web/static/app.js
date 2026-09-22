// ============================================================
// Vaani AI — Web Interface Client Application
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const tweetInput = document.getElementById("tweet-input");
  const charCount = document.getElementById("char-count");
  const charProgress = document.getElementById("char-progress");
  const submitBtn = document.getElementById("submit-tweet-btn");
  const btnSpinner = document.getElementById("btn-spinner");
  const btnText = submitBtn.querySelector(".btn-text");
  const timelineFeed = document.getElementById("timeline-feed");
  const clearFeedBtn = document.getElementById("clear-feed-btn");
  const authorSelect = document.getElementById("author-select");
  const authorAvatar = document.getElementById("current-author-avatar");

  // Telemetry elements
  const chipModel = document.getElementById("chip-model");
  const chipLora = document.getElementById("chip-lora");
  const chipDataset = document.getElementById("chip-dataset");
  const mModelId = document.getElementById("m-model-id");
  const mBaseSize = document.getElementById("m-base-size");
  const mLiveSamples = document.getElementById("m-live-samples");
  const dTotalCount = document.getElementById("d-total-count");
  const dBaseCount = document.getElementById("d-base-count");
  const datasetRecords = document.getElementById("dataset-records");

  const CIRCLE_CIRCUMFERENCE = 69.11; // 2 * PI * 11

  // ============================================================
  // Tab Switching Logic
  // ============================================================
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const targetTab = tab.getAttribute("data-tab");
      document.getElementById("tab-timeline").style.display = targetTab === "timeline" ? "flex" : "none";
      document.getElementById("tab-dataset").style.display = targetTab === "dataset" ? "block" : "none";
      document.getElementById("tab-architecture").style.display = targetTab === "architecture" ? "block" : "none";

      if (targetTab === "dataset") {
        fetchDatasetStream();
      }
    });
  });

  // ============================================================
  // Author Selector
  // ============================================================
  authorSelect.addEventListener("change", () => {
    const val = authorSelect.value;
    authorAvatar.textContent = val.charAt(0).toUpperCase();
  });

  // ============================================================
  // Character Counter & Ring Progress
  // ============================================================
  function updateCharCounter() {
    const length = tweetInput.value.length;
    charCount.textContent = `${length} / 280`;

    const percentage = Math.min(1, length / 280);
    const offset = CIRCLE_CIRCUMFERENCE - (percentage * CIRCLE_CIRCUMFERENCE);
    charProgress.style.strokeDashoffset = offset;

    if (length > 280) {
      charProgress.style.stroke = "var(--accent-red)";
      charCount.style.color = "var(--accent-red)";
    } else if (length > 240) {
      charProgress.style.stroke = "var(--accent-yellow)";
      charCount.style.color = "var(--accent-yellow)";
    } else {
      charProgress.style.stroke = "var(--twitter-blue)";
      charCount.style.color = "var(--text-muted)";
    }
  }

  tweetInput.addEventListener("input", updateCharCounter);
  updateCharCounter();

  // Quick Prompt Chips
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      tweetInput.value = prompt;
      tweetInput.focus();
      updateCharCounter();
    });
  });

  // Keyboard shortcut: Ctrl + Enter
  tweetInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSendMention();
    }
  });

  submitBtn.addEventListener("click", handleSendMention);
  clearFeedBtn.addEventListener("click", () => {
    timelineFeed.innerHTML = "";
  });

  // ============================================================
  // Fetch Runtime Telemetry
  // ============================================================
  async function fetchTelemetry() {
    try {
      const res = await fetch("/api/stats");
      if (!res.ok) return;
      const data = await res.json();

      chipModel.textContent = data.hf_model_id.split("/").pop();
      mModelId.textContent = data.hf_model_id;
      
      if (data.lora_active) {
        chipLora.textContent = "checkpoints/vaani-lora (Active)";
      } else {
        chipLora.textContent = "Base Model Only";
      }

      chipDataset.textContent = `Dolly 15k (${data.base_dataset_count.toLocaleString()} samples)`;
      mBaseSize.textContent = `${data.base_dataset_count.toLocaleString()} (${data.base_dataset_size_mb} MB)`;
      mLiveSamples.textContent = data.live_dataset_count;
      dTotalCount.textContent = data.live_dataset_count;
      dBaseCount.textContent = data.base_dataset_count.toLocaleString();
    } catch (err) {
      console.warn("Could not fetch telemetry:", err);
    }
  }

  // ============================================================
  // Fetch Dataset Inspector Stream
  // ============================================================
  async function fetchDatasetStream() {
    try {
      datasetRecords.innerHTML = "<p style='color: var(--text-muted);'>Loading dataset entries...</p>";
      const res = await fetch("/api/dataset?limit=20");
      if (!res.ok) return;
      const data = await res.json();

      if (!data.samples || data.samples.length === 0) {
        datasetRecords.innerHTML = "<p style='color: var(--text-muted);'>No interactions logged yet. Send a mention to generate training pairs!</p>";
        return;
      }

      datasetRecords.innerHTML = "";
      data.samples.forEach((sample, idx) => {
        const card = document.createElement("div");
        card.className = "json-record-card";
        card.textContent = JSON.stringify(sample, null, 2);
        datasetRecords.appendChild(card);
      });
    } catch (err) {
      datasetRecords.innerHTML = `<p style='color: var(--accent-red);'>Error loading dataset: ${err.message}</p>`;
    }
  }

  // ============================================================
  // Send Mention & Render Thread
  // ============================================================
  async function handleSendMention() {
    const rawText = tweetInput.value.trim();
    if (!rawText) return;

    const author = authorSelect.value;
    const authorInitial = author.charAt(0).toUpperCase();

    // 1. Lock UI
    submitBtn.disabled = true;
    btnSpinner.style.display = "inline-block";
    btnText.textContent = "Generating...";

    // 2. Create placeholder thread container
    const threadContainer = document.createElement("div");
    threadContainer.className = "thread-card-container";

    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // User's initiating tweet
    const userTweetHtml = `
      <div class="tweet-card">
        <div class="tweet-avatar-wrap">
          <div class="user-avatar-circle">${authorInitial}</div>
          <div class="thread-line-connector"></div>
        </div>
        <div class="tweet-content-wrap">
          <div class="tweet-meta-row">
            <span class="tweet-display-name">${author}</span>
            <span class="tweet-username">@${author}</span>
            <span class="tweet-dot-sep">·</span>
            <span class="tweet-time">${nowStr}</span>
          </div>
          <div class="tweet-body">${escapeHtml(rawText)}</div>
        </div>
      </div>
    `;

    // Thinking placeholder for Vaani AI
    const placeholderBotHtml = `
      <div class="tweet-card" id="thinking-card">
        <div class="tweet-avatar-wrap">
          <div class="user-avatar-circle vaani-avatar">V</div>
        </div>
        <div class="tweet-content-wrap">
          <div class="tweet-meta-row">
            <span class="tweet-display-name">Vaani AI</span>
            <span class="verified-badge">✓</span>
            <span class="tweet-username">@vaaniai</span>
            <span class="tweet-dot-sep">·</span>
            <span class="tweet-time">just now</span>
          </div>
          <div class="tweet-body" style="color: var(--accent-cyan); display: flex; align-items: center; gap: 8px;">
            <span class="btn-spinner" style="display: inline-block; border-color: rgba(0, 242, 254, 0.3); border-top-color: var(--accent-cyan);"></span>
            <span>Vaani AI is running Hugging Face + LoRA inference...</span>
          </div>
        </div>
      </div>
    `;

    threadContainer.innerHTML = userTweetHtml + placeholderBotHtml;
    timelineFeed.prepend(threadContainer);

    try {
      const response = await fetch("/api/mention", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText, author: author })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const result = await response.json();

      // Remove thinking placeholder
      const thinkingCard = threadContainer.querySelector("#thinking-card");
      if (thinkingCard) thinkingCard.remove();

      // Render each response chunk as connected thread tweets
      result.chunks.forEach((chunk, index) => {
        const isLast = index === result.chunks.length - 1;
        const chunkCard = document.createElement("div");
        chunkCard.className = "tweet-card";

        chunkCard.innerHTML = `
          <div class="tweet-avatar-wrap">
            <div class="user-avatar-circle vaani-avatar">V</div>
            ${!isLast ? '<div class="thread-line-connector"></div>' : ''}
          </div>
          <div class="tweet-content-wrap">
            <div class="tweet-meta-row">
              <span class="tweet-display-name">Vaani AI</span>
              <span class="verified-badge" title="Verified Model">✓</span>
              <span class="tweet-username">@vaaniai</span>
              <span class="tweet-dot-sep">·</span>
              <span class="tweet-time">just now</span>
              <span class="tweet-chunk-pill">${index + 1}/${result.chunks.length} · ${chunk.length} chars</span>
            </div>
            <div class="tweet-body">${escapeHtml(chunk)}</div>
            <div class="tweet-actions-bar">
              <button class="action-btn" title="Reply">💬 Reply</button>
              <button class="action-btn" title="Retweet">🔁 Retweet</button>
              <button class="action-btn" title="Like">❤️ Like</button>
              <button class="action-btn copy-btn" title="Copy Tweet text" data-text="${escapeHtml(chunk)}">📋 Copy</button>
            </div>
          </div>
        `;

        threadContainer.appendChild(chunkCard);
      });

      // Attach copy listeners
      threadContainer.querySelectorAll(".copy-btn").forEach(copyBtn => {
        copyBtn.addEventListener("click", () => {
          const textToCopy = copyBtn.getAttribute("data-text");
          navigator.clipboard.writeText(textToCopy);
          const orig = copyBtn.textContent;
          copyBtn.textContent = "✓ Copied!";
          setTimeout(() => { copyBtn.textContent = orig; }, 1500);
        });
      });

      // Update counters
      fetchTelemetry();

      // Reset textarea
      tweetInput.value = "@vaaniai ";
      updateCharCounter();

    } catch (err) {
      const thinkingCard = threadContainer.querySelector("#thinking-card");
      if (thinkingCard) {
        thinkingCard.innerHTML = `
          <div class="tweet-avatar-wrap">
            <div class="user-avatar-circle vaani-avatar">V</div>
          </div>
          <div class="tweet-content-wrap">
            <div class="tweet-meta-row">
              <span class="tweet-display-name">Vaani AI</span>
              <span class="tweet-username">@vaaniai</span>
            </div>
            <div class="tweet-body" style="color: var(--accent-red);">
              ⚠️ Error solving query: ${err.message}
            </div>
          </div>
        `;
      }
    } finally {
      submitBtn.disabled = false;
      btnSpinner.style.display = "none";
      btnText.textContent = "Tweet @vaaniai";
      tweetInput.focus();
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Initial telemetry load
  fetchTelemetry();
});
