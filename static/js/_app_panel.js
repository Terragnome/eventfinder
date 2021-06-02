var AppPanel = AppPanel || {};

AppPanel.init = function(){
  $(".toggle_app_panel").unbind('click', AppPanel.toggle);
  $(".toggle_app_panel").bind('click', AppPanel.toggle);
  
  $("#app_panel > a").unbind('click', AppPanel.hide);
  $("#app_panel > a").bind('click', AppPanel.hide);
}

AppPanel.toggle = function(e){
  let isVisible = $("#app_panel").is(':visible');
  if(isVisible){
    AppPanel.hide();
  }else{
    AppPanel.show();
  }
  e.stopPropagation();
}

AppPanel.hide = function(){
  let isVisible = $("#app_panel").is(':visible');
  if(isVisible){
    $("#app_panel").hide();
    $('html').unbind('click', AppPanel.checkHide);
  }
}

AppPanel.checkHide = function(e){
  if(e.target.id != 'app_panel'){
    AppPanel.hide();
  }
}

AppPanel.show = function(){
  let isVisible = $("#app_panel").is(':visible');
  if(!isVisible){
    $("#app_panel").show();
    $('html').bind('click', AppPanel.checkHide);
  }
}