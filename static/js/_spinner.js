var Spinner = Spinner || {};

Spinner.init = function(){
  let mainSpinner = $("#main_spinner");
  Spinner.spinnerHtml = mainSpinner.html();
  mainSpinner.html("");
}

Spinner.show = function(target){
  $(target).html(Spinner.spinnerHtml);
}

Spinner.hide = function(target){
  $(target).html("");
}