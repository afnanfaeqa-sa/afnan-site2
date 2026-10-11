(function(){
  var A=window.AFN||{};
  var ARTICLES={{ARTICLES_JSON}};
  var reduce=A.reduce,narrow=A.narrow;
  var $=function(id){return document.getElementById(id)};
  var hero=$("hero");
  /* ---------- services on phones: swipe or arrows ---------- */
  (function(){
    var tr=$("svcTrack"),now=$("svcNow"),pv=$("svcPrev"),nx=$("svcNext");
    function stepW(){var c=tr.querySelector(".card");return c?c.getBoundingClientRect().width+28:300}
    function idx(){return Math.round(Math.abs(tr.scrollLeft)/stepW())}
    function upd(){if(!narrow.matches)return;var i=Math.min(5,idx());now.textContent="0"+(i+1);pv.disabled=i<=0;nx.disabled=i>=5}
    tr.addEventListener("scroll",function(){requestAnimationFrame(upd)},{passive:true});
    function to(i){i=Math.max(0,Math.min(5,i));var c=tr.querySelectorAll(".card")[i];if(c)c.scrollIntoView({behavior:reduce?"auto":"smooth",block:"nearest",inline:"center"})}
    nx.onclick=function(){to(idx()+1)};pv.onclick=function(){to(idx()-1)};upd();
  })();

  /* ---------- reviews ---------- */
  var rvItems=[].slice.call(document.querySelectorAll(".rv-item")),rvNav=$("rvNav"),rvI=0,rvT;
  rvItems.forEach(function(it,i){var p=it.querySelector("p");p.innerHTML=p.textContent.split(" ").map(function(w,k){return'<span class="w" style="transition-delay:'+(k*0.035).toFixed(3)+'s">'+w+"</span>"}).join(" ");
    var b=document.createElement("button");b.type="button";b.setAttribute("role","tab");b.setAttribute("aria-label","رأي "+(i+1));b.onclick=function(){showRv(i)};rvNav.appendChild(b)});
  function showRv(i){rvI=i;rvItems.forEach(function(it,k){it.classList.toggle("on",k===i)});[].forEach.call(rvNav.children,function(b,k){b.classList.remove("on");if(k===i){void b.offsetWidth;b.classList.add("on")}});clearTimeout(rvT);if(!reduce)rvT=setTimeout(function(){showRv((rvI+1)%rvItems.length)},7000)}
  if(rvItems.length)showRv(0);

  /* ---------- FAQ ---------- */
  document.querySelectorAll(".qa button").forEach(function(b){b.addEventListener("click",function(){var q=b.parentNode,on=!q.classList.contains("on");q.classList.toggle("on",on);b.setAttribute("aria-expanded",on?"true":"false")})});

  /* ---------- article reader ---------- */
  var reader=$("reader"),lastArt=null;
  document.querySelectorAll(".ac").forEach(function(c){c.addEventListener("click",function(){var a=ARTICLES[c.getAttribute("data-a")];if(!a)return;lastArt=a;
    $("rImg").src=a.image;$("rMeta").textContent=a.label+" · "+a.minutes+" دقائق قراءة";$("rTitle").textContent=a.title;$("rBody").innerHTML=a.html;
    reader.classList.add("on");reader.setAttribute("aria-hidden","false");reader.scrollTop=0;A.lock(true);setTimeout(function(){$("rx").focus({preventScroll:true})},400)})});
  function closeReader(){reader.classList.remove("on");reader.setAttribute("aria-hidden","true");A.lock(false)}
  $("rx").onclick=closeReader;
  $("rBook").onclick=function(){closeReader();setTimeout(function(){A.openBook(lastArt&&lastArt.service||null)},350)};

  addEventListener("keydown",function(e){if(e.key==="Escape"&&reader.classList.contains("on"))closeReader()});

  /* ---------- statement words, journey ---------- */
  var say=$("sayText");
  say.innerHTML=say.textContent.split(" ").map(function(w){return'<span class="w">'+w+"</span>"}).join(" ");
  var sw=say.querySelectorAll(".w");
  var steps=[].slice.call(document.querySelectorAll(".step")),pics=[].slice.call(document.querySelectorAll("#jrMedia img"));
  function setStep(i){steps.forEach(function(s,k){s.classList.toggle("on",k<=i)});pics.forEach(function(p,k){p.classList.toggle("on",k===i)})}

  var curtain=$("curtain");
  if(!window.gsap||reduce){
    if(curtain)curtain.remove();
    sw.forEach(function(w){w.style.opacity=1});setStep(3);$("fill").style.transform="scaleY(1)";
    return;
  }
  gsap.registerPlugin(ScrollTrigger);
  var E="expo.out";

  var tl=gsap.timeline();
  if(A.firstVisit&&curtain){tl.to("#curtain i",{scaleX:1,duration:.7,ease:"power3.inOut"})
    .to("#curtain .mark",{y:-14,opacity:0,duration:.45,ease:"power2.in"},"+=.1")
    .to("#curtain",{yPercent:-100,duration:.95,ease:"expo.inOut"},"-=.05")
    .set("#curtain",{display:"none"})}else{if(curtain)curtain.remove();tl.to({},{duration:.55})}
  tl.from("#heroImg",{scale:1.25,duration:2.2,ease:E},"-=.85")
    .from("#h .w",{yPercent:110,rotate:4,duration:1.15,stagger:.07,ease:E},"-=1.9")
    .from(".h-in",{y:28,opacity:0,duration:1,stagger:.1,ease:E},"-=.9")
    .from(".tb-in > .tb-side",{y:-24,opacity:0,duration:1,stagger:.08,ease:E,clearProps:"transform,opacity"},"-=1.1")
    .from(".hang",{yPercent:-120,duration:1.2,ease:"elastic.out(1,.6)",clearProps:"transform"},"-=1")
    .from("#dock",{y:140,opacity:0,duration:1.1,ease:E,clearProps:"transform,opacity"},"-=.9");

  gsap.to("#heroImg",{yPercent:12,ease:"none",scrollTrigger:{trigger:hero,start:"top top",end:"bottom top",scrub:true}});
  gsap.to(".hero .copy",{y:-80,opacity:.15,ease:"none",scrollTrigger:{trigger:hero,start:"center center",end:"bottom top",scrub:true}});

  var loop=gsap.to("#mq",{xPercent:-50,duration:38,ease:"none",repeat:-1});
  ScrollTrigger.create({onUpdate:function(self){var v=Math.min(Math.abs(self.getVelocity())/350,6);gsap.to(loop,{timeScale:1+v,duration:.2,overwrite:true});gsap.to(loop,{timeScale:1,duration:1.2,delay:.25,ease:"power2.out"})}});

  var mm=gsap.matchMedia();
  mm.add("(min-width: 901px)",function(){
    var track=$("svcTrack"),now=$("svcNow");
    var dist=function(){return Math.max(0,track.scrollWidth-innerWidth)};
    gsap.to(track,{x:dist,ease:"none",scrollTrigger:{trigger:"#svcPin",start:"top top",end:function(){return"+="+dist()},pin:true,scrub:.8,invalidateOnRefresh:true,onUpdate:function(s){now.textContent="0"+Math.min(6,1+Math.round(s.progress*5))}}});
  });
  gsap.utils.toArray(".card .ph").forEach(function(ph,i){
    gsap.from(ph,{clipPath:"inset(100% 0 0 0)",duration:1.4,ease:"expo.inOut",delay:(i%3)*.08,scrollTrigger:{trigger:"#services",start:"top 70%"}});
    gsap.from(ph.querySelector("img"),{scale:1.35,duration:1.8,ease:E,delay:(i%3)*.08,scrollTrigger:{trigger:"#services",start:"top 70%"}});
  });
  gsap.from(".svc-head > *",{y:40,opacity:0,duration:1.1,stagger:.1,ease:E,scrollTrigger:{trigger:"#services",start:"top 75%"}});

  /* programs: each card shrinks back as the next one slides over it */
  var cards=gsap.utils.toArray(".pc");
  cards.forEach(function(c,i){if(i===cards.length-1)return;gsap.to(c,{scale:.92-(cards.length-2-i)*0.01,opacity:.55,ease:"none",scrollTrigger:{trigger:cards[i+1],start:"top bottom",end:"top 160px",scrub:true}})});
  gsap.from(".prg-head > *",{y:40,opacity:0,duration:1.1,stagger:.1,ease:E,scrollTrigger:{trigger:"#programs",start:"top 75%"}});

  gsap.to(sw,{opacity:1,stagger:.05,ease:"none",scrollTrigger:{trigger:say,start:"top 80%",end:"bottom 45%",scrub:true}});
  gsap.from(".pt",{y:40,opacity:0,duration:1,stagger:.1,ease:E,scrollTrigger:{trigger:".pts",start:"top 85%"}});

  gsap.to("#fill",{scaleY:1,ease:"none",scrollTrigger:{trigger:"#steps",start:"top 60%",end:"bottom 60%",scrub:true}});
  steps.forEach(function(s,i){ScrollTrigger.create({trigger:s,start:"top 62%",end:"bottom 62%",onToggle:function(st){if(st.isActive)setStep(i)}})});
  gsap.from(".jr-head > *",{y:40,opacity:0,duration:1.1,stagger:.1,ease:E,scrollTrigger:{trigger:"#journey",start:"top 75%"}});
  gsap.from("#jrMedia",{clipPath:"inset(0 0 100% 0)",duration:1.5,ease:"expo.inOut",scrollTrigger:{trigger:"#journey",start:"top 70%"}});

  gsap.from(".ac",{y:60,opacity:0,duration:1.2,stagger:.08,ease:E,scrollTrigger:{trigger:".agrid",start:"top 80%"}});
  gsap.utils.toArray(".ac .ph").forEach(function(ph){gsap.from(ph,{clipPath:"inset(0 0 100% 0)",duration:1.4,ease:"expo.inOut",scrollTrigger:{trigger:ph,start:"top 88%"}})});
  gsap.from(".sec-head > div > *",{y:36,opacity:0,duration:1.1,stagger:.08,ease:E,scrollTrigger:{trigger:"#guide",start:"top 75%"}});
  gsap.from(".qa",{y:30,opacity:0,duration:1,stagger:.07,ease:E,scrollTrigger:{trigger:"#qaList",start:"top 80%"}});
  gsap.from(".ptn-ph",{clipPath:"inset(100% 0 0 0)",duration:1.6,ease:"expo.inOut",scrollTrigger:{trigger:"#partners",start:"top 70%"}});
  gsap.from(".who-list div",{x:-40,opacity:0,duration:1,stagger:.08,ease:E,scrollTrigger:{trigger:".who-list",start:"top 85%"}});

  gsap.from(".end .wrap > *",{y:50,opacity:0,duration:1.2,stagger:.1,ease:E,scrollTrigger:{trigger:".end",start:"top 72%"}});
  gsap.from(".end .arch",{yPercent:30,opacity:0,duration:2,stagger:.15,ease:E,scrollTrigger:{trigger:".end",start:"top 80%"}});

  addEventListener("load",function(){ScrollTrigger.refresh()});
})();
