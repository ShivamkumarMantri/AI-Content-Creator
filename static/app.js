/**
 * VortexAI Studio — Client Application Script
 * Full SQLite Project Management & Automated Video Pipeline
 */

// Global Application State
const state = {
  activeView: 'dashboard',
  selectedStyle: 'cinematic',
  selectedDuration: 30,
  selectedPlatform: 'Instagram Reels',
  selectedFilter: 'all',
  currentPlan: null,
  isGeneratingPlan: false,
  isRenderingVideo: false,
  projects: [],
  activeModalProject: null,
  settings: {
    apiKey: localStorage.getItem('vortex_api_key') || '',
    model: localStorage.getItem('vortex_model') || 'local-engine'
  }
};

// DOM Helper
const $ = (id) => document.getElementById(id);

// Toast Notification Engine
function showToast(message, type = 'info', duration = 3500) {
  const container = $('toastContainer');
  if (!container) return;

  const icons = {
    success: '✓',
    info: 'ℹ',
    sparkle: '✨',
    error: '✕'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || '✨'}</div>
    <div class="toast-content">${escapeHtml(message)}</div>
    <button class="toast-close" aria-label="Close">&times;</button>
    <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  const dismiss = () => {
    toast.classList.add('toast-exit');
    setTimeout(() => {
      if (toast.parentNode === container) container.removeChild(toast);
    }, 300);
  };

  closeBtn.addEventListener('click', dismiss);
  container.appendChild(toast);

  setTimeout(dismiss, duration);
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initTemplateStarters();
  initFormControls();
  initProjectsView();
  initSettings();
  initProjectModal();
  fetchProjects();
  fetchStats();
});

// ==========================================================================
// View Routing & Navigation
// ==========================================================================

function initNavigation() {
  const navButtons = document.querySelectorAll('.nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // Action Buttons from Dashboard
  $('dashStartBtn')?.addEventListener('click', () => switchView('create'));
  $('dashViewProjectsBtn')?.addEventListener('click', () => switchView('projects'));
  $('dashSeeAllProjectsBtn')?.addEventListener('click', () => switchView('projects'));
  $('headerCreateBtn')?.addEventListener('click', () => switchView('create'));
  $('projectsNewVideoBtn')?.addEventListener('click', () => switchView('create'));
  $('restartCreationBtn')?.addEventListener('click', () => {
    resetVideoPlayerState();
    $('topic').focus();
  });

  // Mobile Menu Toggle
  $('sidebarToggle')?.addEventListener('click', () => {
    $('sidebar').classList.toggle('open');
  });

  // Modal Close
  $('modalCloseBtn')?.addEventListener('click', closeModal);
  $('projectModal')?.addEventListener('click', (e) => {
    if (e.target === $('projectModal')) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });
}

function switchView(viewId) {
  state.activeView = viewId;

  // Update Nav links
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-view') === viewId);
  });

  // Update Views
  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.remove('active');
  });

  const targetPanel = $(`view-${viewId}`);
  if (targetPanel) {
    targetPanel.classList.add('active');
  }

  // Update Breadcrumb Title
  const titles = {
    dashboard: 'Dashboard',
    create: 'Video Studio',
    projects: 'Projects Library',
    settings: 'Settings'
  };
  $('currentViewTitle').textContent = titles[viewId] || 'Dashboard';

  // Refresh lists if switching
  if (viewId === 'projects') {
    fetchProjects();
  } else if (viewId === 'dashboard') {
    fetchStats();
    fetchProjects();
  }

  // Close mobile sidebar
  $('sidebar')?.classList.remove('open');
}

// ==========================================================================
// Dashboard Stats & Quick Templates
// ==========================================================================

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    
    if ($('statVideosCount')) $('statVideosCount').textContent = data.total_projects || 0;
    if ($('statCompletedCount')) $('statCompletedCount').textContent = data.completed_videos || 0;
    if ($('statTotalDuration')) $('statTotalDuration').textContent = `${data.total_duration_seconds || 0}s`;
    if ($('projectCountBadge')) $('projectCountBadge').textContent = data.total_projects || 0;
  } catch (err) {
    console.error('Failed to fetch stats:', err);
  }
}

function initTemplateStarters() {
  const cards = document.querySelectorAll('.template-card');
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const topic = card.getAttribute('data-topic');
      const style = card.getAttribute('data-style');
      const duration = parseInt(card.getAttribute('data-duration'), 10);
      const platform = card.getAttribute('data-platform');

      // Populate Create View
      $('topic').value = topic;
      selectPlatform(platform);
      selectStyle(style);
      selectDuration(duration);

      switchView('create');
      $('generate').scrollIntoView({ behavior: 'smooth' });
      showToast(`Loaded prompt: "${topic}"`, 'sparkle');
    });
  });
}

