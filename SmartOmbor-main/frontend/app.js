// SmartOmbor frontend — fetch() -> window.API_BASE (see config.js)
window.__smartOmborLoaded = true;
(function(){
"use strict";
const API = (window.API_BASE || "http://127.0.0.1:8000/api").replace(/\/$/, "");
let access = localStorage.getItem("access") || "";
let refresh = localStorage.getItem("refresh") || "";
let me = null;

const $ = s => document.querySelector(s);
function showErr(msg){
  const a = $("#alert");
  if(!msg){ a.classList.add("hidden"); a.textContent=""; return; }
  a.textContent = msg; a.classList.remove("hidden");
}
function esc(t){ return (t??"").toString().replace(/[&<>"']/g, m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m])); }

async function api(path, opts={}){
  const headers = Object.assign({"Content-Type":"application/json"}, opts.headers||{});
  if (access) headers.Authorization = "Bearer " + access;
  const init = Object.assign({}, opts, {headers});
  let res;
  try{ res = await fetch(API + path, init); }
  catch(e){ const m = "Tarmoq xatosi: " + e.message + " (API: " + API + path + ") — backend " + API + " ishlayaptimi?"; showErr(m); throw new Error(m); }
  if (res.status===401 && refresh && !path.includes("/auth/")){
    try{
      const r = await fetch(API+"/auth/token/refresh/", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({refresh})});
      if (r.ok){ const d = await r.json(); access=d.access; localStorage.setItem("access", access); headers.Authorization="Bearer "+access; res = await fetch(API+path, Object.assign({}, opts, {headers})); }
      else { doLogout(); }
    }catch(_){ doLogout(); }
  }
  const txt = await res.text();
  let data; try{ data = txt ? JSON.parse(txt) : null; }catch{ data = txt; }
  if (!res.ok){
    const msg = typeof data==="string" ? data : ((data&&data.detail) || (data&&Object.values(data).join("; ")) || JSON.stringify(data));
    showErr("API " + res.status + " ("+path+"): " + msg);
    throw new Error(msg);
  }
  showErr(""); return data;
}
function doLogout(){ localStorage.removeItem("access"); localStorage.removeItem("refresh"); access=""; refresh=""; me=null; show("login"); }

async function loadMe(){
  if (!access){ show("login"); return; }
  try{ me = await api("/auth/me/"); }
  catch(_){ doLogout(); return; }
  $("#nav").classList.remove("hidden");
  $("#navUser").textContent = me.username;
  $("#footUser").textContent = me.username + " (" + (me.role||"") + ")";
  const isR = me.is_superuser || me.role==="Rahbar";
  $("#navRahbar").classList.toggle("hidden", !isR);
  show(me.is_superuser || (me.groups||[]).includes("Rahbar") ? "dashboard" : "products");
}

function show(page){
  document.querySelectorAll("main section").forEach(s=>s.classList.add("hidden"));
  const sec = $("#page-"+page);
  if (sec) sec.classList.remove("hidden");
  document.querySelectorAll("#nav .sidebar-link").forEach(a=>a.classList.toggle("active", a.dataset.page===page));
  $("#pageHeading").textContent = "SmartOmbor — " + page.replace("_"," ");
  try{ if (history.replaceState) history.replaceState(null, "", "#" + page); }catch(_){}
  const loaders = { dashboard:loadDashboard, products:loadProducts, categories:loadCats, movements:loadMovs,
    orders:()=>loadOrders(false), manager_orders:()=>loadOrders(true),
    users:loadUsers, sellers_report:loadSellers, inventory_report:loadInvReport, profile:loadProfile };
  const fn = loaders[page]; if (fn) Promise.resolve().then(fn).catch(e=>showErr(e.message));
}
function paginate(d){ return Array.isArray(d)?d:((d&&d.results)||[]); }

async function loadDashboard(){
  const d = await api("/reports/dashboard/").catch(()=>null); if(!d) return;
  $("#dOrders").textContent = (d.davr&&d.davr.buyurtmalar_soni) ?? 0;
  $("#dSum").textContent = (d.davr&&d.davr.savdo_summasi) ?? 0;
  $("#dProfit").textContent = (d.davr&&d.davr.foyda) ?? 0;
  $("#dTop").innerHTML = ((d.davr_top_mahsulotlar||[]).map(p=>"<li>"+esc(p.product__nomi)+" — "+p.jami_soni+"</li>").join("")) || "—";
  $("#dLow").innerHTML = ((d.kam_qolgan||[]).map(p=>"<span class='badge bg-warning'>"+esc(p.nomi)+": "+p.qoldiq+"</span>").join(" ")) || "—";
}
async function loadProducts(){
  const qv = $("#prodQ").value; const q = qv? "?q="+encodeURIComponent(qv):"";
  const d = await api("/products/"+q); if(!d) return;
  $("#prodList").innerHTML = "<table class='table'><thead><tr><th>ID</th><th>Nom</th><th>Kat</th><th>Xarid</th><th>Sotish</th><th>Qoldiq</th></tr></thead><tbody>" +
    paginate(d).map(p=>"<tr><td>"+p.id+"</td><td>"+esc(p.nomi)+"</td><td>"+esc(p.category_nomi||p.category)+"</td><td>"+p.xarid_narxi+"</td><td>"+p.sotish_narxi+"</td><td>"+p.qoldiq+"</td></tr>").join("") + "</tbody></table>";
}
async function loadCats(){
  const d = await api("/categories/"); if(!d) return;
  $("#catList").innerHTML = paginate(d).map(c=>"<div><b>"+esc(c.nomi)+"</b> — "+esc(c.description||"")+"</div>").join("") || "—";
}
async function loadMovs(){
  const qv = $("#movQ").value; const q = qv? "?q="+encodeURIComponent(qv):"";
  const d = await api("/movements/"+q); if(!d) return;
  $("#movList").innerHTML = "<table class='table'><thead><tr><th>#</th><th>Mahsulot</th><th>Turi</th><th>Miqdor</th><th>Sabab</th><th>Kim</th></tr></thead><tbody>" +
    paginate(d).map(m=>"<tr><td>"+m.id+"</td><td>"+esc(m.product_nomi||m.product)+"</td><td>"+m.movement_type+"</td><td>"+m.nechta+"</td><td>"+esc(m.sababi||"")+"</td><td>"+esc(m.user_username||"")+"</td></tr>").join("") + "</tbody></table>";
}
async function loadOrders(manager){
  $("#ordersTitle").textContent = manager ? "Barcha buyurtmalar (manager)" : "Mening buyurtmalarim";
  const qv = $("#ordQ").value; const q = qv? "?q="+encodeURIComponent(qv):"";
  const base = manager ? "/manager/orders/" : "/orders/";
  window._orderBase = base;
  const d = await api(base+q); if(!d) return;
  $("#ordList").innerHTML = "<table class='table'><thead><tr><th>#</th><th>Mijoz</th><th>Status</th><th>Jami</th><th>Amal</th></tr></thead><tbody>" +
    paginate(d).map(o=>"<tr><td>"+o.id+"</td><td>"+esc(o.customer_username||o.customer)+"</td><td><span class='badge bg-secondary'>"+o.status+"</span></td><td>"+o.total_price+"</td><td class='d-flex gap-1'>"+
      "<button class='btn btn-sm btn-outline-primary' onclick='finishOrder("+o.id+")'>Yakunla</button>"+
      "<button class='btn btn-sm btn-outline-warning' onclick='cancelOrder("+o.id+")'>Bekor</button>"+
      "<button class='btn btn-sm btn-outline-danger' onclick='delOrder("+o.id+")'>O'chirish</button>"+
      "<button class='btn btn-sm btn-outline-secondary' onclick='detailOrder("+o.id+")'>Batafsil</button></td></tr>").join("") + "</tbody></table>";
}
window.finishOrder=async(id)=>{ try{ await api((window._orderBase||"/orders/")+id+"/finish/",{method:"POST"}); loadOrders((window._orderBase||"").includes("manager")); }catch(e){} };
window.cancelOrder=async(id)=>{ try{ await api((window._orderBase||"/orders/")+id+"/cancel/",{method:"POST"}); loadOrders((window._orderBase||"").includes("manager")); }catch(e){} };
window.delOrder=async(id)=>{ try{ await api((window._orderBase||"/orders/")+id+"/",{method:"DELETE"}); loadOrders((window._orderBase||"").includes("manager")); }catch(e){} };
window.detailOrder=async(id)=>{ try{ const o=await api((window._orderBase||"/orders/")+id+"/"); $("#ordDetail").innerHTML="<div class='card p-3'><h6>#"+o.id+" — "+o.status+" — "+o.total_price+"</h6><ul>"+((o.items||[]).map(i=>"<li>"+esc(i.product_nomi)+" x"+i.soni+" = "+i.subtotal+"</li>").join(""))+"</ul></div>"; }catch(e){} };
async function loadUsers(){
  const d = await api("/users/"); if(!d) return;
  $("#userList").innerHTML = "<table class='table'><thead><tr><th>ID</th><th>Login</th><th>Ism</th><th>Rol</th><th>Faol</th><th></th></tr></thead><tbody>" +
    paginate(d).map(u=>"<tr><td>"+u.id+"</td><td>"+esc(u.username)+"</td><td>"+esc(u.first_name)+" "+esc(u.last_name)+"</td><td>"+esc(u.role||"")+"</td><td>"+u.is_active+"</td><td><button class='btn btn-sm btn-outline-warning' onclick='toggleUser("+u.id+")'>Toggle</button></td></tr>").join("") + "</tbody></table>";
}
window.toggleUser=async(id)=>{ try{ await api("/users/"+id+"/toggle-status/",{method:"POST"}); loadUsers(); }catch(e){} };
async function loadSellers(){
  const d = await api("/reports/sellers/"); if(!d) return;
  $("#sellerList").innerHTML = "<table class='table'><thead><tr><th>Sotuvchi</th><th>Buyurtma</th><th>Savdo</th></tr></thead><tbody>" +
    ((d.sotuvchilar||[]).map(s=>"<tr><td>"+esc(s.customer__username)+"</td><td>"+s.jami_buyurtmalar+"</td><td>"+s.savdo_summasi+"</td></tr>").join("")) + "</tbody></table>" +
    "<a class='btn btn-outline-primary mt-2' href='"+API+"/reports/export/sellers/excel/' target='_blank'>Excel</a> <a class='btn btn-outline-danger mt-2' href='"+API+"/reports/export/sellers/pdf/' target='_blank'>PDF</a>";
}
async function loadInvReport(){
  const d = await api("/reports/inventory/"); if(!d) return;
  $("#invReport").innerHTML = "<p>Kirim: "+d.jami_kirim+" · Chiqim: "+d.jami_chiqim+"</p>" +
    "<table class='table'><thead><tr><th>Mahsulot</th><th>Kirim</th><th>Chiqim</th><th>Qoldiq</th></tr></thead><tbody>" +
    ((d.mahsulotlar||[]).map(p=>"<tr><td>"+esc(p.nomi)+"</td><td>"+p.jami_kirim+"</td><td>"+p.jami_chiqim+"</td><td>"+p.qoldiq+"</td></tr>").join("")) + "</tbody></table>" +
    "<a class='btn btn-outline-primary' href='"+API+"/reports/export/inventory/excel/' target='_blank'>Excel</a> <a class='btn btn-outline-danger' href='"+API+"/reports/export/inventory/pdf/' target='_blank'>PDF</a>";
}
async function loadProfile(){ $("#profileJson").textContent = JSON.stringify(me,null,2); }

async function init(){
  $("#loginForm").addEventListener("submit", async e=>{
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit], button");
    const old = btn ? btn.textContent : "";
    if (btn){ btn.disabled = true; btn.textContent = "Kirish..."; }
    showErr("");
    const f = new FormData(e.target);
    try{
      const r = await fetch(API+"/auth/token/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:f.get("username"),password:f.get("password")})});
      if(!r.ok){
        let msg = "Login yoki parol xato (HTTP "+r.status+")";
        try{ const d = await r.json(); msg = (d.detail||JSON.stringify(d)) + " (HTTP "+r.status+")"; }catch(_){}
        showErr(msg); console.error("login failed", msg); return;
      }
      const d = await r.json(); access=d.access; refresh=d.refresh;
      localStorage.setItem("access",access); localStorage.setItem("refresh",refresh);
      await loadMe();
    }catch(err){ showErr("Kirishda xato: " + err.message); console.error(err); }
    finally{ if (btn){ btn.disabled = false; btn.textContent = old || "Kirish"; } }
  });
  $("#logoutBtn").addEventListener("click", doLogout);
  document.querySelectorAll("#nav .sidebar-link").forEach(a=>a.addEventListener("click",()=>show(a.dataset.page)));
  $("#prodSearch").addEventListener("click", loadProducts);
  $("#prodNew").addEventListener("click", async ()=>{
    const nomi=prompt("Mahsulot nomi"); if(!nomi) return;
    const c = await api("/categories/"); const catId = paginate(c)[0] && paginate(c)[0].id;
    if(!catId){showErr("Avval kategoriya yarating");return;}
    const xarid=prompt("Xarid narxi"), sotish=prompt("Sotish narxi");
    await api("/products/",{method:"POST",body:JSON.stringify({nomi:nomi,category:catId,xarid_narxi:+xarid,sotish_narxi:+sotish,min_qoldiq:10})}); loadProducts();
  });
  $("#catForm").addEventListener("submit", async e=>{ e.preventDefault(); try{ const f=Object.fromEntries(new FormData(e.target).entries()); await api("/categories/",{method:"POST",body:JSON.stringify(f)}); e.target.reset(); loadCats(); }catch(_){} });
  $("#movSearch").addEventListener("click", loadMovs);
  $("#movForm").addEventListener("submit", async e=>{ e.preventDefault(); try{ const f=Object.fromEntries(new FormData(e.target).entries()); f.product=+f.product; f.nechta=+f.nechta; await api("/movements/",{method:"POST",body:JSON.stringify(f)}); loadMovs(); }catch(_){} });
  $("#ordSearch").addEventListener("click", ()=>loadOrders((window._orderBase||"").includes("manager")));
  $("#ordNew").addEventListener("click", async ()=>{ try{ const items=prompt("buyurtma: product_id:soni,product_id:soni (masalan 1:2,3:1)"); if(!items) return; const arr=items.split(",").map(s=>{const p=s.split(":");return{product:+p[0],soni:+p[1]}}); await api("/orders/",{method:"POST",body:JSON.stringify({items:arr})}); loadOrders(false); }catch(_){} });
  $("#userForm").addEventListener("submit", async e=>{ e.preventDefault(); try{ const f=Object.fromEntries(new FormData(e.target).entries()); await api("/users/",{method:"POST",body:JSON.stringify(f)}); e.target.reset(); loadUsers(); }catch(_){} });
  $("#profileForm").addEventListener("submit", async e=>{ e.preventDefault(); try{ const f=Object.fromEntries(new FormData(e.target).entries()); me=await api("/auth/profile/",{method:"PATCH",body:JSON.stringify(f)}); loadProfile(); }catch(_){} });

  const hash = (location.hash||"").replace("#","");
  if (access && hash && hash!=="login") show(hash.toLowerCase());
  await loadMe();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
})();
