const API_BASE = "/api";

const PRIORITY_TO_COLOR_ID = {
  1: "9",
  2: "10",
  3: "5",
  4: "6",
  5: "11",
};

const COLOR_ID_TO_PRIORITY = Object.fromEntries(
  Object.entries(PRIORITY_TO_COLOR_ID).map(([priority, colorId]) => [colorId, Number(priority)]),
);

const PRIORITY_COLORS = {
  5: "#d93025",
  4: "#f4511e",
  3: "#fbbc04",
  2: "#0b8043",
  1: "#039be5",
  none: "#7a869a",
};

const state = {
  auth: null,
  calendars: [],
  events: [],
  selectedCalendarId: "",
  loadingCalendars: false,
  loadingEvents: false,
  updatingEventIds: new Set(),
  collapsedGroups: new Set(),
  collapsedSubsections: new Set(),
  search: "",
  range: "all",
};

const els = {
  authStatus: document.querySelector("#authStatus"),
  authActionButton: document.querySelector("#authActionButton"),
  refreshButton: document.querySelector("#refreshButton"),
  calendarSelect: document.querySelector("#calendarSelect"),
  calendarMeta: document.querySelector("#calendarMeta"),
  eventSearch: document.querySelector("#eventSearch"),
  rangeFilter: document.querySelector("#rangeFilter"),
  viewKicker: document.querySelector("#viewKicker"),
  viewTitle: document.querySelector("#viewTitle"),
  eventCount: document.querySelector("#eventCount"),
  prioritizedCount: document.querySelector("#prioritizedCount"),
  unprioritizedCount: document.querySelector("#unprioritizedCount"),
  alert: document.querySelector("#alert"),
  eventGroups: document.querySelector("#eventGroups"),
  eventTemplate: document.querySelector("#eventTemplate"),
};

