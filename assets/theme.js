/* Shared site script, loaded on every page.
   1. Design themes: Playful (default), Vibrant and Classic. Picker in the nav; choice saved per browser.
   2. Mobile menu, back-to-top button, scroll regions, blog search. Every block checks its elements exist. */
(function () {
  var root = document.documentElement;
  var names = { vibrant: "Vibrant", classic: "Classic", playful: "Playful" };
  var colors = { vibrant: "#FAFAF9", classic: "#F8F6F1", playful: "#FFFBF2" };
  function current() { var t = root.getAttribute("data-site-theme"); return names[t] ? t : "playful"; }
  function sync() {
    var t = current();
    document.querySelectorAll(".theme-btn .theme-name").forEach(function (n) { n.textContent = names[t]; });
    document.querySelectorAll(".theme-btn").forEach(function (b) { b.setAttribute("aria-label", "Design theme: " + names[t] + ". Choose another theme"); });
    document.querySelectorAll(".theme-menu [data-theme]").forEach(function (o) { o.setAttribute("aria-checked", String(o.getAttribute("data-theme") === t)); });
    var m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute("content", colors[t]);
  }
  function setTheme(t) {
    root.setAttribute("data-site-theme", t);
    if (window.__themeFonts) window.__themeFonts(t);
    try { localStorage.setItem("site-theme", t); } catch (e) {}
    var tilt = document.querySelector(".tilt"); if (tilt) tilt.style.transform = "";
    sync();
  }
  document.querySelectorAll(".theme-pick").forEach(function (pick) {
    var btn = pick.querySelector(".theme-btn"), menu = pick.querySelector(".theme-menu");
    if (!btn || !menu) return;
    function close() { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); }
    function open() {
      menu.hidden = false; btn.setAttribute("aria-expanded", "true");
      var on = menu.querySelector('[aria-checked="true"]') || menu.querySelector("button"); if (on) on.focus();
    }
    btn.addEventListener("click", function (e) { e.stopPropagation(); menu.hidden ? open() : close(); });
    menu.addEventListener("click", function (e) {
      var o = e.target.closest("[data-theme]"); if (!o) return;
      setTheme(o.getAttribute("data-theme")); close(); btn.focus();
    });
    menu.addEventListener("keydown", function (e) {
      var items = [].slice.call(menu.querySelectorAll("[data-theme]")), i = items.indexOf(document.activeElement);
      if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      if (e.key === "Escape") { close(); btn.focus(); }
    });
    document.addEventListener("click", function (e) { if (!pick.contains(e.target)) close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { close(); btn.focus(); } });
  });
  sync();

  var photo = document.querySelector(".photo"), tilt = photo && photo.querySelector(".tilt");
  if (!tilt || !window.matchMedia || matchMedia("(prefers-reduced-motion: reduce)").matches || !matchMedia("(pointer: fine)").matches) return;
  photo.addEventListener("mousemove", function (e) {
    if (current() !== "vibrant") return;
    var r = photo.getBoundingClientRect();
    var x = (e.clientX - r.left - r.width / 2) / r.width, y = (e.clientY - r.top - r.height / 2) / r.height;
    tilt.style.transform = "rotateX(" + (-y * 12).toFixed(2) + "deg) rotateY(" + (x * 14).toFixed(2) + "deg)";
  });
  photo.addEventListener("mouseleave", function () { tilt.style.transform = ""; });
})();

(function () {
  var doc = document, root = doc.documentElement;

  /* Mobile menu: overlay under the header. Closes on link tap, Escape, outside tap and when the desktop nav returns. */
  var btn = doc.getElementById("menuBtn"), menu = doc.getElementById("mobileMenu");
  if (btn && menu) {
    var setMenu = function (open) {
      menu.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
      btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      root.classList.toggle("menu-open", open);
    };
    btn.addEventListener("click", function () { setMenu(menu.hidden); });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { setMenu(false); btn.focus(); } });
    doc.addEventListener("click", function (e) { if (!menu.hidden && !menu.contains(e.target) && !btn.contains(e.target)) setMenu(false); });
    if (window.matchMedia) {
      var wide = matchMedia("(min-width:981px)"), onWide = function () { if (wide.matches && !menu.hidden) setMenu(false); };
      if (wide.addEventListener) wide.addEventListener("change", onWide); else if (wide.addListener) wide.addListener(onWide);
    }
  }

  /* Back to top: appears after two screens of scrolling. */
  var top = doc.createElement("button");
  top.type = "button"; top.className = "to-top"; top.hidden = true;
  top.setAttribute("aria-label", "Back to top");
  top.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 13V3M3.5 7.5 8 3l4.5 4.5"/></svg>';
  top.addEventListener("click", function () {
    var calm = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: calm ? "auto" : "smooth" });
    var brand = doc.querySelector(".brand"); if (brand) brand.focus({ preventScroll: true });
  });
  doc.body.appendChild(top);
  var ticking = false, showTop = function () { ticking = false; top.hidden = window.scrollY < window.innerHeight * 2; };
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(showTop); } }, { passive: true });
  showTop();

  /* Sideways-scrolling blocks: keyboard reachable, and flagged only while they actually overflow. */
  var scrollers = [].slice.call(doc.querySelectorAll(".ruler, pre.sql, .post-code"));
  var mark = function () {
    scrollers.forEach(function (el) {
      var over = el.scrollWidth > el.clientWidth + 2;
      el.classList.toggle("can-scroll", over);
      if (over) el.setAttribute("tabindex", "0"); else el.removeAttribute("tabindex");
    });
  };
  if (scrollers.length) { mark(); window.addEventListener("resize", mark); window.addEventListener("load", mark); }

  /* Blog index: filter the list as you type. */
  var q = doc.getElementById("blogSearch"), rows = [].slice.call(doc.querySelectorAll(".bl-list .bl-row"));
  if (q && rows.length) {
    var none = doc.getElementById("blogNone"), count = doc.getElementById("blogCount");
    q.addEventListener("input", function () {
      var words = q.value.toLowerCase().split(/\s+/).filter(Boolean), shown = 0;
      rows.forEach(function (r) {
        var text = r.textContent.toLowerCase(), hit = words.every(function (w) { return text.indexOf(w) > -1; });
        r.hidden = !hit; if (hit) shown++;
      });
      if (none) none.hidden = shown > 0;
      if (count) count.textContent = words.length ? shown + " of " + rows.length + " posts" : rows.length + " posts";
    });
  }
})();
