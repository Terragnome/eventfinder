var UrlParams = {};

UrlParams.delParam = function(k){
  let params = UrlParams.getParams();
  delete params[k];
  UrlParams.setParams(params);
}

UrlParams.getParams = function(){
  let paramsObj = {};
  let params = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,k,v) {
      paramsObj[k] = v;
  });
  return paramsObj;
}

UrlParams.getParam = function(p){
    let result = null;
    try{
      result = UrlParams.getParams()[p];
    }catch(e){}
    return result
}

UrlParams.setParams = function(newParams){
  let urlRoot = window.location.href.split("?")[0];
  let origParams = UrlParams.getParams();

  let paramArray = [];
  Object.keys(newParams).forEach(function(k){ origParams[k] = newParams[k]; });
  Object.keys(origParams).forEach(function(k){ paramArray.push(k+"="+origParams[k]); });

  let newUrl = urlRoot;
  if(paramArray){ newUrl = urlRoot+"?"+paramArray.join("&"); }
  console.log(newUrl);
  window.location.href = newUrl;
}

UrlParams.setParam = function(k, v){
    let hash = UrlParams.getParams();
    hash[k] = v;
    UrlParams.setParams(hash);
}