// ==========================================================================
// Create Video Studio (Plan Generation & Rendering)
// ==========================================================================

function initFormControls() {
  // Platform pills
  document.querySelectorAll('.platform-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      selectPlatform(pill.getAttribute('data-platform'));
    });
  });

  // Style pills
  document.querySelectorAll('.style-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      selectStyle(pill.getAttribute('data-style'));
    });
  });

  // Duration pills
  document.querySelectorAll('.duration-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      selectDuration(parseInt(pill.getAttribute('data-duration'), 10));
    });
  });

  // Generate Plan CTA
  $('generate')?.addEventListener('click', handleGeneratePlan);

  // Render Video CTA
  $('createVideo')?.addEventListener('click', handleCreateVideo);

  // Copy buttons
  $('copyHookBtn')?.addEventListener('click', () => {
    const text = $('hookText').textContent;
    navigator.clipboard.writeText(text).then(() => {
      $('copyHookBtn').textContent = 'Copied!';
      showToast('Opening hook copied to clipboard!', 'info');
      setTimeout(() => { $('copyHookBtn').textContent = 'Copy'; }, 2000);
    });
  });

  $('copyScriptBtn')?.addEventListener('click', () => {
    const text = $('scriptText').textContent;
    navigator.clipboard.writeText(text).then(() => {
      $('copyScriptBtn').textContent = 'Copied!';
      showToast('Voiceover script copied to clipboard!', 'info');
      setTimeout(() => { $('copyScriptBtn').textContent = 'Copy'; }, 2000);
    });
  });
}

function selectPlatform(platformName) {
  state.selectedPlatform = platformName;
  document.querySelectorAll('.platform-pill').forEach(pill => {
    pill.classList.toggle('active', pill.getAttribute('data-platform') === platformName);
  });
}

function selectStyle(styleName) {
  state.selectedStyle = styleName;
  document.querySelectorAll('.style-pill').forEach(pill => {
    pill.classList.toggle('active', pill.getAttribute('data-style') === styleName);
  });
}

function selectDuration(dur) {
  state.selectedDuration = dur;
  document.querySelectorAll('.duration-pill').forEach(pill => {
    pill.classList.toggle('active', parseInt(pill.getAttribute('data-duration'), 10) === dur);
  });
}

