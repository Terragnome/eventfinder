var Geocoder = Geocoder || {};

Geocoder.getLocation = function(e) {
  e.preventDefault();

  let currentTarget = $(e.currentTarget);

  let onDefault = function(event){
    let data = Application.ajaxData(e);
    let url = currentTarget.attr('href');
    Application.getElem(data.target, url);  
  }

  if( currentTarget.hasClass('selected') || !navigator.geolocation ) {
    onDefault(e);
  }else{
    let geoOptions = {
      timeout: 3 * 1000,
      // maximumAge: 5 * 60 * 1000,
      // enableHighAccuracy: true
    };

    let onSuccess = function(position){
      Geocoder.onReady(position);

      let data = Application.ajaxData(e);
      let url = new URL(currentTarget.attr('href'));
      url.searchParams.set('lat', Geocoder.latitude);
      url.searchParams.set('lon', Geocoder.longitude);
      url = url.toString()

      Application.getElem(data.target, url);
    };

    let onError = function(error) {
      Spinner.hide(Application.mainSpinner);
      onDefault(e);
    };

    navigator.geolocation.getCurrentPosition(onSuccess, onError, geoOptions);
    Spinner.show(Application.mainSpinner);
  }
}

Geocoder.onReady = function(position) {
  Geocoder.latitude = position.coords.latitude;
  Geocoder.longitude = position.coords.longitude;
}