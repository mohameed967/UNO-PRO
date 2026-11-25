const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }
const headers = {"Content-Type":"application/json"};
if (tg?.initData) headers["X-Telegram-Init-Data"] = tg.initData;

const $ = id => document.getElementById(id);
let state = null;
const colorNames = {red:"أحمر",yellow:"أصفر",green:"أخضر",blue:"أزرق"};
const valueNames = {skip:"تخطي",reverse:"عكس",draw2:"+2",wild:"تغيير اللون",wild4:"+4"};

function showToast(text){$("toast").textContent=text;$("toast").classList.remove("hidden");setTimeout(()=>$("toast").classList.add("hidden"),2500)}
async function api(path, method="GET", body=null){
  const res=await fetch(path,{method,headers,...(body?{body:JSON.stringify(body)}:{})});
  const data=await res.json().catch(()=>({detail:"خطأ غير معروف"}));
  if(!res.ok) throw new Error(data.detail||"حدث خطأ");
  return data;
}
function label(card){return valueNames[card.value]||card.value}
function colorClass(card){return card.color||"wild"}
function renderCard(card, big=false, playable=false){
  const el=document.createElement("button");
  el.className=`card ${colorClass(card)} ${playable?"":"not-playable"} ${big?"big":""}`;
  el.textContent=label(card); el.title=card.color?colorNames[card.color]: "ورقة خاصة";
  return el;
}
function render(){
  $("welcome").classList.add("hidden");$("game").classList.remove("hidden");
  $("aiCount").textContent=`${state.ai_count} أوراق`;
  $("topCard").className=`card big ${colorClass(state.top_card)}`;
  $("topCard").textContent=label(state.top_card);
  $("colorText").textContent=`اللون الحالي: ${state.current_color_ar}`;
  $("message").textContent=state.message;
  $("handCount").textContent=`(${state.hand.length})`;
  $("turnText").textContent=state.status==="finished"?"انتهت المباراة":state.turn==="player"?"دورك":"دور الكمبيوتر";
  $("drawBtn").disabled=state.status!=="playing"||state.turn!=="player";
  const hand=$("hand");hand.innerHTML="";
  state.hand.forEach(card=>{
    const playable=state.playable_ids.includes(card.id);
    const el=renderCard(card,false,playable);
    el.addEventListener("click",()=>play(card));
    hand.appendChild(el);
  });
  if(state.status==="finished") showToast(state.winner==="player"?"🏆 فزت بالمباراة!":"🤖 فاز الكمبيوتر!");
}
async function loadNew(){
  try{state=await api("/api/game/new","POST",{});render()}
  catch(e){showToast(e.message)}
}
async function play(card){
  if(!state.playable_ids.includes(card.id)){showToast("هذه الورقة غير قابلة للعب الآن");return}
  let chosen_color=null;
  if(!card.color){
    const choice=prompt("اختر اللون: red أو yellow أو green أو blue","red");
    const allowed=["red","yellow","green","blue"];
    if(!allowed.includes((choice||"").toLowerCase())){showToast("لون غير صالح");return}
    chosen_color=choice.toLowerCase();
  }
  try{state=await api("/api/game/play","POST",{card_id:card.id,chosen_color});render()}
  catch(e){showToast(e.message)}
}
$("newGame").addEventListener("click",loadNew);
$("newBtn").addEventListener("click",loadNew);
$("drawBtn").addEventListener("click",async()=>{
  try{state=await api("/api/game/draw","POST",{});render()}
  catch(e){showToast(e.message)}
});
(async()=>{
  try{state=await api("/api/game");render()}
  catch(_){/* no active game yet */}
})();