function updateWorkflowTracker(activeStepNumber) {
  const steps = ['flowStepIdea', 'flowStepScript', 'flowStepScenes', 'flowStepVisuals', 'flowStepVoice', 'flowStepRender'];
  steps.forEach((id, index) => {
    const el = $(id);
    if (!el) return;
    if (index <= activeStepNumber) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  const connectors = document.querySelectorAll('.workflow-connector');
  connectors.forEach((conn, index) => {
    if (index < activeStepNumber) {
      conn.classList.add('active');
    } else {
      conn.classList.remove('active');
    }
  });
}

async function handleGeneratePlan() {
  const topic = $('topic').value.trim();
  if (!topic) {
    showStatus('Please enter a video topic or idea description.', true);
    $('topic').focus();
    return;
  }

  updateWorkflowTracker(1); // Idea -> Script
  state.isGeneratingPlan = true;
  showStatus('Synthesizing structured video plan and scene prompts...');
  $('generate').disabled = true;
  $('generate').innerHTML = `
    <div class="spinner-ring" style="width:16px;height:16px;margin:0;border-width:2px;"></div>
    <span>Analyzing & Structuring Script...</span>
  `;

  try {
    const payload = {
      topic: topic,
      style: state.selectedStyle,
      duration: state.selectedDuration,
      platform: state.selectedPlatform
    };

    if (state.settings.apiKey) {
      payload.api_key = state.settings.apiKey;
      payload.model = state.settings.model;
    }

    const res = await fetch('/api/generate-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to generate plan.');

    state.currentPlan = data;
    renderPlan(data);
    updateWorkflowTracker(4); // Scenes, Visuals, Voice ready
    showStatus('✓ Production plan created! Customize audio/captions below and click Create AI Video.');
    showToast('AI Video Production Plan generated!', 'success');
  } catch (err) {
    showStatus(`Error: ${err.message}`, true);
    showToast(`Plan generation failed: ${err.message}`, 'error');
    updateWorkflowTracker(0);
  } finally {
    state.isGeneratingPlan = false;
    $('generate').disabled = false;
    $('generate').innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <span>Generate AI Video →</span>
    `;
  }
}

function renderPlan(plan) {
  $('planTitle').textContent = plan.title || 'Untitled Plan';
  $('hookText').textContent = plan.hook || 'No hook provided.';
  $('scriptText').textContent = plan.script || (plan.scenes || []).map(s => s.narration).join(' ');
  $('planPlatformBadge').textContent = plan.platform || state.selectedPlatform;
  $('planStyleBadge').textContent = (plan.style || state.selectedStyle).toUpperCase();
  $('planDurationBadge').textContent = `${plan.total_duration || state.selectedDuration}s`;
  $('sceneCountTag').textContent = `${plan.scenes?.length || 0} Scenes`;

  const container = $('scenesList');
  container.innerHTML = (plan.scenes || []).map((scene, i) => `
    <div class="scene-item-card">
      <div class="scene-badge-col">
        <div class="scene-num-badge">${String(i + 1).padStart(2, '0')}</div>
        <span class="scene-dur-pill">${scene.duration || 5}s</span>
      </div>
      <div class="scene-content-col">
        <div class="scene-headline">${escapeHtml(scene.on_screen_text || `SCENE ${i + 1}`)}</div>
        <div class="scene-meta-row">
          <div class="narr"><b>Narration:</b> ${escapeHtml(scene.narration || '')}</div>
          <div class="vis"><b>Visual Direction:</b> ${escapeHtml(scene.visual || '')}</div>
        </div>
      </div>
    </div>
  `).join('');

  $('planContainer').classList.remove('hidden');
  $('planContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function handleCreateVideo() {
  if (!state.currentPlan || !state.currentPlan.scenes) {
    showStatus('Generate a content plan first.', true);
    return;
  }

  state.isRenderingVideo = true;
  $('createVideo').disabled = true;
  $('createVideo').innerHTML = `
    <div class="spinner-ring" style="width:16px;height:16px;margin:0;border-width:2px;"></div>
    <span>Rendering Video...</span>
  `;

  // Show live progress in Phone Mockup
  $('renderStateBadge').textContent = 'Rendering';
  $('renderStateBadge').className = 'render-badge rendering';
  $('videoPlaceholder').classList.add('hidden');
  $('videoPlayer').classList.add('hidden');
  $('renderProgressOverlay').classList.remove('hidden');
  $('videoActionsBar').classList.add('hidden');

  // Animated progress bar steps
  animateProgressSteps();

  try {
    const payload = {
      title: state.currentPlan.title,
      topic: $('topic') ? $('topic').value.trim() : state.currentPlan.title,
      hook: state.currentPlan.hook,
      script: state.currentPlan.script,
      platform: state.selectedPlatform,
      style: state.selectedStyle,
      scenes: state.currentPlan.scenes,
      enable_captions: $('toggleCaptions') ? $('toggleCaptions').checked : true,
      caption_style: $('captionStyleSelect') ? $('captionStyleSelect').value : 'hormozi',
      caption_position: $('captionPositionSelect') ? $('captionPositionSelect').value : 'bottom',
      enable_voiceover: $('toggleVoiceover') ? $('toggleVoiceover').checked : true,
      voice: $('voiceSelect') ? $('voiceSelect').value : 'male_deep',
      enable_music: $('toggleMusic') ? $('toggleMusic').checked : true
    };

    if (state.settings.apiKey) {
      payload.api_key = state.settings.apiKey;
    }

    const res = await fetch('/api/create-video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Video rendering failed.');

    // Video Ready!
    setTimeout(() => {
      displayRenderedVideo(data.video_url, state.currentPlan.title);
      updateWorkflowTracker(5); // All 6 steps complete (Render complete)
      fetchProjects();
      fetchStats();
      showToast('1080p MP4 Video ready! Saved to SQLite.', 'success');
    }, 600);

  } catch (err) {
    alert(`Rendering failed: ${err.message}`);
    resetVideoPlayerState();
  } finally {
    state.isRenderingVideo = false;
    $('createVideo').disabled = false;
    $('createVideo').innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Create AI Video</span>
    `;
  }
}

function animateProgressSteps() {
  const fill = $('progressBarFill');
  const stageTitle = $('progressStageTitle');
  const stageDesc = $('progressStageDesc');
  const step1 = $('stepCheck1');
  const step2 = $('stepCheck2');
  const step3 = $('stepCheck3');

  fill.style.width = '20%';
  stageTitle.textContent = 'Synthesizing Scenes...';
  stageDesc.textContent = 'Generating 1080x1920 layout and animated typography';
  step1.className = 'step-check done';
  step2.className = 'step-check active';
  step3.className = 'step-check';

  setTimeout(() => {
    fill.style.width = '60%';
    stageTitle.textContent = 'Generating Audio & Captions...';
    stageDesc.textContent = 'Synthesizing voiceover narration & ambient soundtrack';
    step2.className = 'step-check done';
    step3.className = 'step-check active';
  }, 1000);

  setTimeout(() => {
    fill.style.width = '88%';
    stageTitle.textContent = 'Encoding MP4 Video...';
    stageDesc.textContent = 'Multiplexing 30 FPS video with H.264 & AAC into SQLite';
  }, 2200);
}

function displayRenderedVideo(url, title) {
  $('renderStateBadge').textContent = 'Ready';
  $('renderStateBadge').className = 'render-badge ready';
  $('renderProgressOverlay').classList.add('hidden');
  
  const video = $('videoPlayer');
  video.src = url;
  video.classList.remove('hidden');
  video.load();
  video.play().catch(() => {});

  $('downloadVideoBtn').href = url;
  $('downloadVideoBtn').download = `${(title || 'ai_video').replace(/[^a-z0-9]/gi, '_').toLowerCase()}.mp4`;
  $('videoActionsBar').classList.remove('hidden');
}

function resetVideoPlayerState() {
  $('renderStateBadge').textContent = 'Idle';
  $('renderStateBadge').className = 'render-badge ready';
  $('renderProgressOverlay').classList.add('hidden');
  $('videoPlayer').classList.add('hidden');
  $('videoPlayer').pause();
  $('videoPlaceholder').classList.remove('hidden');
  $('videoActionsBar').classList.add('hidden');
}

function showStatus(msg, isError = false) {
  const el = $('status');
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? 'var(--accent-rose)' : '#a5b4fc';
}

// ==========================================================================
// Projects Management (SQLite CRUD)
// ==========================================================================

function initProjectsView() {
  $('projectSearch')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    renderProjectsGrid(query);
  });

  // Filter Pills
  document.querySelectorAll('.filter-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.selectedFilter = pill.getAttribute('data-filter');
      fetchProjects();
    });
  });
}

