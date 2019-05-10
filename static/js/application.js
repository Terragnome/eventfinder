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
  $(document).ajaxComplete(Application.onReady);
  $(document).ready(Application.onReady);
}

Application.onReady = function(){
  UserPanel.init();
  Application.ajaxifyLinks();
  Scroll.init();
  Scroll.enable();
  Application.initGroupChips();
}

Application.ajaxData = function(e){
  let targetData = $(e.currentTarget).attr('data');
  let data = {};

  if(targetData){ data = JSON.parse(targetData); }
  if(!data.target){ data.target = '#main'; }

  return data;
}

Application.ajaxGet = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));
}
Application.ajaxGetSkipTransition = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href'), true, false, false, true));
}

Application.ajaxGetOverlay = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(function(){
    Overlay.open();
    Application.getElem("#app_panel_overlay_main", $(this).attr('href'))
  });
}

Application.ajaxGetReplace = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(Application.getElem(data.target, $(this).attr('href')));
}

Application.ajaxPost = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data));
}

Application.ajaxPostReplace = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  $(this).click(Application.postElem(data.target, $(this).attr('href'), data, true));
}

Application.ajaxForm = function(e){
  e.preventDefault();
  let data = Application.ajaxData(e);
  let form = $(this);
  let url = form.attr('action');
  let method = form.attr('method').toLowerCase();

  let urlComponents = url.split('?');
  let urlRoot = urlComponents[0];

  let urlQuery;
  if(urlComponents[1]){
   urlQuery = urlComponents[1].split('&');
  }else{
    urlQuery = [];
  }
  let urlValues = {};
  urlQuery.forEach(function(kv){
    let pair = kv.split('=');
    let k = pair[0];
    let v = pair[1];
    urlValues[k] = v;
  });

  let inputs = form.find($('input'));
  inputs.each(function() {
    if(this.name != null && this.name != ""){
      let k = this.name;
      let v = $(this).val();
      urlValues[k] = v;
    }
  });
  
  if(method == 'get'){
    let newUrlQuery = [];
    for(let k in urlValues){
      let v = urlValues[k];
      newUrlQuery.push(k+'='+v);
    }
    let newUrl = urlRoot+"?"+newUrlQuery.join('&');
    Application.getElem(data.target, newUrl);
  }
}

Application.ajaxifyLinks = function() {
  Application.animateElems();

  $('a.nav_link_get:not(".skip_transition")').unbind('click', Application.ajaxGet);
  $('a.nav_link_get:not(".skip_transition")').click(Application.ajaxGet);

  $('a.nav_link_get.skip_transition').unbind('click', Application.ajaxGetSkipTransition);
  $('a.nav_link_get.skip_transition').click(Application.ajaxGetSkipTransition);

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

  let state = e.originalEvent.state;
  if (state != null) {
    if(state.title){ document.title = state.title; }
    Application.getElem('#main', state.url, false, false, true);
  }else{
    window.location.replace('/');
  }
}

Application.getElem = function(target, url, push_state=true, replace=false, skip_scroll=false, skip_transition=false) {
  $.get(url, {
  }).done(function(response) {
    if(!skip_transition){
      $(target).addClass('anim_fade_in');      
    }

    if(response != '' && push_state){
      let push_url = url;
      if(typeof push_state === 'string'){ push_url = push_state; }
      history.pushState({'url':push_url}, null, push_url);
    }
    if(replace){
      $(target).replaceWith(response);  
    }else{
      $(target).html(response);
    }

    if(!skip_scroll){
      let route = false;
      try{
        route = url.split('/')[3].split('?')[0];
      }catch(e){}

      if(!route || ["", "explore"].indexOf(route)<0){
        Scroll.top();
      }
    }
  }).fail(function(xhr, status, error) {
    window.location.replace(Application.url_home);
  });
}

Application.clickGroupChip = function(e){
  let clickedBtn = $(e.currentTarget);

  let groupBtns = $('#event_group_chips > .cap_group');
  groupBtns.each(function(i){
    let curBtn = $(groupBtns[i]);
    let curGroup = $(curBtn.attr('target'));
    if(clickedBtn.is(curBtn)){
      Application.toggleVisibility(curGroup);
      if(curGroup.is(':visible')){
        clickedBtn.addClass('highlighted');
      }else{
        clickedBtn.removeClass('highlighted');
      }
    }else{
      curBtn.removeClass('highlighted');
      curGroup.hide();
    }
  });
}

Application.initGroupChips = function() {
  $('#event_group_chips > .cap_group').unbind('click', Application.clickGroupChip);
  $('#event_group_chips > .cap_group').click(Application.clickGroupChip);
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
  if(url == null){
    $('.app_background').css('background-image', 'none');
  }else{
    $('.app_background').css('background-image', 'url('+url+')');
  }
}

Application.toggleVisibility = function(target){
  let isVisible = $(target).is(':visible');
  if(isVisible){
    $(target).hide();
  }else{
    $(target).show();
  }
}