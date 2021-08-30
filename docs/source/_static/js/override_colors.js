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
    change_color("nf", "#5865F2")
    // create class instance
    // change_color("n", )
    
    // built-in function calls
    change_color("nb", "#ecfc5b")
    // +, -, *, /, =
    // change_color("o", "#69f5f2")
    //#endregion

    // fix code
    result = document.getElementsByTagName("code");
    for (let i = 0; i < result.length; i++)
        result[i].style["font-weight"] = 100
}