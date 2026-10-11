(function(){
  var d=document.documentElement;
  var reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
  var narrow=matchMedia("(max-width: 900px)");
  var $=function(id){return document.getElementById(id)};
  var firstVisit=!d.classList.contains("seen");
  try{sessionStorage.setItem("afnSeen","1")}catch(e){}
  var tb=$("tb"),prog=$("prog"),dock=$("dock"),scrim=$("scrim"),secs=$("secs");
  function lock(on){document.documentElement.style.overflow=on?"hidden":""}

  /* ---------- Riyadh clock ---------- */
  var tf,df;
  try{tf=new Intl.DateTimeFormat("ar-SA-u-nu-latn",{timeZone:"Asia/Riyadh",hour:"numeric",minute:"2-digit",hour12:true})}catch(e){}
  function tick(){if(tf)$("clk").textContent=tf.format(new Date())}
  tick();setInterval(tick,15000);
  function riyadhNow(){var p={};try{new Intl.DateTimeFormat("en-US",{timeZone:"Asia/Riyadh",year:"numeric",month:"numeric",day:"numeric",hour:"numeric",hourCycle:"h23"}).formatToParts(new Date()).forEach(function(x){p[x.type]=x.value});return{y:+p.year,m:+p.month-1,d:+p.day,h:+p.hour}}catch(e){var n=new Date();return{y:n.getFullYear(),m:n.getMonth(),d:n.getDate(),h:n.getHours()}}}

  /* ---------- top bar: slims while reading down; gold line = progress ---------- */
  var lastY=scrollY,tk=false;
  function onScroll(){
    var y=scrollY,max=document.documentElement.scrollHeight-innerHeight;
    prog.style.transform="scaleX("+(max>0?Math.min(1,y/max):0)+")";
    if(y<120||y<lastY-6)tb.classList.remove("slim");else if(y>lastY+6)tb.classList.add("slim");
    lastY=y;tk=false;
  }
  addEventListener("scroll",function(){if(!tk){tk=true;requestAnimationFrame(onScroll)}},{passive:true});onScroll();

  /* ---------- dock label + current section ---------- */
  var lbl=$("lbl"),cur=lbl.textContent;
  function setLabel(t){if(!t||t===cur)return;cur=t;lbl.classList.add("out");setTimeout(function(){lbl.textContent=t;lbl.classList.remove("out");lbl.classList.add("in");void lbl.offsetWidth;lbl.classList.remove("in")},300)}
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;setLabel(e.target.getAttribute("data-ctx"));var id=e.target.id;if(id)secs.querySelectorAll("a").forEach(function(a){a.classList.toggle("cur",a.getAttribute("href")==="#"+id)})})},{rootMargin:"-50% 0px -50% 0px"});
    document.querySelectorAll("[data-ctx]").forEach(function(s){io.observe(s)});
  }

  /* ---------- sections sheet (phones) ---------- */
  var secBtn=$("secBtn");
  function setSecs(on){secs.classList.toggle("on",on);secs.setAttribute("aria-hidden",on?"false":"true");secBtn.setAttribute("aria-expanded",on?"true":"false");scrim.classList.toggle("on",on||dock.classList.contains("open"))}
  secBtn.addEventListener("click",function(){setSecs(!secs.classList.contains("on"))});
  secs.querySelectorAll("a").forEach(function(a){a.addEventListener("click",function(){setSecs(false)})});

  /* ---------- booking ---------- */
  var SV=[["التمريض المنزلي","n/svc-nursing"],["رعاية كبار السن","n/svc-elderly"],["العلاج الطبيعي","n/svc-physio"],["التحاليل المنزلية","n/svc-lab"],["رعاية الأم والطفل","n/svc-mother"],["زيارة طبيب","n/svc-doctor"],["التغذية العلاجية","n/prg-chronic"],["خدمة أخرى",null]];
  var CITIES=["الرياض","جدة","مكة","المدينة","الدمام والخبر","الطائف","أبها","مدينة أخرى"];
  var P=[{n:"الصباح",r:"8 ص – 12 م",s:8,e:12},{n:"الظهر",r:"12 – 4 م",s:12,e:16},{n:"المساء",r:"4 – 9 م",s:16,e:21},{n:"الليل",r:"9 م – 8 ص",s:21,e:32}];
  var B={},step=1;
  var tiles=$("tiles"),citiesEl=$("cities"),daysEl=$("days"),arc=$("arc"),periods=$("periods");
  var nextB=$("bkNext"),backB=$("bkBack");

  SV.forEach(function(s){var b=document.createElement("button");b.type="button";b.className="tile"+(s[1]?"":" plain");b.innerHTML=(s[1]?'<img src="img/'+s[1]+'.jpg" alt="" loading="lazy">':"")+"<span>"+s[0]+"</span>";b.onclick=function(){B.svc=s[0];paint();setTimeout(function(){go(2)},320)};tiles.appendChild(b)});
  CITIES.forEach(function(c){var b=document.createElement("button");b.type="button";b.className="pill";b.textContent=c;b.onclick=function(){B.city=c;paint()};citiesEl.appendChild(b)});

  var dayList=[];
  function buildDays(){
    daysEl.innerHTML="";dayList=[];var r=riyadhNow();
    var wd,full;try{wd=new Intl.DateTimeFormat("ar-SA-u-ca-gregory-nu-latn",{weekday:"short",timeZone:"UTC"});full=new Intl.DateTimeFormat("ar-SA-u-ca-gregory-nu-latn",{weekday:"long",day:"numeric",month:"long",timeZone:"UTC"})}catch(e){}
    for(var i=0;i<7;i++){
      var d=new Date(Date.UTC(r.y,r.m,r.d+i));
      var o={i:i,label:full?full.format(d):d.toDateString(),short:i===0?"اليوم":(wd?wd.format(d):""),num:d.getUTCDate()};
      dayList.push(o);
      var b=document.createElement("button");b.type="button";b.className="day"+(i===0?" today":"");
      b.innerHTML="<small>"+o.short+"</small><b>"+o.num+"</b>";b.setAttribute("aria-label",o.label);
      (function(o){b.onclick=function(){B.day=o;if(B.p!=null&&isOff(B.p))B.p=null;paint()}})(o);
      daysEl.appendChild(b);
    }
  }
  function isOff(k){if(!B.day||B.day.i!==0)return false;var h=riyadhNow().h;return P[k].e<=h&&k!==3}

  /* time arc */
  var CX=160,CY=172,R=132;
  function pt(a){var t=a*Math.PI/180;return[CX+R*Math.cos(t),CY-R*Math.sin(t)]}
  function seg(a,b){var p1=pt(a),p2=pt(b);return"M"+p1[0].toFixed(1)+" "+p1[1].toFixed(1)+" A"+R+" "+R+" 0 0 0 "+p2[0].toFixed(1)+" "+p2[1].toFixed(1)}
  var NS="http://www.w3.org/2000/svg",segs=[],knob,sun;
  (function(){
    for(var k=0;k<4;k++){var p=document.createElementNS(NS,"path");p.setAttribute("d",seg(k*45+4,k*45+41));p.setAttribute("class","arc-seg");arc.appendChild(p);segs.push(p);
      var lp=pt(k*45+22.5),lx=CX+(lp[0]-CX)*1.2,ly=CY-(CY-lp[1])*1.2;var t=document.createElementNS(NS,"text");t.setAttribute("x",lx.toFixed(1));t.setAttribute("y",(ly+4).toFixed(1));t.setAttribute("text-anchor","middle");t.setAttribute("class","arc-lbl");t.textContent=P[k].n;arc.appendChild(t)}
    var base=document.createElementNS(NS,"line");base.setAttribute("x1","14");base.setAttribute("x2","306");base.setAttribute("y1",CY);base.setAttribute("y2",CY);base.setAttribute("stroke","rgba(244,239,228,.14)");arc.appendChild(base);
    knob=document.createElementNS(NS,"g");sun=document.createElementNS(NS,"circle");sun.setAttribute("r","13");sun.setAttribute("fill","#c9a24e");var halo=document.createElementNS(NS,"circle");halo.setAttribute("r","21");halo.setAttribute("fill","rgba(201,162,78,.22)");knob.appendChild(halo);knob.appendChild(sun);knob.setAttribute("class","knob");arc.appendChild(knob);setKnob(pt(112.5),true);
    P.forEach(function(p,k){var b=document.createElement("button");b.type="button";b.className="pill";b.textContent=p.n;b.onclick=function(){setP(k)};periods.appendChild(b)});
    var drag=false;
    function fromEv(e){var r=arc.getBoundingClientRect(),x=(e.clientX-r.left)*320/r.width,y=(e.clientY-r.top)*190/r.height;var a=Math.atan2(CY-y,x-CX)*180/Math.PI;if(a<0)a=x>CX?0:180;a=Math.max(0,Math.min(180,a));return a}
    function moveTo(a){setKnob(pt(a),true);var k=Math.min(3,Math.floor(a/45));if(!isOff(k))setP(k,true)}
    arc.addEventListener("pointerdown",function(e){drag=true;arc.setPointerCapture(e.pointerId);moveTo(fromEv(e))});
    arc.addEventListener("pointermove",function(e){if(drag)moveTo(fromEv(e))});
    arc.addEventListener("pointerup",function(){drag=false;if(B.p!=null)placeKnob(B.p)});
    arc.addEventListener("pointercancel",function(){drag=false;if(B.p!=null)placeKnob(B.p)});
  })();
  function setKnob(p,instant){if(!knob)return;knob.classList.toggle("drag",!!instant);knob.style.transform="translate("+p[0].toFixed(1)+"px,"+p[1].toFixed(1)+"px)"}
  function placeKnob(k){setKnob(pt(k*45+22.5),false)}
  function setP(k,noKnob){if(isOff(k))return;B.p=k;if(!noKnob)placeKnob(k);paint()}

  function paint(){
    tiles.querySelectorAll(".tile").forEach(function(t,i){t.classList.toggle("sel",SV[i][0]===B.svc)});
    citiesEl.querySelectorAll(".pill").forEach(function(t){t.classList.toggle("sel",t.textContent===B.city)});
    daysEl.querySelectorAll(".day").forEach(function(t,i){t.classList.toggle("sel",!!B.day&&B.day.i===i)});
    segs.forEach(function(s,k){s.classList.toggle("sel",B.p===k);s.classList.toggle("off",isOff(k))});
    periods.querySelectorAll(".pill").forEach(function(t,k){t.classList.toggle("sel",B.p===k);t.classList.toggle("off",isOff(k))});
    var k=B.p!=null?B.p:2;$("pName").textContent=P[k].n;$("pRange").textContent=P[k].r;knob.style.opacity=B.p!=null?1:.35;
    var ok={1:!!B.svc,2:!!(B.city&&B.day),3:B.p!=null,4:true}[step];nextB.disabled=!ok;
  }
  function go(n){
    var from=document.querySelector('.step-p[data-s="'+step+'"]'),to=document.querySelector('.step-p[data-s="'+n+'"]');
    var fwd=n>step;from.classList.add(fwd?"right":"left");from.hidden=true;
    to.classList.remove("left","right");to.classList.add(fwd?"left":"right");to.hidden=false;void to.offsetWidth;to.classList.remove("left","right");
    setTimeout(function(){from.classList.remove("left","right")},600);
    step=n;
    $("bkStep").textContent=n<5?"الخطوة "+n+" من 4":"تذكرة الزيارة";
    $("bars").querySelectorAll("i").forEach(function(b,i){b.classList.toggle("on",i<Math.min(n,4)||n===5)});
    backB.disabled=n===1;$("bkF").hidden=n===5;nextB.textContent=n===4?"أصدر التذكرة":"التالي";
    if(n===3&&B.p==null){var h=riyadhNow().h;var guess=B.day&&B.day.i===0?(h<12?0:h<16?1:h<21?2:3):2;setP(guess)}
    if(n===3&&B.p!=null)placeKnob(B.p);
    paint();to.scrollTop=0;
  }
  nextB.onclick=function(){
    if(step<4){go(step+1);return}
    var name=$("fName").value.trim(),ph=$("fPhone").value.replace(/\D/g,"").replace(/^0/,"");
    if(name.length<2){$("err").textContent="اكتبوا الاسم لو سمحتم.";$("fName").focus();return}
    if(!/^5\d{8}$/.test(ph)){$("err").textContent="رقم الجوال يبدأ بـ 5 ويتكون من 9 أرقام.";$("fPhone").focus();return}
    $("err").textContent="";B.name=name;B.phone="0"+ph;B.note=$("fNote").value.trim();ticket();go(5);
  };
  backB.onclick=function(){if(step>1)go(step-1)};
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
  function ticket(){
    var code="AFN-"+(Math.floor(1000+Math.random()*9000));
    var msg="السلام عليكم، طلب زيارة رقم "+code+"\nالخدمة: "+B.svc+"\nالمدينة: "+B.city+"\nاليوم: "+B.day.label+"\nالفترة: "+P[B.p].n+" ("+P[B.p].r+")\nالاسم: "+B.name+"\nالجوال: "+B.phone+(B.note?"\nملاحظة: "+B.note:"");
    $("ticketBox").innerHTML='<div class="ticket"><div class="tk-top"><span class="chip"><img src="img/mark.png" alt=""></span><div><b>تذكرة زيارة</b><small>أفنان الفائقة للخدمات الطبية المنزلية</small></div><span class="tk-code">'+code+'</span></div>'+
      '<div class="tk-grid"><div class="wide"><small>الخدمة</small><b>'+esc(B.svc)+'</b></div><div><small>اليوم</small><b>'+esc(B.day.label)+'</b></div><div><small>الفترة</small><b>'+P[B.p].n+'<br><span style="font-size:13px;font-weight:500;color:var(--muted)">'+P[B.p].r+'</span></b></div><div><small>المدينة</small><b>'+esc(B.city)+'</b></div><div><small>الاسم</small><b>'+esc(B.name)+'</b></div></div>'+
      '<div class="tk-cut"></div><div class="tk-foot"><a class="send" target="_blank" rel="noopener" href="https://wa.me/966555185244?text='+encodeURIComponent(msg)+'">أرسل التذكرة على واتساب</a><p>نأكد معكم الموعد على واتساب خلال دقائق.</p><button class="edit" type="button" id="tkEdit">تعديل الطلب</button></div></div>';
    $("tkEdit").onclick=function(){go(4)};
  }
  function openBook(svc){
    setSecs(false);buildDays();
    if(svc){B={svc:svc==="زيارات الأطباء"?"زيارة طبيب":svc};}
    var startAt=svc?2:(step===5?1:step);
    if(step===5&&!svc)B={};
    dock.classList.add("open");document.body.classList.add("bk-open");scrim.classList.add("on");$("bookBtn").setAttribute("aria-expanded","true");if(narrow.matches)lock(true);
    document.querySelectorAll(".step-p").forEach(function(s){s.hidden=+s.getAttribute("data-s")!==startAt;s.classList.remove("left","right")});
    step=startAt;go(startAt);
    setTimeout(function(){$("bkX").focus({preventScroll:true})},500);
  }
  function closeBook(){dock.classList.remove("open");document.body.classList.remove("bk-open");if(!secs.classList.contains("on"))scrim.classList.remove("on");$("bookBtn").setAttribute("aria-expanded","false");lock(false)}
  $("bookBtn").onclick=function(){openBook(null)};
  $("bkX").onclick=closeBook;
  scrim.onclick=function(){closeBook();setSecs(false)};
  document.querySelectorAll("[data-book]").forEach(function(b){b.addEventListener("click",function(e){e.preventDefault();openBook(b.getAttribute("data-book")||null)})});
  addEventListener("keydown",function(e){if(e.key!=="Escape")return;if(document.querySelector(".reader.on"))return;if(dock.classList.contains("open"))closeBook();else setSecs(false)});

  /* ---------- page transition (navy panel) ---------- */
  var ptEl=$("pt");
  function lift(){if(!ptEl)return;requestAnimationFrame(function(){ptEl.classList.add("anim");ptEl.classList.remove("cover","home","on")})}
  if(document.readyState==="complete")lift();else addEventListener("load",lift);
  setTimeout(lift,1800);
  addEventListener("pageshow",function(e){if(e.persisted&&ptEl){ptEl.classList.remove("on")}});
  document.addEventListener("click",function(e){
    var a=e.target.closest&&e.target.closest("a[href]");if(!a||a.target==="_blank"||e.metaKey||e.ctrlKey||e.shiftKey)return;
    var h=a.getAttribute("href");if(!/\.html(#.*)?$/.test(h))return;
    var here=location.pathname.split("/").pop()||"index.html",dest=h.split("#")[0];
    if(dest===here&&h.indexOf("#")>-1)return;
    if(!ptEl||reduce)return;
    e.preventDefault();ptEl.classList.remove("anim");ptEl.classList.add("down");void ptEl.offsetWidth;ptEl.classList.add("anim","on");ptEl.classList.remove("down");
    setTimeout(function(){location.href=h},620);
  });

  /* ---------- reveal on scroll (inner pages) ---------- */
  if("IntersectionObserver" in window){
    var rio=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");rio.unobserve(e.target)}})},{rootMargin:"0px 0px -12% 0px"});
    document.querySelectorAll(".rvl,.rv-clip").forEach(function(el){rio.observe(el)});
  }else document.querySelectorAll(".rvl,.rv-clip").forEach(function(el){el.classList.add("in")});

  /* ---------- magnetic buttons (mouse only) ---------- */
  if(window.gsap&&matchMedia("(hover:hover) and (pointer:fine)").matches){
    document.querySelectorAll(".mag").forEach(function(b){
      var xTo=gsap.quickTo(b,"x",{duration:.5,ease:"power3"}),yTo=gsap.quickTo(b,"y",{duration:.5,ease:"power3"});
      b.addEventListener("mousemove",function(e){var r=b.getBoundingClientRect();xTo((e.clientX-r.left-r.width/2)*.25);yTo((e.clientY-r.top-r.height/2)*.35)});
      b.addEventListener("mouseleave",function(){xTo(0);yTo(0)});
    });
  }

  window.AFN={openBook:openBook,lock:lock,reduce:reduce,narrow:narrow,firstVisit:firstVisit};
})();
