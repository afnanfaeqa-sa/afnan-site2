(function(){
  var S=window.AFN_STORIES||[],sv=document.getElementById("sv"),logo=document.getElementById("logoSt");if(!sv||!S.length||!logo)return;
  var $=function(id){return document.getElementById(id)},bars=$("svBars"),hint=$("stHint"),i=0,t=null,A=window.AFN||{};
  function get(k){try{return sessionStorage.getItem(k)}catch(e){return null}}
  function put(k){try{sessionStorage.setItem(k,"1")}catch(e){}}
  if(get("afnStSeen"))logo.classList.add("seen");
  S.forEach(function(){var b=document.createElement("i");b.appendChild(document.createElement("b"));bars.appendChild(b)});
  function show(k){
    if(k<0)k=0;if(k>=S.length){close();return}
    i=k;var s=S[k];
    [].forEach.call(bars.children,function(b,n){b.className=n<k?"done":""});
    var img=$("svImg");img.style.animation="none";img.src=s.img;void img.offsetWidth;img.style.animation="";
    $("svT").textContent=s.t;$("svH").textContent=s.h;$("svP").textContent=s.p;var c=$("svCta");c.textContent=s.cta+" ←";c.href=s.href;
    var cur=bars.children[k];void cur.offsetWidth;cur.className="run";
    var copy=sv.querySelector(".sv-copy");copy.style.display="none";void copy.offsetWidth;copy.style.display="";
    clearTimeout(t);t=setTimeout(function(){show(i+1)},5000);
  }
  function open(k){hideHint();sv.classList.add("on");sv.setAttribute("aria-hidden","false");if(A.lock)A.lock(true);show(k||0);logo.classList.add("seen");put("afnStSeen");setTimeout(function(){$("svX").focus({preventScroll:true})},300)}
  function close(){clearTimeout(t);sv.classList.remove("on");sv.setAttribute("aria-hidden","true");if(A.lock)A.lock(false);logo.focus({preventScroll:true})}
  logo.addEventListener("click",function(){open(0)});
  $("svX").onclick=close;$("svNext").onclick=function(){show(i+1)};$("svPrev").onclick=function(){show(i-1)};
  $("svCta").addEventListener("click",function(){clearTimeout(t);setTimeout(close,700)});
  addEventListener("keydown",function(e){if(!sv.classList.contains("on"))return;if(e.key==="Escape")close();if(e.key==="ArrowLeft")show(i+1);if(e.key==="ArrowRight")show(i-1)});
  /* one gentle hint per visit, until the stories are opened */
  function hideHint(){if(hint)hint.hidden=true}
  if(hint&&!get("afnStSeen")&&!get("afnStHint")){
    var first=A.firstVisit&&document.getElementById("curtain");
    setTimeout(function(){if(logo.classList.contains("seen"))return;hint.hidden=false;put("afnStHint");setTimeout(hideHint,6000)},first?4200:1600);
    addEventListener("scroll",function(){if(scrollY>200)hideHint()},{passive:true});
    hint.addEventListener("click",function(){open(0)});
  }
})();
