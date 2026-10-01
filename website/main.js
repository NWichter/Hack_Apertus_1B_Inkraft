(function () {
  var img = document.getElementById("hero-logo");
  if (!img) return;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var still = /[?&]still(=|&|$)/.test(location.search);
  if (!reduceMotion.matches && !still)
    img.setAttribute("src", img.dataset.anim);
})();
