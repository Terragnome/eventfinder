var Application = Application || {};

Application.init = function(params) {
  var urls = params['urls'];
  Application.url_auth = urls['auth'];

  Application.enableScrollEvent();

  $(window).on('popstate', Application.backButton);

  $(document).ready(Application.ajaxifyLinks);
  $(document).ajaxStart(function(e){
    $('#main').removeClass('anim_fade_in');
    Application.disableScrollEvent();
  });
  $(document).ajaxSuccess(Application.ajaxifyLinks);
  $(document).ajaxComplete(Application.enableScrollEvent);
}

Application.ajaxHistory = function(e){
  var targetData = $(e.target).attr('data');
  var data = {};

  if(targetData){ data = JSON.parse(targetData); }
  if(!data.target){ data.target = '#main' }

  return data;
}

Application.ajaxGet = function(e){
  e.preventDefault();
  var data = Application.ajaxHistory(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));  
}

Application.ajaxGetReplace = function(e){
  e.preventDefault();
  var data = Application.ajaxHistory(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));
}

Application.ajaxPost = function(e){
  e.preventDefault();
  var data = Application.ajaxHistory(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data));
}

Application.ajaxPostReplace = function(e){
  e.preventDefault();
  var data = Application.ajaxHistory(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data, true));
}

Application.ajaxifyLinks = function() {
  Application.animateElems();

  $('a.nav_link_get').unbind('click', Application.ajaxGet);
  $('a.nav_link_get').click(Application.ajaxGet);

  $('a.nav_link_get_replace').unbind('click', Application.ajaxGetReplace);
  $('a.nav_link_get_replace').click(Application.ajaxGetReplace);

  $('a.nav_link_post').unbind('click', Application.ajaxPost);
  $('a.nav_link_post').click(Application.ajaxPost);

  $('a.nav_link_post_replace').unbind('click', Application.ajaxPostReplace);
  $('a.nav_link_post_replace').click(Application.ajaxPostReplace);
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

Application.getElem = function(target, url, push_state=true, replace=false) {
  $.get(url, {
  }).done(function(response) {
    $(target).addClass('anim_fade_in');
    if(push_state){ history.pushState({'url':url}, null, url); }
    if(replace){
      $(target).replaceWith(response);  
    }else{
      $(target).html(response);
    }
  }).fail(function(xhr, status, error) {
    window.location.replace(url);
  });
}

Application.postElem = function(target, url, params, replace=false) {
  $.post(url, params, {
  }).done(function(response) {
    if(replace){
      $(target).replaceWith(response);  
    }else{
      $(target).html(response);  
    }
  }).fail(function(xhr, status, error) {
    window.location.replace(Application.url_auth);
  });
}

Application.removeElem = function(target) {
  $(target).remove();
}

Application.scrollNext = function(){
  var scrollHeight = $(document).height();
  var scrollPosition = $(window).height()+$(window).scrollTop();

  if((scrollHeight-scrollPosition)/scrollHeight === 0){
    var current_url = window.location.pathname+window.location.search;
    var next_url = $('.pagination:last').find('a:first').attr('href');
    if(next_url && next_url != current_url){
      history.pushState({'url':next_url}, null, next_url);
      Application.getElem('.pagination:last', next_url+'&scroll=true', false, true);
    }
  }
}