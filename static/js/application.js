var Application = Application || {};

Application.init = function(params) {
  var urls = params['urls'];
  Application.url_auth = urls['auth'];
  Application.url_home = urls['home'];

  Scroll.enable();

  $(window).on('popstate', Application.backButton);

  $(document).ajaxStart(function(e){
    $('#main').removeClass('anim_fade_in');
    Scroll.disable();
  });
  $(document).ajaxSuccess(Application.ajaxifyLinks);
  $(document).ajaxComplete(Scroll.enable);

  $(document).ready(Application.ajaxifyLinks);
  $(document).ready(UserPanel.init);
}

Application.ajaxData = function(e){
  var targetData = $(e.currentTarget).attr('data');
  var data = {};

  if(targetData){ data = JSON.parse(targetData); }
  if(!data.target){ data.target = '#main'; }

  return data;
}

Application.ajaxGet = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));  
}

Application.ajaxGetOverlay = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  $(this).click(function(){
    Overlay.open();
    Application.getElem("#app_panel_overlay_main", $(this).attr('href'))
  });
}

Application.ajaxGetReplace = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));
}

Application.ajaxPost = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data));
}

Application.ajaxPostReplace = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data, true));
}

Application.ajaxForm = function(e){
  e.preventDefault();
  var data = Application.ajaxData(e);
  var form = $(this);
  var url = form.attr('action');
  var method = form.attr('method').toLowerCase();

  var urlComponents = url.split('?');
  var urlRoot = urlComponents[0];

  var urlQuery;
  if(urlComponents[1]){
   urlQuery = urlComponents[1].split('&');
  }else{
    urlQuery = [];
  }
  var urlValues = {};
  urlQuery.forEach(function(kv){
    var pair = kv.split('=');
    var k = pair[0];
    var v = pair[1];
    urlValues[k] = v;
  });

  var inputs = form.find($('input'));
  inputs.each(function() {
    if(this.name != null && this.name != ""){
      var k = this.name;
      var v = $(this).val();
      urlValues[k] = v;
    }
  });
  
  if(method == 'get'){
    var newUrlQuery = [];
    for(var k in urlValues){
      var v = urlValues[k];
      newUrlQuery.push(k+'='+v);
    }
    var newUrl = urlRoot+"?"+newUrlQuery.join('&');
    Application.getElem(data.target, newUrl);
  }
}

Application.ajaxifyLinks = function() {
  Application.animateElems();

  $('a.nav_link_get').unbind('click', Application.ajaxGet);
  $('a.nav_link_get').click(Application.ajaxGet);

  $('a.nav_link_get_replace').unbind('click', Application.ajaxGetReplace);
  $('a.nav_link_get_replace').click(Application.ajaxGetReplace);

  $('a.nav_link_get_overlay').unbind('click', Application.ajaxGetOverlay);
  $('a.nav_link_get_overlay').click(Application.ajaxGetOverlay);

  $('a.nav_link_post').unbind('click', Application.ajaxPost);
  $('a.nav_link_post').click(Application.ajaxPost);

  $('a.nav_link_post_replace').unbind('click', Application.ajaxPostReplace);
  $('a.nav_link_post_replace').click(Application.ajaxPostReplace);

  $('form.nav_link_form').unbind('submit', Application.ajaxForm);
  $('form.nav_link_form').submit(Application.ajaxForm);
}

Application.animateElems = function() {
  if($('#event_list').length > 0 && $('.event_card').length > 0){
    new AnimOnScroll(
      document.getElementById('event_list'),
      {
        minDuration : 0.4,
        maxDuration : 0.7,
        viewportFactor : 0.2
      }
    );
  }
}

Application.backButton = function(e){
  Scroll.disable();

  var state = e.originalEvent.state;
  if (state != null) {
    if(state.title){ document.title = state.title; }
    Application.getElem('#main', state.url, false);
  }else{
    window.location.replace('/');
  }
}

Application.getElem = function(target, url, push_state=true, replace=false) {
  $.get(url, {
  }).done(function(response) {
    $(target).addClass('anim_fade_in');
    if(response != '' && push_state){
      var push_url = url;
      if(typeof push_state === 'string'){ push_url = push_state; }
      history.pushState({'url':push_url}, null, push_url);
    }
    if(replace){
      $(target).replaceWith(response);  
    }else{
      $(target).html(response);
    }
  }).fail(function(xhr, status, error) {
    window.location.replace(Application.url_home);
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

Application.setAppBackground = function(url) {
  // if(url == null){
  //   $('.app_background').css('background-image', 'none');
  // }else{
  //   $('.app_background').css('background-image', 'url('+url+')');
  // }
}

Application.toggleVisibility = function(target){
  var isVisible = $(target).is(':visible');
  if(isVisible){
    $(target).hide();
  }else{
    $(target).show();
  }
}