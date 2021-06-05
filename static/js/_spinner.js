var Spinner = Spinner || {};

Spinner.init = function(){
  let main_spinner = $("#main_spinner");
  Application.spinnerHtml = main_spinner.html();
  main_spinner.html("");
}