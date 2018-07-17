var Application = Application || {};

Application.init = function() {
}

Application.get_elem = function(target, url) {
  Application.disableScrollEvent();
  $.get(url, {
  }).done(function(response) {
    stateObj = {};
    history.pushState(stateObj, null, url);
    $(target).html(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.post_elem = function(target, url, params) {
  Application.disableScrollEvent();
  $.post(url, params, {
  }).done(function(response) {
    $(target).html(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.remove_elem = function(target) {
  $(target).remove();
}

Application.replace_get_elem = function(target, url) {
  Application.disableScrollEvent();
  $.get(url, {
  }).done(function(response) {
    stateObj = {};
    history.pushState(stateObj, null, url);
    $(target).replaceWith(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.enableScrollEvent = function() {
  Application.disableScrollEvent();
  $(window).on("scroll", Application.scrollNext);
}

Application.disableScrollEvent = function() {
  $(window).off("scroll", Application.scrollNext);
}

Application.scrollNext = function(){
  var scrollHeight = $(document).height();
  var scrollPosition = $(window).height()+$(window).scrollTop();
  if((scrollHeight-scrollPosition)/scrollHeight === 0){
    Application.disableScrollEvent();
    var next_url = $('.pagination:last').find('a:first').attr('href');
    Application.replace_get_elem('.pagination:last', next_url);
  }
}

// Application.onPageLoading = function(e, target, render, url)d{
//   Application.showLoader();
//   Scroll.scrollTo(0);
// }
// Application.onPageRedirected = function(e, target, render, url){}
// Application.onPageDone = function(e, target, render, url){}
// Application.onPageFail = function(e, target, render, url){}
// Application.onPageAlways = function(e, target, render, url){
//   Application.hideLoader();
//   Scroll.scrollTo(DOM.getPageTop());
// }

// Application.showLoader = function(){
// }

// Application.hideLoader = function(){
// }

Application.init();