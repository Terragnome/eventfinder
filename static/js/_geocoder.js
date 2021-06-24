var Geocoder = Geocoder || {};

Geocoder.getLocation = function() {
  if(navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(Geocoder.onReady);
  } else {
  }
}

Geocoder.onReady = function(position) {
  Geocoder.latitude = position.coords.latitude;
  Geocoder.longitude = position.coords.longitude;

  let params = {'lat': Geocoder.latitude, 'lon': Geocoder.longitude};
  $.post(Application.urlGeo, params, {
  }).done(function(response) {
  }).fail(function(xhr, status, error) {
    console.log(error);
  });
}