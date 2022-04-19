const primaryNav = document.querySelector(".primary-navigation")
const navToggle = document.querySelector(".mobile-nav-toggle")
const grad = document.querySelector(".wrapper")

navToggle.addEventListener("click", ()=>{
    const visibility = primaryNav.getAttribute('data-visible');

    if (visibility === "false")
    {
        primaryNav.setAttribute("data-visible", true);
        navToggle.setAttribute("aria-expanded", true);
    } else {
        primaryNav.setAttribute("data-visible", false);
        navToggle.setAttribute("aria-expanded", false);
    }
});

window.addEventListener("load", ()=>{
    const toggler = grad.getAttribute("bkg-c");

    if (toggler === "0")
    {
        document.body.style.background = "#DDDDDC";
    }
});