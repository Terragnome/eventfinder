var Scroll = Scroll || {};

Scroll.top = function(y) {
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;
}

Scroll.disable = function() {
  $(window).off("scroll", Scroll.getNext);
}

Scroll.enable = function() {
  Scroll.disable();
  $(window).on("scroll", Scroll.getNext);
}

Scroll.getNext = function(){
  let scrollHeight = $(document).height();
  let scrollPosition = $(window).height()+$(window).scrollTop();

  if((scrollHeight-scrollPosition)/scrollHeight === 0){
    let current_url = window.location.pathname+window.location.search;
    let next_url = $('.pagination:last').find('a:first').attr('href');
    if(next_url && next_url != current_url){
      Application.getElem('.pagination:last', next_url+'&scroll=true', false, true, true);
    }
  }
}