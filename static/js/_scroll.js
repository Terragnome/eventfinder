var Scroll = Scroll || {};

Scroll.init = function(){
  $('#scroll_top').unbind('click', Scroll.top);
  $('#scroll_top').click(Scroll.top);
  $(document).scroll(Scroll.onScroll);
}

Scroll.onScroll = function(e){
  let scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
  let cutoff = 500;
  console.log(scrollPosition)
  if(scrollPosition > cutoff){
    $('#scroll_top').show();
    $('#scroll_top').removeClass('anim_fade_out');
    $('#scroll_top').addClass('anim_fade_in');
  }else{
    $('#scroll_top').removeClass('anim_fade_in');
    $('#scroll_top').addClass('anim_fade_out');
  }
}

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