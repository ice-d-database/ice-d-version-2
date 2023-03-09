$(document).ready(function(){
    var textFitConfig = {
        minFontSize: 32,
        maxFontSize: 56,
        alignVert: true,
        multiLine: true
    };
    // Fits the title within the box provided
    textFit(document.getElementById('app-title'), textFitConfig);
    $('#app-title').css('visibility', 'visible');
});
