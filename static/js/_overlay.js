var Overlay = Overlay || {};

Overlay.open = function() {
  var scrollTop = document.documentElement.scrollTop;
  var appPanel = $('#app_panel_overlay');
  appPanel.css('top', scrollTop);
  appPanel.show();
}

Overlay.close = function() {
  history.back();
  $('#app_panel_overlay').hide();
}