async function fetchProjects() {
  try {
    let url = '/api/projects';
    const params = new URLSearchParams();
    if (state.selectedFilter && state.selectedFilter !== 'all') {
      params.append('platform', state.selectedFilter);
    }
    const searchVal = $('projectSearch')?.value.trim();
    if (searchVal) {
      params.append('search', searchVal);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const res = await fetch(url);
    if (!res.ok) return;
    state.projects = await res.json();
    
    // Update badge count
    if ($('projectCountBadge')) $('projectCountBadge').textContent = state.projects.length;
    
    renderProjectsGrid();
    renderRecentProjectsDashboard();
  } catch (err) {
    console.error('Failed to fetch projects:', err);
  }
}

function renderProjectsGrid(searchQuery = '') {
  const grid = $('projectsGrid');
  if (!grid) return;

  const filtered = state.projects.filter(p => {
    if (!searchQuery) return true;
    return (p.title || '').toLowerCase().includes(searchQuery) ||
           (p.topic || '').toLowerCase().includes(searchQuery) ||
           (p.hook || '').toLowerCase().includes(searchQuery) ||
           (p.platform || '').toLowerCase().includes(searchQuery);
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-state-card" style="grid-column: 1 / -1;">
        <div class="empty-icon">📁</div>
        <h4>${searchQuery ? 'No matching projects found' : 'No projects saved in SQLite'}</h4>
        <p>${searchQuery ? 'Try another search query.' : 'Generate your first video in the Studio.'}</p>
        <button class="btn btn-primary btn-sm" onclick="switchView('create')">Create AI Video</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(p => {
    const statusClass = p.status === 'completed' ? 'badge-status-completed' : (p.status === 'draft' ? 'badge-status-draft' : 'badge-status-planned');
    return `
      <div class="project-card">
        <div class="project-thumb-box" onclick="openProjectModal('${p.id}')">
          <video src="${p.video_url || ''}#t=0.5" preload="metadata"></video>
          <div class="play-overlay-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          </div>
          <div class="project-duration-tag">${p.duration || 30}s</div>
        </div>
        <div class="project-body">
          <div class="flex-between" style="margin-bottom:6px;">
            <span class="${statusClass}">${escapeHtml(p.status || 'completed')}</span>
            <span class="badge-platform">${escapeHtml(p.platform || 'Shorts')}</span>
          </div>
          <div class="project-title" onclick="openProjectModal('${p.id}')">${escapeHtml(p.title || 'Untitled Video')}</div>
          <div class="project-hook">${escapeHtml(p.hook || p.topic || 'AI short-form video project.')}</div>
          <div class="project-card-footer">
            <span>📅 ${p.created_at || 'Recently'}</span>
            <div class="project-actions-row">
              <button class="icon-action-btn" onclick="openProjectModal('${p.id}')" title="Edit & Details">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
              </button>
              ${p.video_url ? `
                <a class="icon-action-btn" href="${p.video_url}" download title="Download MP4">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                </a>
              ` : ''}
              <button class="icon-action-btn delete" onclick="deleteProject('${p.id}')" title="Delete Project">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderRecentProjectsDashboard() {
  const container = $('dashRecentProjects');
  if (!container) return;

  if (state.projects.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card">
        <div class="empty-icon">🎬</div>
        <h4>No videos generated yet</h4>
        <p>Create your first AI video to populate your studio library.</p>
        <button class="btn btn-primary btn-sm" onclick="switchView('create')">Create AI Video</button>
      </div>
    `;
    return;
  }

  const recent = state.projects.slice(0, 3);
  container.innerHTML = `
    <div class="projects-grid">
      ${recent.map(p => `
        <div class="project-card">
          <div class="project-thumb-box" onclick="openProjectModal('${p.id}')">
            <video src="${p.video_url || ''}#t=0.5" preload="metadata"></video>
            <div class="play-overlay-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            </div>
            <div class="project-duration-tag">${p.duration || 30}s</div>
          </div>
          <div class="project-body">
            <div class="project-title" onclick="openProjectModal('${p.id}')">${escapeHtml(p.title || 'Untitled Video')}</div>
            <div class="project-card-footer">
              <span>${p.platform || 'Shorts'} • ${p.created_at || 'Recently'}</span>
              <button class="btn btn-ghost btn-sm" onclick="openProjectModal('${p.id}')">Details →</button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// ==========================================================================
// Project Details & Edit Modal Handlers
// ==========================================================================

function initProjectModal() {
  $('saveProjectEditsBtn')?.addEventListener('click', saveProjectEdits);
  $('loadProjectInStudioBtn')?.addEventListener('click', () => {
    if (state.activeModalProject) {
      loadProjectInStudio(state.activeModalProject);
    }
  });
  $('deleteProjectModalBtn')?.addEventListener('click', () => {
    if (state.activeModalProject) {
      deleteProject(state.activeModalProject.id);
      closeModal();
    }
  });
}

window.openProjectModal = async function(id) {
  let project = state.projects.find(p => p.id === id);
  if (!project) {
    try {
      const res = await fetch(`/api/projects/${id}`);
      if (res.ok) project = await res.json();
    } catch (e) {}
  }
  if (!project) return;

  state.activeModalProject = project;

  // Header & Status
  $('modalStatusBadge').textContent = (project.status || 'completed').toUpperCase();
  $('modalProjectHeader').textContent = project.title || 'Project Details';

  // Form Fields
  $('editProjectId').value = project.id;
  $('editProjectTitle').value = project.title || '';
  $('editProjectTopic').value = project.topic || '';
  $('editProjectPlatform').value = project.platform || 'Instagram Reels';
  $('editProjectStatus').value = project.status || 'completed';
  $('editProjectHook').value = project.hook || '';
  $('editProjectScript').value = project.script || '';

  // Metadata card
  $('modalMetaDuration').textContent = `${project.duration || 30}s`;
  $('modalMetaCreated').textContent = project.created_at || 'Recently';
  $('modalMetaScenes').textContent = `${project.scenes?.length || project.scene_count || 0} Scenes`;

  // Video Player Preview
  const video = $('modalVideoPlayer');
  if (project.video_url) {
    video.src = project.video_url;
    video.classList.remove('hidden');
    video.load();
    $('modalDownloadBtn').href = project.video_url;
    $('modalDownloadBtn').download = `${(project.title || 'video').replace(/[^a-z0-9]/gi, '_')}.mp4`;
    $('modalDownloadBtn').classList.remove('hidden');
  } else {
    video.classList.add('hidden');
    $('modalDownloadBtn').classList.add('hidden');
  }

  $('projectModal').classList.remove('hidden');
};

async function saveProjectEdits() {
  const id = $('editProjectId').value;
  if (!id) return;

  const payload = {
    title: $('editProjectTitle').value.trim() || 'Untitled Video',
    topic: $('editProjectTopic').value.trim(),
    platform: $('editProjectPlatform').value,
    status: $('editProjectStatus').value,
    hook: $('editProjectHook').value.trim(),
    script: $('editProjectScript').value.trim()
  };

  $('saveProjectEditsBtn').disabled = true;
  $('saveProjectEditsBtn').textContent = 'Saving...';

  try {
    const res = await fetch(`/api/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const updated = await res.json();
    if (!res.ok) throw new Error(updated.error || 'Failed to update project.');

    // Update local state
    const idx = state.projects.findIndex(p => p.id === id);
    if (idx !== -1) {
      state.projects[idx] = { ...state.projects[idx], ...updated };
    }
    state.activeModalProject = updated;

    $('modalProjectHeader').textContent = updated.title;
    $('modalStatusBadge').textContent = (updated.status || 'completed').toUpperCase();
    renderProjectsGrid();
    renderRecentProjectsDashboard();

    $('saveProjectEditsBtn').textContent = '✓ Saved!';
    showToast('Project updated successfully in SQLite!', 'success');
    setTimeout(() => {
      $('saveProjectEditsBtn').disabled = false;
      $('saveProjectEditsBtn').textContent = 'Save Changes';
    }, 1500);

  } catch (err) {
    alert(`Update failed: ${err.message}`);
    showToast(`Update failed: ${err.message}`, 'error');
    $('saveProjectEditsBtn').disabled = false;
    $('saveProjectEditsBtn').textContent = 'Save Changes';
  }
}

function loadProjectInStudio(project) {
  closeModal();

  $('topic').value = project.topic || project.title;
  selectPlatform(project.platform || 'Instagram Reels');
  selectStyle(project.style || 'cinematic');
  selectDuration(project.duration || 30);

  if (project.scenes && project.scenes.length > 0) {
    state.currentPlan = {
      title: project.title,
      hook: project.hook,
      script: project.script,
      platform: project.platform,
      style: project.style,
      total_duration: project.duration,
      scenes: project.scenes
    };
    renderPlan(state.currentPlan);
  }

  switchView('create');
  $('topic').scrollIntoView({ behavior: 'smooth' });
  showToast(`Loaded project "${project.title}" into Studio`, 'sparkle');
}

function closeModal() {
  const video = $('modalVideoPlayer');
  if (video) video.pause();
  $('projectModal').classList.add('hidden');
  state.activeModalProject = null;
}

window.deleteProject = async function(id) {
  if (!confirm('Are you sure you want to delete this video project from SQLite?')) return;
  try {
    const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete request failed.');

    state.projects = state.projects.filter(p => p.id !== id);
    renderProjectsGrid();
    renderRecentProjectsDashboard();
    fetchStats();
    showToast('Project removed from SQLite database.', 'info');
  } catch (err) {
    alert(`Failed to delete project: ${err.message}`);
    showToast(`Delete failed: ${err.message}`, 'error');
  }
};

// ==========================================================================
// Settings Management
// ==========================================================================

function initSettings() {
  const apiKeyInput = $('settingsApiKey');
  const modelSelect = $('settingsModel');

  if (apiKeyInput && state.settings.apiKey) {
    apiKeyInput.value = state.settings.apiKey;
  }
  if (modelSelect && state.settings.model) {
    modelSelect.value = state.settings.model;
  }

  $('saveSettingsBtn')?.addEventListener('click', () => {
    state.settings.apiKey = apiKeyInput.value.trim();
    state.settings.model = modelSelect.value;

    localStorage.setItem('vortex_api_key', state.settings.apiKey);
    localStorage.setItem('vortex_model', state.settings.model);

    updateModelStatusUI();
    showToast('Configuration preferences saved!', 'info');

    const statusEl = $('settingsSaveStatus');
    statusEl.textContent = '✓ Configuration saved!';
    setTimeout(() => { statusEl.textContent = ''; }, 3000);
  });
}

function updateModelStatusUI() {
  const statusEl = $('headerModelStatus');
  if (!statusEl) return;

  if (state.settings.apiKey && state.settings.model !== 'local-engine') {
    statusEl.textContent = `OpenAI (${state.settings.model})`;
  } else {
    statusEl.textContent = 'Local AI Engine';
  }
}

// Helper: Escape HTML
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[c]));
}
