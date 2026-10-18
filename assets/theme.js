/* Design theme switch (Vibrant default, Classic original) and the Vibrant hero tilt. */
(function () {
  var root = document.documentElement;
  var names = { vibrant: "Vibrant", classic: "Classic" };
  function current() { return root.getAttribute("data-site-theme") === "classic" ? "classic" : "vibrant"; }
  function sync() {
    var t = current(), other = t === "vibrant" ? "classic" : "vibrant";
    document.querySelectorAll(".theme-btn").forEach(function (b) {
      var n = b.querySelector(".theme-name"); if (n) n.textContent = names[t];
      b.setAttribute("aria-label", "Design theme: " + names[t] + ". Switch to " + names[other]);
      b.setAttribute("title", "Switch to " + names[other] + " theme");
    });
    var m = document.querySelector('meta[name="theme-color"]');
    if (m) m.setAttribute("content", t === "vibrant" ? "#FAFAF9" : "#F8F6F1");
  }
  document.querySelectorAll(".theme-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      var next = current() === "vibrant" ? "classic" : "vibrant";
      root.setAttribute("data-site-theme", next);
      try { localStorage.setItem("site-theme", next); } catch (e) {}
      var t = document.querySelector(".tilt"); if (t) t.style.transform = "";
      sync();
    });
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