function encodeSegment(value) {
  return encodeURIComponent(value);
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      if (response.status >= 500) {
        message = "The server hit an unexpected error while contacting Google Calendar. Please try again.";
      }
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function priorityForEvent(event) {
  return COLOR_ID_TO_PRIORITY[event.color_id] ?? null;
}

function calendarLabel(calendar) {
  if (!calendar) {
    return "Calendar";
  }

  return calendar.summary || calendar.id;
}

function selectedCalendar() {
  return state.calendars.find((calendar) => calendar.id === state.selectedCalendarId) || null;
}

function setAlert(message = "") {
  els.alert.hidden = !message;
  els.alert.textContent = message;
}

function setLoadingBoard(message) {
  els.eventGroups.innerHTML = `
    <div class="priority-group">
      <div class="loading-state">
        <div class="loading-line"></div>
        <div class="loading-line"></div>
        <p>${message}</p>
      </div>
    </div>
  `;
}

function renderAuth() {
  const isAuthenticated = Boolean(state.auth?.is_authenticated);
  els.authActionButton.textContent = isAuthenticated ? "Sign out" : "Sign in with Google";
  els.authActionButton.classList.toggle("button-primary", !isAuthenticated);
  els.authActionButton.classList.toggle("button-ghost", isAuthenticated);
  els.authStatus.textContent = isAuthenticated ? "Signed in" : "Signed out";
}

function renderCalendarControls() {
  els.calendarSelect.disabled = !state.auth?.is_authenticated || state.loadingCalendars || state.calendars.length === 0;
  els.calendarSelect.innerHTML = "";

  if (state.calendars.length === 0) {
    const option = new Option(state.loadingCalendars ? "Loading calendars" : "No calendars loaded", "");
    els.calendarSelect.add(option);
  } else {
    state.calendars.forEach((calendar) => {
      const option = new Option(calendarLabel(calendar), calendar.id);
      option.selected = calendar.id === state.selectedCalendarId;
      els.calendarSelect.add(option);
    });
  }

  const calendar = selectedCalendar();
  if (!state.auth?.is_authenticated) {
    els.calendarMeta.textContent = "Not connected";
  } else if (state.loadingCalendars) {
    els.calendarMeta.textContent = "Loading";
  } else if (calendar) {
    const parts = [
      calendar.primary ? "Primary" : "",
      calendar.access_role ? `Access: ${calendar.access_role}` : "",
      calendar.time_zone || "",
    ].filter(Boolean);
    els.calendarMeta.textContent = parts.join(" / ") || calendar.id;
  } else {
    els.calendarMeta.textContent = "No calendar selected";
  }
}

function eventStartMillis(event) {
  const value = event.start?.date_time || event.start?.date;
  if (!value) {
    return Number.POSITIVE_INFINITY;
  }

  const date = new Date(event.start?.date ? `${value}T00:00:00` : value);
  return Number.isNaN(date.getTime()) ? Number.POSITIVE_INFINITY : date.getTime();
}

function eventMatchesRange(event) {
  if (state.range !== "upcoming") {
    return true;
  }

  const value = event.end?.date_time || event.start?.date_time || event.end?.date || event.start?.date;
  if (!value) {
    return true;
  }

  const date = new Date((event.end?.date || event.start?.date) ? `${value}T23:59:59` : value);
  return Number.isNaN(date.getTime()) || date.getTime() >= Date.now();
}

function eventEndMillis(event) {
  const value = event.end?.date_time || event.start?.date_time || event.end?.date || event.start?.date;
  if (!value) {
    return Number.POSITIVE_INFINITY;
  }

  const isAllDay = Boolean(event.end?.date || event.start?.date);
  const date = new Date(isAllDay ? `${value}T23:59:59` : value);
  return Number.isNaN(date.getTime()) ? Number.POSITIVE_INFINITY : date.getTime();
}

function isPastEvent(event) {
  return eventEndMillis(event) < Date.now();
}

function eventMatchesSearch(event) {
  if (!state.search) {
    return true;
  }

  const haystack = [
    event.summary,
    event.description,
    event.location,
    event.organizer_email,
    event.creator_email,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(state.search);
}

function filteredEvents() {
  return state.events.filter((event) => eventMatchesRange(event) && eventMatchesSearch(event));
}

function formatDateTime(value, allDay = false) {
  if (!value) {
    return "";
  }

  const date = new Date(allDay ? `${value}T00:00:00` : value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  if (allDay) {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date);
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatEventTime(event) {
  if (!event.start) {
    return "Time not set";
  }

  if (event.start.date) {
    return `${formatDateTime(event.start.date, true)} / All day`;
  }

  const start = formatDateTime(event.start.date_time);
  const end = event.end?.date_time
    ? new Intl.DateTimeFormat(undefined, {
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(event.end.date_time))
    : "";

  return end ? `${start} - ${end}` : start;
}

function renderStats(events) {
  const prioritized = events.filter((event) => priorityForEvent(event) !== null).length;
  els.eventCount.textContent = String(events.length);
  els.prioritizedCount.textContent = String(prioritized);
  els.unprioritizedCount.textContent = String(events.length - prioritized);
}

function renderShell() {
  renderAuth();
  renderCalendarControls();

  const calendar = selectedCalendar();
  els.viewTitle.textContent = calendar ? calendarLabel(calendar) : "Events";
  els.viewKicker.textContent = calendar?.time_zone || "Calendar";

  if (!state.auth?.is_authenticated) {
    renderStats([]);
    els.eventGroups.innerHTML = `
      <div class="priority-group">
        <div class="empty-state">Signed out</div>
      </div>
    `;
    return;
  }

  if (state.loadingCalendars) {
    renderStats([]);
    setLoadingBoard("Loading calendars");
    return;
  }

  if (!calendar) {
    renderStats([]);
    els.eventGroups.innerHTML = `
      <div class="priority-group">
        <div class="empty-state">No calendars available</div>
      </div>
    `;
    return;
  }

  if (state.loadingEvents) {
    renderStats([]);
    setLoadingBoard("Loading events");
    return;
  }

  renderEvents();
}

function renderEvents() {
  const events = filteredEvents();
  renderStats(events);
  els.eventGroups.innerHTML = "";

  if (events.length === 0) {
    els.eventGroups.innerHTML = `
      <div class="priority-group">
        <div class="empty-state">No events found</div>
      </div>
    `;
    return;
  }

  const groups = [5, 4, 3, 2, 1, null].map((priority) => ({
    priority,
    events: events
      .filter((event) => priorityForEvent(event) === priority)
      .sort((left, right) => eventStartMillis(left) - eventStartMillis(right)),
  }));

  groups.forEach((group) => {
    const section = document.createElement("section");
    section.className = "priority-group";
    section.style.setProperty("--priority-color", PRIORITY_COLORS[group.priority ?? "none"]);

    const title = group.priority === null ? "Unprioritized" : `Priority ${group.priority}`;
    const label = group.priority === 5 ? `${title} / Highest` : title;
    const groupKey = String(group.priority ?? "none");
    const isCollapsed = state.collapsedGroups.has(groupKey);
    const eventWord = group.events.length === 1 ? "event" : "events";

    section.innerHTML = `
      <button class="priority-group-header" type="button" aria-expanded="${!isCollapsed}">
        <span class="priority-title">
          <span class="priority-dot" aria-hidden="true"></span>
          <span>${label}</span>
        </span>
        <span class="group-meta">
          <span class="group-count">${group.events.length} ${eventWord}</span>
          <span class="collapse-indicator" aria-hidden="true">${isCollapsed ? "+" : "-"}</span>
        </span>
      </button>
      <div class="event-list" ${isCollapsed ? "hidden" : ""}></div>
    `;

    section.querySelector(".priority-group-header").addEventListener("click", () => {
      if (state.collapsedGroups.has(groupKey)) {
        state.collapsedGroups.delete(groupKey);
      } else {
        state.collapsedGroups.add(groupKey);
      }
      renderEvents();
    });

    const list = section.querySelector(".event-list");
    if (group.events.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No events at this level";
      list.append(empty);
    } else if (state.range === "all") {
      appendEventSubsection(
        list,
        groupKey,
        "future",
        "Future Events",
        group.events.filter((event) => !isPastEvent(event)),
      );
      appendEventSubsection(
        list,
        groupKey,
        "past",
        "Past Events",
        group.events.filter((event) => isPastEvent(event)),
      );
    } else {
      group.events.forEach((event) => list.append(createEventRow(event)));
    }

    els.eventGroups.append(section);
  });
}

function appendEventSubsection(parent, groupKey, subsectionKey, title, events) {
  const collapseKey = `${groupKey}:${subsectionKey}`;
  const isCollapsed = state.collapsedSubsections.has(collapseKey);
  const subsection = document.createElement("section");
  subsection.className = "event-subsection";
  subsection.innerHTML = `
    <button class="event-subsection-header" type="button" aria-expanded="${!isCollapsed}">
      <span class="event-subsection-title">${title}</span>
      <span class="group-meta">
        <span>${events.length} ${events.length === 1 ? "event" : "events"}</span>
        <span class="collapse-indicator" aria-hidden="true">${isCollapsed ? "+" : "-"}</span>
      </span>
    </button>
    <div class="event-subsection-body" ${isCollapsed ? "hidden" : ""}></div>
  `;

  subsection.querySelector(".event-subsection-header").addEventListener("click", () => {
    if (state.collapsedSubsections.has(collapseKey)) {
      state.collapsedSubsections.delete(collapseKey);
    } else {
      state.collapsedSubsections.add(collapseKey);
    }
    renderEvents();
  });

  const body = subsection.querySelector(".event-subsection-body");
  if (events.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state compact";
    empty.textContent = `No ${title.toLowerCase()}`;
    body.append(empty);
  } else {
    events.forEach((event) => body.append(createEventRow(event)));
  }

  parent.append(subsection);
}

function createEventRow(event) {
  const row = els.eventTemplate.content.firstElementChild.cloneNode(true);
  const priority = priorityForEvent(event);
  row.dataset.eventId = event.id;
  row.dataset.priority = priority ?? "none";
  row.style.setProperty("--priority-color", PRIORITY_COLORS[priority ?? "none"]);

  row.querySelector(".event-time").textContent = formatEventTime(event);
  row.querySelector(".event-title").textContent = event.summary || "Untitled event";

  const details = row.querySelector(".event-details");
  [
    event.location,
    event.organizer_email ? `Organizer: ${event.organizer_email}` : "",
    event.status,
  ]
    .filter(Boolean)
    .forEach((text) => {
      const item = document.createElement("span");
      item.className = "detail-pill";
      item.textContent = text;
      details.append(item);
    });

  const controls = row.querySelector(".priority-buttons");
  [5, 4, 3, 2, 1].forEach((value) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "priority-button";
    button.dataset.priority = String(value);
    button.style.setProperty("--priority-color", PRIORITY_COLORS[value]);
    button.setAttribute("aria-pressed", String(priority === value));
    button.title = `Set priority ${value}`;
    button.textContent = String(value);
    button.disabled = state.updatingEventIds.has(event.id);
    button.addEventListener("click", () => updatePriority(event.id, value));
    controls.append(button);
  });

  const link = row.querySelector(".event-link");
  if (event.html_link) {
    link.href = event.html_link;
    link.hidden = false;
  }

  return row;
}

async function loadAuth() {
  try {
    state.auth = await apiFetch("/auth/me");
  } catch (error) {
    state.auth = { is_authenticated: false };
    setAlert(error.message);
  }
}

async function loadCalendars() {
  if (!state.auth?.is_authenticated) {
    state.calendars = [];
    state.events = [];
    state.selectedCalendarId = "";
    renderShell();
    return;
  }

  state.loadingCalendars = true;
  setAlert("");
  renderShell();

  try {
    const calendars = [];
    let pageToken = "";
    do {
      const params = new URLSearchParams({ max_results: "250" });
      if (pageToken) {
        params.set("page_token", pageToken);
      }

      const payload = await apiFetch(`/calendars?${params}`);
      calendars.push(...payload.items);
      pageToken = payload.next_page_token || "";
    } while (pageToken);

    state.calendars = calendars;
    const preferred = calendars.find((calendar) => calendar.primary) || calendars[0];
    state.selectedCalendarId = state.selectedCalendarId || preferred?.id || "";
  } catch (error) {
    if (error.status === 401) {
      state.auth = { is_authenticated: false };
    }
    setAlert(error.message);
  } finally {
    state.loadingCalendars = false;
    renderShell();
  }

  if (state.selectedCalendarId) {
    await loadEvents(state.selectedCalendarId);
  }
}

async function loadEvents(calendarId) {
  state.selectedCalendarId = calendarId;
  state.loadingEvents = true;
  state.events = [];
  setAlert("");
  renderShell();

  try {
    const events = [];
    let pageToken = "";
    do {
      const params = new URLSearchParams({
        max_results: "2500",
        single_events: "true",
        order_by: "startTime",
      });
      if (pageToken) {
        params.set("page_token", pageToken);
      }

      const payload = await apiFetch(`/calendars/${encodeSegment(calendarId)}/events?${params}`);
      events.push(...payload.items);
      pageToken = payload.next_page_token || "";
    } while (pageToken);

    state.events = events;
  } catch (error) {
    if (error.status === 401) {
      state.auth = { is_authenticated: false };
      state.calendars = [];
      state.selectedCalendarId = "";
    }
    setAlert(error.message);
  } finally {
    state.loadingEvents = false;
    renderShell();
  }
}

async function updatePriority(eventId, priority) {
  if (!state.selectedCalendarId || state.updatingEventIds.has(eventId)) {
    return;
  }

  state.updatingEventIds.add(eventId);
  setAlert("");
  renderShell();

  try {
    const payload = await apiFetch(
      `/calendars/${encodeSegment(state.selectedCalendarId)}/events/${encodeSegment(eventId)}/priority/${priority}`,
      { method: "PATCH" },
    );

    state.events = state.events.map((event) =>
      event.id === eventId ? { ...event, color_id: payload.color_id } : event,
    );
  } catch (error) {
    setAlert(error.message);
  } finally {
    state.updatingEventIds.delete(eventId);
    renderShell();
  }
}

async function logout() {
  setAlert("");
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } catch (error) {
    setAlert(error.message);
  } finally {
    state.auth = { is_authenticated: false };
    state.calendars = [];
    state.events = [];
    state.selectedCalendarId = "";
    renderShell();
  }
}

async function refresh() {
  await loadAuth();
  if (state.auth?.is_authenticated) {
    if (state.calendars.length === 0) {
      await loadCalendars();
    } else if (state.selectedCalendarId) {
      await loadEvents(state.selectedCalendarId);
    } else {
      await loadCalendars();
    }
  } else {
    state.calendars = [];
    state.events = [];
    state.selectedCalendarId = "";
    renderShell();
  }
}

function bindEvents() {
  els.calendarSelect.addEventListener("change", (event) => {
    const calendarId = event.target.value;
    if (calendarId) {
      loadEvents(calendarId);
    }
  });

  els.eventSearch.addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLowerCase();
    renderShell();
  });

  els.rangeFilter.addEventListener("change", (event) => {
    state.range = event.target.value;
    renderShell();
  });

  els.refreshButton.addEventListener("click", refresh);
  els.authActionButton.addEventListener("click", () => {
    if (state.auth?.is_authenticated) {
      logout();
    } else {
      window.location.assign("/api/auth/google/login");
    }
  });
}

async function init() {
  bindEvents();
  renderShell();
  await loadAuth();
  renderShell();

  if (state.auth?.is_authenticated) {
    await loadCalendars();
  }
}

init();
