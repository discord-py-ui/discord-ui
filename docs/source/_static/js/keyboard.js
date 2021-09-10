document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'k') {
        event.preventDefault()
        document.getElementById("rtd-search-form").children[0].focus()
    }
});