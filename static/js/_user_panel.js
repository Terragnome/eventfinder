var UserPanel = UserPanel || {};

UserPanel.init = function(){
  $(".toggle_user_panel").unbind('click', UserPanel.toggle);
  $(".toggle_user_panel").bind('click', UserPanel.toggle);
  
  $("#user_panel > a").unbind('click', UserPanel.hide);
  $("#user_panel > a").bind('click', UserPanel.hide);
}

UserPanel.toggle = function(e){
  var isVisible = $("#user_panel").is(':visible');
  if(isVisible){
    UserPanel.hide();
  }else{
    UserPanel.show();
  }
  e.stopPropagation();
}

UserPanel.hide = function(){
  var isVisible = $("#user_panel").is(':visible');
  if(isVisible){
    $("#user_panel").hide();
    $('html').unbind('click', UserPanel.checkHide);
  }
}

UserPanel.checkHide = function(e){
  if(e.target.id != 'user_panel'){
    UserPanel.hide();
  }
}

UserPanel.show = function(){
  var isVisible = $("#user_panel").is(':visible');
  if(!isVisible){
    $("#user_panel").show();
    $('html').bind('click', UserPanel.checkHide);
  }
}