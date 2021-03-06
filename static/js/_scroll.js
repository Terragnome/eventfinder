var Scroll = Scroll || {};

Scroll.init = function(){
  $('#scroll_top').unbind('click', Scroll.onScrollTopClick);
  $('#scroll_top').click(Scroll.onScrollTopClick);
  $(document).unbind('scroll', Scroll.onScroll);
  $(document).scroll(Scroll.onScroll);
}

Scroll.onScroll = function(e){
  let scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
  let cutoff = 500;

  if(scrollPosition > cutoff){
    $('#scroll_top').show();
    $('#scroll_top').removeClass('anim_fade_out');
    $('#scroll_top').addClass('anim_fade_in');
  }else{
    $('#scroll_top').removeClass('anim_fade_in');
    $('#scroll_top').addClass('anim_fade_out');
  }
}

Scroll.onScrollTopClick = function(e){
  Scroll.top(4000);
}

Scroll.top = function(speed=0, max_duration=750){
  Scroll.to(0, speed, max_duration);
}

Scroll.to = function(y, speed=0, max_duration=1000){
  let dist = document.body.scrollTop || document.documentElement.scrollTop;

  if(speed == 0){
    document.body.scrollTop = y;
    document.documentElement.scrollTop = y;
  }else{
    let duration = Math.min(dist*1.0/speed*1000, max_duration);

    $('html, body').animate({
      'scrollTop': y
    }, duration);
  }
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

  if((scrollHeight-scrollPosition)/scrollHeight < 0.1){
    Scroll.disable();
    let nextUrl = $('.pagination:last').find('a:first').attr('href');
    if(nextUrl){
      if(Scroll.lastScrollUrl != nextUrl){
        Scroll.lastScrollUrl = nextUrl;
        let pushUrl = UrlParams.delParam('scroll');
        Application.getElem('.pagination:last', nextUrl+'&scroll=true', nextUrl, true, true, false, '#events_spinner');
      }
    }
  }
}