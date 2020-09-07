var Overlay = Overlay || {};

Overlay.open = function() {
  let scrollTop = document.documentElement.scrollTop;
  let appPanel = $('#app_panel_overlay');
  appPanel.css('top', scrollTop);
  appPanel.show();
}

Overlay.close = function() {
  history.back();
  $('#app_panel_overlay').hide();
}
