/*

    This override module is needed to change some values I Could not change in a custom css
    (I know this is a shit idea but it kinda works)

*/

function change_color(class_name, color) {
    result = document.getElementsByClassName(class_name)
    for (var i = 0; i < result.length; i++) {
        result[i].style.color = color
        result[i].style["font-weight"] = 100
    };
}

window.onload = function() {
    //#region colors
    let string_green = "#afff7d"
    let self_red = "#ff525d"
    let int_orange = "#ffed85"

    // numbers
    change_color("mi", int_orange)
    // '' string
    change_color("s1", string_green)
    // "" string
    change_color("s2", string_green)
    // """""" docstring
    change_color("sd", string_green)
    // bools
    change_color("kc", self_red)

    // import statements
    change_color("kn", "#d962fc")
    // import package
    change_color("nn", "orange")
    // comments
    change_color("c1", "grey")

    
    // class name
    change_color("nc", "orange")
    // __init__
    change_color("fm", "#5865F2")
    // self
    change_color("bp", self_red)

    // async, def, await 
    change_color("k", "#eb52ff")
    // function name
    change_color("nf", "#5c9aff")
    // Decorators
    change_color("nd", "#FE0")

    // built-in function calls
    change_color("nb", "#ecfc5b")
    // +, -, *, /, =
    // change_color("o", "#69f5f2")
    //#endregion

    // fix code
    result = document.getElementsByTagName("code");
    for (let i = 0; i < result.length; i++)
        result[i].style["font-weight"] = 100

    // mobile only
    change_color("wy-nav-top", "#5865F2")


    // functions
    result = document.getElementsByClassName("sig sig-object py")
    for (let i = 0; i < result.length; i++) {
        result[i].style["color"] = "black";
        result[i].style["background-color"] = "#F6F6F6";
        result[i].style["border"] = "3px solid #F6F6F6";
        result[i].style["border-radius"] = "4px";
        result[i].style["border-top"] = "3px solid black";
        result[i].style["font-size"] = "95%"
    }

    result = document.getElementsByTagName("dt")
    for (let i = 0; i < result.length; i++)
    {
        result[i].style["background-color"] = "#fcfcfc";
        result[i].style["border-left"] = "5px solid #fcfcfc";
    }


    // Makes page full size
    result = document.getElementsByClassName("wy-nav-content")
    if (result.length > 0)
        result[0].style["max-width"] = "100%";

    // displays the menu icon
    result = document.getElementsByClassName("wy-nav-top")
    if (result.length > 0)
        result[0].style["color"] = "white";

    setTimeout(() => document.getElementsByClassName("rst-content")[0].innerHTML += "\n<p style='color: gray;'>Modified by <a href='https://github.com/404kuso' target='_blank'>404kuso</a></p>", 100)
}