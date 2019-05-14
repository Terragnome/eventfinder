var UrlParams = {};

UrlParams.getUrl = function(){
  return window.location.href;
}

UrlParams.getUrlRoot = function(url=null){
  if(!url){ url = UrlParams.getUrl(); }
  return url.split("?")[0];
}

UrlParams.getParams = function(url=null){
  let targetUrl = url ? url : UrlParams.getUrl();

  let paramsObj = {};
  let params = targetUrl.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,k,v) {
      paramsObj[k] = v;
  });
  return paramsObj;
}

UrlParams.getParam = function(p, url=null){
    let result = null;
    try{
      let params = UrlParams.getParams(url);
      result = params[p];
    }catch(e){}
    return result
}

UrlParams.delParam = function(k, url=null){
  let params = UrlParams.getParams(url);
  delete params[k];
  return UrlParams.setParams(params, url);
}

UrlParams.setParams = function(newParams, url=null){
  let urlRoot = UrlParams.getUrlRoot(url);
  let origParams = UrlParams.getParams(url);

  let paramArray = [];
  Object.keys(newParams).forEach(function(k){ origParams[k] = newParams[k]; });
  Object.keys(origParams).forEach(function(k){ paramArray.push(k+"="+origParams[k]); });

  let newUrl = urlRoot;
  if(paramArray){ newUrl = urlRoot+"?"+paramArray.join("&"); }
  // window.location.href = newUrl;
  return newUrl;
}

UrlParams.setParam = function(k, v, url=null){
    let hash = UrlParams.getParams(url);
    hash[k] = v;
    UrlParams.setParams(hash, url);
}