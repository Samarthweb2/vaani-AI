// ============================================================
// Vaani AI — Official X (Twitter) Web Client Script
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const tweetInput = document.getElementById("tweet-input");
  const postSubmitBtn = document.getElementById("post-submit-btn");
  const charRing = document.getElementById("char-ring");
  const tweetFeed = document.getElementById("tweet-feed");
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeIcon = document.getElementById("theme-icon");
  const htmlRoot = document.documentElement;

  const RING_CIRCUMFERENCE = 56.55; // 2 * PI * 9

  // ============================================================
  // Theme Switching (Default: Light / Clean White Page)
  // ============================================================
  const savedTheme = localStorage.getItem("x-theme") || "light";
  setTheme(savedTheme);

  themeToggleBtn.addEventListener("click", () => {
    const current = htmlRoot.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    setTheme(next);
  });

  function setTheme(theme) {
    htmlRoot.setAttribute("data-theme", theme);
    localStorage.setItem("x-theme", theme);
    themeIcon.textContent = theme === "light" ? "🌙" : "☀️";
  }

  // ============================================================
  // Character Ring Progress Counter
  // ============================================================
  function updateCharRing() {
    const textLen = tweetInput.value.length;
    const progress = Math.min(1, textLen / 280);
    const offset = RING_CIRCUMFERENCE - (progress * RING_CIRCUMFERENCE);
    charRing.style.strokeDashoffset = offset;

    if (textLen > 280) {
      charRing.style.stroke = "#f4212e";
      postSubmitBtn.disabled = true;
    } else if (textLen > 240) {
      charRing.style.stroke = "#ffd400";
      postSubmitBtn.disabled = false;
    } else {
      charRing.style.stroke = "#1d9bf0";
      postSubmitBtn.disabled = textLen === 0;
    }
  }

  tweetInput.addEventListener("input", updateCharRing);
  updateCharRing();

  // Focus textarea when clicking "Post" in left nav
  document.getElementById("nav-post-btn").addEventListener("click", () => {
    tweetInput.focus();
    tweetInput.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  // Enter to submit (Ctrl+Enter or Meta+Enter)
  tweetInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handlePostTweet();
    }
  });

  postSubmitBtn.addEventListener("click", handlePostTweet);

  // ============================================================
  // Seed Timeline with authentic demo tweet thread
  // ============================================================
  seedInitialTimeline();

  function seedInitialTimeline() {
    appendTweetThread({
      userAuthor: "hackathon_judge",
      userHandle: "@hackathon_judge",
      userInitial: "J",
      userText: "@vaaniai what makes your architecture different from generic AI bots?",
      timeAgo: "12m",
      botChunks: [
        "Vaani AI runs pure Hugging Face open-weights models (Qwen2.5) with local PEFT LoRA adapters instead of external APIs. It tracks every mention in SQLite to eliminate duplicate replies and chunk-formats answers strictly to 280 characters.",
        "Crucially, it continuously records every solved query into an Alpaca-format instruction dataset (data/dataset.jsonl), making it self-improving through automated retraining! (2/2)"
      ],
      replyCount: 3,
      retweetCount: 14,
      likeCount: 42
    });
  }

  // ============================================================
  // Post Tweet & Render Thread
  // ============================================================
  async function handlePostTweet() {
    const rawText = tweetInput.value.trim();
    if (!rawText) return;

    postSubmitBtn.disabled = true;
    postSubmitBtn.textContent = "Posting...";

    // Thread Container
    const threadBlock = document.createElement("div");
    threadBlock.className = "tweet-thread-block";

    // 1. User's initiating tweet
    const userRow = document.createElement("div");
    userRow.className = "tweet-row";
    userRow.innerHTML = `
      <div class="tweet-avatar-col">
        <div class="avatar-img avatar-user">S</div>
        <div class="thread-connector-line"></div>
      </div>
      <div class="tweet-main-col">
        <div class="tweet-header-row">
          <span class="t-author-name">sam ☕</span>
          <span class="t-author-handle">@samarthsharma44</span>
          <span class="t-dot">·</span>
          <span class="t-time">just now</span>
        </div>
        <div class="tweet-text">${escapeHtml(rawText)}</div>
        <div class="tweet-action-bar">
          <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.01-8.183-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 6.01 6.138 6.01l.613-.01 1.248.69 4.25 2.35v-2.03l.613-.34c2.164-1.2 3.509-3.48 3.509-5.95 0-3.38-2.738-6.13-6.13-6.13h-4.236z"/></svg> <span>0</span></button>
          <button class="t-action-btn btn-retweet"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg> <span>0</span></button>
          <button class="t-action-btn btn-like"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-2.415.11-4.3 2.15-4.3 4.69 0 3.48 3.09 6.27 7.749 10.49l1.247 1.13 1.248-1.13c4.658-4.22 7.748-7.01 7.748-10.49 0-2.54-1.885-4.58-4.3-4.69z"/></svg> <span>0</span></button>
          <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/></svg> <span>1</span></button>
        </div>
      </div>
    `;

    // 2. Thinking indicator
    const thinkingRow = document.createElement("div");
    thinkingRow.className = "thinking-row";
    thinkingRow.id = "active-thinking";
    thinkingRow.innerHTML = `
      <div class="spinner-circle"></div>
      <span>Vaani AI is solving query with Hugging Face + LoRA...</span>
    `;

    threadBlock.appendChild(userRow);
    threadBlock.appendChild(thinkingRow);
    tweetFeed.prepend(threadBlock);

    try {
      const response = await fetch("/api/mention", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText, author: "samarthsharma44" })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      // Remove thinking indicator
      thinkingRow.remove();

      // 3. Render each response chunk as connected thread tweet
      data.chunks.forEach((chunk, idx) => {
        const isLast = idx === data.chunks.length - 1;
        const botRow = document.createElement("div");
        botRow.className = "tweet-row";

        const partBadge = data.chunks.length > 1 ? `<span class="t-part-badge">${idx + 1}/${data.chunks.length}</span>` : "";

        botRow.innerHTML = `
          <div class="tweet-avatar-col">
            <div class="avatar-img avatar-vaani">V</div>
            ${!isLast ? '<div class="thread-connector-line"></div>' : ''}
          </div>
          <div class="tweet-main-col">
            <div class="tweet-header-row">
              <span class="t-author-name">Vaani AI</span>
              <svg class="t-verified-icon" viewBox="0 0 22 22"><path fill="#1d9bf0" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.136 2.136 5.445-5.446 1.302 1.293-6.747 6.747z"/></svg>
              <span class="t-author-handle">@vaaniai</span>
              <span class="t-dot">·</span>
              <span class="t-time">just now</span>
              ${partBadge}
            </div>
            <div class="tweet-text">${escapeHtml(chunk)}</div>
            <div class="tweet-action-bar">
              <button class="t-action-btn btn-reply"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.01-8.183-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 6.01 6.138 6.01l.613-.01 1.248.69 4.25 2.35v-2.03l.613-.34c2.164-1.2 3.509-3.48 3.509-5.95 0-3.38-2.738-6.13-6.13-6.13h-4.236z"/></svg> <span>1</span></button>
              <button class="t-action-btn btn-retweet"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg> <span>3</span></button>
              <button class="t-action-btn btn-like"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-2.415.11-4.3 2.15-4.3 4.69 0 3.48 3.09 6.27 7.749 10.49l1.247 1.13 1.248-1.13c4.658-4.22 7.748-7.01 7.748-10.49 0-2.54-1.885-4.58-4.3-4.69z"/></svg> <span>12</span></button>
              <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/></svg> <span>184</span></button>
            </div>
          </div>
        `;

        threadBlock.appendChild(botRow);
      });

      // Clear input
      tweetInput.value = "@vaaniai ";
      updateCharRing();

    } catch (err) {
      thinkingRow.innerHTML = `<span style="color: #f4212e;">Error: ${err.message}</span>`;
    } finally {
      postSubmitBtn.disabled = false;
      postSubmitBtn.textContent = "Post";
      tweetInput.focus();
    }
  }

  function appendTweetThread(opts) {
    const threadBlock = document.createElement("div");
    threadBlock.className = "tweet-thread-block";

    const userRow = document.createElement("div");
    userRow.className = "tweet-row";
    userRow.innerHTML = `
      <div class="tweet-avatar-col">
        <div class="avatar-img avatar-user">${opts.userInitial}</div>
        <div class="thread-connector-line"></div>
      </div>
      <div class="tweet-main-col">
        <div class="tweet-header-row">
          <span class="t-author-name">${opts.userAuthor}</span>
          <span class="t-author-handle">${opts.userHandle}</span>
          <span class="t-dot">·</span>
          <span class="t-time">${opts.timeAgo}</span>
        </div>
        <div class="tweet-text">${escapeHtml(opts.userText)}</div>
        <div class="tweet-action-bar">
          <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.01-8.183-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 6.01 6.138 6.01l.613-.01 1.248.69 4.25 2.35v-2.03l.613-.34c2.164-1.2 3.509-3.48 3.509-5.95 0-3.38-2.738-6.13-6.13-6.13h-4.236z"/></svg> <span>${opts.replyCount}</span></button>
          <button class="t-action-btn btn-retweet"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg> <span>${opts.retweetCount}</span></button>
          <button class="t-action-btn btn-like"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-2.415.11-4.3 2.15-4.3 4.69 0 3.48 3.09 6.27 7.749 10.49l1.247 1.13 1.248-1.13c4.658-4.22 7.748-7.01 7.748-10.49 0-2.54-1.885-4.58-4.3-4.69z"/></svg> <span>${opts.likeCount}</span></button>
          <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/></svg> <span>842</span></button>
        </div>
      </div>
    `;
    threadBlock.appendChild(userRow);

    opts.botChunks.forEach((chunk, idx) => {
      const isLast = idx === opts.botChunks.length - 1;
      const botRow = document.createElement("div");
      botRow.className = "tweet-row";
      const partBadge = opts.botChunks.length > 1 ? `<span class="t-part-badge">${idx + 1}/${opts.botChunks.length}</span>` : "";

      botRow.innerHTML = `
        <div class="tweet-avatar-col">
          <div class="avatar-img avatar-vaani">V</div>
          ${!isLast ? '<div class="thread-connector-line"></div>' : ''}
        </div>
        <div class="tweet-main-col">
          <div class="tweet-header-row">
            <span class="t-author-name">Vaani AI</span>
            <svg class="t-verified-icon" viewBox="0 0 22 22"><path fill="#1d9bf0" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.136 2.136 5.445-5.446 1.302 1.293-6.747 6.747z"/></svg>
            <span class="t-author-handle">@vaaniai</span>
            <span class="t-dot">·</span>
            <span class="t-time">${opts.timeAgo}</span>
            ${partBadge}
          </div>
          <div class="tweet-text">${escapeHtml(chunk)}</div>
          <div class="tweet-action-bar">
            <button class="t-action-btn btn-reply"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.01-8.183-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 6.01 6.138 6.01l.613-.01 1.248.69 4.25 2.35v-2.03l.613-.34c2.164-1.2 3.509-3.48 3.509-5.95 0-3.38-2.738-6.13-6.13-6.13h-4.236z"/></svg> <span>1</span></button>
            <button class="t-action-btn btn-retweet"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg> <span>5</span></button>
            <button class="t-action-btn btn-like"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-2.415.11-4.3 2.15-4.3 4.69 0 3.48 3.09 6.27 7.749 10.49l1.247 1.13 1.248-1.13c4.658-4.22 7.748-7.01 7.748-10.49 0-2.54-1.885-4.58-4.3-4.69z"/></svg> <span>28</span></button>
            <button class="t-action-btn"><svg viewBox="0 0 24 24" class="t-action-icon"><path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/></svg> <span>620</span></button>
          </div>
        </div>
      `;
      threadBlock.appendChild(botRow);
    });

    tweetFeed.appendChild(threadBlock);
  }

  // Interactive like and retweet toggle
  tweetFeed.addEventListener("click", (e) => {
    const likeBtn = e.target.closest(".btn-like");
    if (likeBtn) {
      const span = likeBtn.querySelector("span");
      const icon = likeBtn.querySelector(".t-action-icon");
      const isLiked = likeBtn.classList.toggle("liked");
      let count = parseInt(span.textContent, 10) || 0;
      span.textContent = isLiked ? count + 1 : Math.max(0, count - 1);
      likeBtn.style.color = isLiked ? "#f91880" : "";
      icon.style.fill = isLiked ? "#f91880" : "currentColor";
    }

    const retweetBtn = e.target.closest(".btn-retweet");
    if (retweetBtn) {
      const span = retweetBtn.querySelector("span");
      const isRt = retweetBtn.classList.toggle("retweeted");
      let count = parseInt(span.textContent, 10) || 0;
      span.textContent = isRt ? count + 1 : Math.max(0, count - 1);
      retweetBtn.style.color = isRt ? "#00ba7c" : "";
    }
  });

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
});
