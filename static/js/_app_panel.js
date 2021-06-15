// class AppPanel{
//   constructor(elemId){
//     this.elemId = elemId;
//     this.toggleId = elemId+"_toggle";

//     this.init = this.init.bind(this);
//     this.show = this.show.bind(this);
//   }
//   init(){
//     $(this.toggleId).unbind('click', this.toggle);
//     $(this.toggleId).bind('click', this.toggle);
    
//     $(this.elemId+" > a").unbind('click', this.hide);
//     $(this.elemId+" > a").bind('click', this.hide);
//   }
//   get isVisible(){
//     return $(this.elemId).is(':visible');
//   }
//   checkHide(e){
//     if(e.target.id != 'app_panel'){
//       this.hide();
//     }
//   }
//   hide(){
//     if(this.isVisible){
//       $(AppPanel.elemId).hide();
//       $('html').unbind('click', this.checkHide);
//     }
//   }
//   show(){
//     $(".app_panel").hide();
//     if(!this.isVisible){
//       $(this.elemId).show();
//       $('html').bind('click', this.checkHide);
//     }
//   } 
//   toggle(){
//     if(this.isVisible){
//       this.hide();
//     }else{
//       this.show();
//     }
//     e.stopPropagation();
//   }
// }

var AppPanel = AppPanel || {};
AppPanel.init = function(elem_id){
  AppPanel.elemId = elem_id;
  AppPanel.toggleId = AppPanel.elemId+"_toggle";
  AppPanel.bindEvents();
}

AppPanel.bindEvents = function(){
  $(AppPanel.toggleId).unbind('click', AppPanel.toggle);
  $(AppPanel.toggleId).bind('click', AppPanel.toggle);
  
  $(AppPanel.elemId+" > a").unbind('click', AppPanel.hide);
  $(AppPanel.elemId+" > a").bind('click', AppPanel.hide);
}

AppPanel.isVisible = function(){
  return $(AppPanel.elemId).is(':visible');
}

AppPanel.toggle = function(e){
  let isVisible = AppPanel.isVisible();
  if(isVisible){
    AppPanel.hide();
  }else{
    AppPanel.show();
  }
  e.stopPropagation();
}

AppPanel.hide = function(){
  let isVisible = AppPanel.isVisible();
  if(isVisible){
    $(AppPanel.elemId).hide();
    $('html').unbind('click', AppPanel.checkHide);
  }
}

AppPanel.checkHide = function(e){
  if(e.target.id != 'app_panel'){
    AppPanel.hide();
  }
}

AppPanel.show = function(){
  $(".app_panel").hide();

  let isVisible = AppPanel.isVisible();
  if(!isVisible){
    $(AppPanel.elemId).show();
    $('html').bind('click', AppPanel.checkHide);
  }
}

var UserPanel = UserPanel || {};
UserPanel.init = function(elem_id){
  UserPanel.elemId = elem_id;
  UserPanel.toggleId = UserPanel.elemId+"_toggle";
  UserPanel.bindEvents();
}

UserPanel.bindEvents = function(){
  $(UserPanel.toggleId).unbind('click', UserPanel.toggle);
  $(UserPanel.toggleId).bind('click', UserPanel.toggle);
  
  $(UserPanel.elemId+" > a").unbind('click', UserPanel.hide);
  $(UserPanel.elemId+" > a").bind('click', UserPanel.hide);
}

UserPanel.isVisible = function(){
  return $(UserPanel.elemId).is(':visible');
}

UserPanel.toggle = function(e){
  let isVisible = UserPanel.isVisible();
  if(isVisible){
    UserPanel.hide();
  }else{
    UserPanel.show();
  }
  e.stopPropagation();
}

UserPanel.hide = function(){
  let isVisible = UserPanel.isVisible();
  if(isVisible){
    $(UserPanel.elemId).hide();
    $('html').unbind('click', UserPanel.checkHide);
  }
}

UserPanel.checkHide = function(e){
  if(e.target.id != 'app_panel'){
    UserPanel.hide();
  }
}

UserPanel.show = function(){
  $(".app_panel").hide();

  let isVisible = UserPanel.isVisible();
  if(!isVisible){
    $(UserPanel.elemId).show();
    $('html').bind('click', UserPanel.checkHide);
  }
}