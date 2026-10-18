/* Design themes: Vibrant (default), Classic (original) and Playful. Picker in the nav; choice saved per browser. */
(function () {
  var root = document.documentElement;
  var names = { vibrant: "Vibrant", classic: "Classic", playful: "Playful" };
  var colors = { vibrant: "#FAFAF9", classic: "#F8F6F1", playful: "#FFFBF2" };
  function current() { var t = root.getAttribute("data-site-theme"); return names[t] ? t : "vibrant"; }
  function sync() {
    var t = current();
    document.querySelectorAll(".theme-btn .theme-name").forEach(function (n) { n.textContent = names[t]; });
    document.querySelectorAll(".theme-btn").forEach(function (b) { b.setAttribute("aria-label", "Design theme: " + names[t] + ". Choose another theme"); });
    document.querySelectorAll(".theme-menu [data-theme]").forEach(function (o) { o.setAttribute("aria-checked", String(o.getAttribute("data-theme") === t)); });
    var m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute("content", colors[t]);
  }
  function setTheme(t) {
    root.setAttribute("data-site-theme", t);
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
