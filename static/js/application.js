var Application = Application || {};

Application.init = function() {
  Application.enableScrollEvent();

  $(window).on('popstate', Application.backButton);

  $(document).ready(Application.ajaxifyLinks);
  $(document).ajaxStart(Application.disableScrollEvent);
  $(document).ajaxSuccess(Application.ajaxifyLinks);
  $(document).ajaxComplete(Application.enableScrollEvent);
}

Application.ajaxifyLinks = function() {
  Application.animateElems();

  $('a.nav_link').click(function(e){
  e.preventDefault();
    $(this).click(Application.getElem('#main', $(this).attr('href')));
  });
}

Application.animateElems = function() {
  if($('#event_list').length > 0 && $('.event_card').length > 0){
    new AnimOnScroll(
      document.getElementById('event_list'), {
        minDuration : 0.4,
        maxDuration : 0.7,
        viewportFactor : 0.2
      }
    );
  }
}

Application.backButton = function(e){
  Application.disableScrollEvent();

  var state = e.originalEvent.state;
  if (state !== null) {
    if(state.title){ document.title = state.title; }
    Application.getElem('#main', state.url, false);
  }
}

Application.disableScrollEvent = function() {
  $(window).off("scroll", Application.scrollNext);
}

Application.enableScrollEvent = function() {
  Application.disableScrollEvent();
  $(window).on("scroll", Application.scrollNext);
}

Application.getElem = function(target, url, push_state=true) {
  $.get(url, {
  }).done(function(response) {
    if(push_state){ history.pushState({'url':url}, null, url); }
    $(target).html(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.postElem = function(target, url, params) {
  $.post(url, params, {
  }).done(function(response) {
    $(target).html(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.removeElem = function(target) {
  $(target).remove();
}

Application.replaceGetElem = function(target, url, push_state=true) {
  $.get(url, {
  }).done(function(response) {
    if(push_state){ history.pushState({'url':url}, null, url); }
    $(target).replaceWith(response);
  }).fail(function(xhr, status, error) {
  });
}

Application.scrollNext = function(){
  var scrollHeight = $(document).height();
  var scrollPosition = $(window).height()+$(window).scrollTop();

  if((scrollHeight-scrollPosition)/scrollHeight === 0){
    var current_url = window.location.pathname+window.location.search;
    var next_url = $('.pagination:last').find('a:first').attr('href');
    if(next_url && next_url != current_url){
      history.pushState({'url':next_url}, null, next_url);
      Application.replaceGetElem('.pagination:last', next_url+'&scroll=true', false);
    }
  }
}

Application.init();