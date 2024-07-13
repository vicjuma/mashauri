// add hovered class to selected list item
let list = document.querySelectorAll(".navigation li");

function activeLink() {
  list.forEach((item) => {
    item.classList.remove("hovered");
  });
  this.classList.add("hovered");
}

// list.forEach((item) => item.addEventListener("mouseover", activeLink));

// Menu Toggle
// let toggle = document.querySelector(".toggle");
// let navigation = document.querySelector(".navigation");
// let main = document.querySelector(".main");

// toggle.onclick = function () {
//   navigation.classList.toggle("active");
//   main.classList.toggle("active");
// };

$(document).on("ready", function () {
  // 0 = oculto, 1 = visible
  var menuState = 0;
  //if($(".mini-menu-options").is(":hidden")) {
  /* Agrega un listener del evento Click a btn-select */
  $(".btn-select").on("click", function () {
    if (menuState === 0) {
      $(".mini-menu-options").slideDown("slow");
      menuState = 1;
    } else {
      $(".mini-menu-options").slideUp("slow");
      menuState = 0;
    }
  });
  //}
  // Si el enlace actual (li) tiene mas de 1 hijo, es decir
  // su enlace (a) y ademas un submenu (ul)
  $(".mini-menu-options li").on("click", function () {
    var numHijos = $(this).children().length;
    if (numHijos < 2) {
      // esconde el menu
      $(".mini-menu-options").hide("fast");
      // obtiene el texto del elemento elegido
      var texto = $(this).text();
      // y lo agrega a la barra del menu
      $(".menu-select .menu-actual").text(texto);
    }
    menuState = 0; // reinicia la variable que controla el menu
  });
});
