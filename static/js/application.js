var Application = Application || {};

Application.init = function(params) {
  let urls = params['urls'];
  Application.urlAuth = urls['auth'];
  Application.urlExplore = urls['explore'];

  let main = params['main'];
  Application.main = main['container'];
  Application.mainSpinner = main['spinner'];

  $(document).ready(Application.onReady);
}

Application.onReady = function(){
  $(document).ajaxStart(Application.onAjaxStart);
  $(document).ajaxComplete(Application.onAjaxComplete);
  $(window).on('popstate', Application.onBack);

  AppPanel.init("#app_panel");
  UserPanel.init("#user_panel");
  Scroll.init();
  Spinner.init();
  Application.onAjaxComplete();
}

Application.initBackButtons = function(){
  let backButtons = $('a.button_back');
  if(backButtons){
    try{
      backButtons.unbind('click', Application.backButton);
    }catch(e){}
    backButtons.click(Application.backButton);
  }
}

Application.initLocationButtons = function(){
  let locationButtons = $('a.needs_location');
  if(locationButtons){
    try{
      locationButtons.unbind('click', Geocoder.getLocation);
    }catch(e){}
    locationButtons.click(Geocoder.getLocation);
  }
}

Application.onAjaxStart = function(){
  $(Application.main).removeClass('anim_fade_in');
  Scroll.disable();
}

Application.onAjaxComplete = function(){
  Application.ajaxifyLinks();
  Application.initGroupChips();
  Application.initBackButtons();
  Application.initLocationButtons();
  Scroll.enable();
}

Application.ajaxData = function(e){
  let targetData = $(e.currentTarget).attr('data');
  let data = {};

  if(targetData){ data = JSON.parse(targetData); }
  if(!data.target){ data.target = Application.main; }

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
  let entityLists = $('.entity_list');
  entityLists.each(function(){
    if($(this).length > 0 && $('.entity_card').length > 0){
      let elId = $(this).attr('id');
      new AnimOnScroll(
        document.getElementById(elId),
        {
          minDuration : 0.4,
          maxDuration : 0.7,
          viewportFactor : 0.2
        }
      );
    }
  });
}

Application.backButton = function(e){
  window.history.back();
}

Application.onBack = function(e){
  Scroll.disable();

  let state = e.originalEvent.state;
  if (state != null) {
    if(state.title){ document.title = state.title; }
    Application.getElem(Application.main, state.url, false, false, true, false, Application.mainSpinner);
  }else{
    Spinner.show(Application.mainSpinner);
    let backUrl = document.referrer;
    if(backUrl == null){ backUrl = '/'; }
    window.location.replace(backUrl);
  }
}

Application.getElem = function(target, url, pushState=true, replace=false, skipScroll=false, skipTransition=false, spinner=false){
  if(target == Application.main && spinner == false){
    spinner = Application.mainSpinner;
  }

  if(spinner != false){
    let spinnerTarget = spinner == true ? target : spinner;
    Spinner.show(spinnerTarget);
  }

  $.get(url, {
  }).done(function(response) {
    if(target == Application.main){
      Application.setAppBackground(null);
    }

    if(!skipTransition){
      $(target).addClass('anim_fade_in');      
    }

    if(response!='' && pushState){
      let pushUrl = url;
      if(typeof pushState === 'string'){ pushUrl = pushState; }
      history.pushState({'url':pushUrl}, null, pushUrl);
    }
    if(replace){
      $(target).replaceWith(response);  
    }else{
      $(target).html(response);
    }

    if(!skipScroll){
      let route = false;
      try{
        route = url.split('/')[3].split('?')[0];
      }catch(e){}

      if(!route || ["", "explore"].indexOf(route)<0){
        Scroll.top();
      }
    }
    if(spinner != false){ Spinner.hide(spinner); }
  }).fail(function(xhr, status, error) {
    window.location.replace(Application.urlExplore);
    if(spinner != false){ Spinner.hide(spinner); }
  });
}

Application.clickGroupChip = function(e){
  let clickedBtn = $(e.currentTarget);

  let groupBtns = $('.cap_group');
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
  $('.cap_group').unbind('click', Application.clickGroupChip);
  $('.cap_group').click(Application.clickGroupChip);
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
    window.location.replace(Application.urlAuth);
  });
}

Application.removeElem = function(target) {
  $(target).remove();
}

Application.setBackground = function(selector, url) {
  if(url == null){
    $(selector).removeAttr('style');
  }else{
    $(selector).css('background-image', 'url('+url+')');
  }
}

Application.setAppBackground = function(url) {
  var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
  var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHi || 0);

  if(url == null || vw < 720 || vh < 320){
    $('.app_header').css('background-color', '');
    Application.setBackground('.app_background', null);
  }else{
    $('.app_header').css('background-color', 'white');
    Application.setBackground('.app_background', url);
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