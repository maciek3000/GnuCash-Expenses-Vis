var elements = document.getElementsByClassName("menu_button");
var i;

for (i = 0; i < elements.length; i++) {
    elements[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
        }
    });
}