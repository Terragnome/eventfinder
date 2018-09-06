var Scroll = Scroll || {};

Scroll.disable = function() {
  $(window).off("scroll", Scroll.getNext);
}

Scroll.enable = function() {
  Scroll.disable();
  $(window).on("scroll", Scroll.getNext);
}

Scroll.getNext = function(){
  var scrollHeight = $(document).height();
  var scrollPosition = $(window).height()+$(window).scrollTop();

  if((scrollHeight-scrollPosition)/scrollHeight === 0){
    var current_url = window.location.pathname+window.location.search;
    var next_url = $('.pagination:last').find('a:first').attr('href');
    if(next_url && next_url != current_url){
      Application.getElem('.pagination:last', next_url+'&scroll=true', false, true);
    }
  }
}