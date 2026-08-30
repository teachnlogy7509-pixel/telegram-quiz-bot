<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>RATHOD HUB - NEET Library & Community</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" rel="stylesheet">
<style>
body{background:#0f172a}
.doctor-bg{background:linear-gradient(rgba(15,23,42,.90),rgba(15,23,42,.96)),url('https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=1920&q=80');background-size:cover;background-position:center;background-attachment:fixed}
::-webkit-scrollbar{width:8px}::-webkit-scrollbar-thumb{background:#334155;border-radius:20px}

/* ===== RATHOD HUB responsive app shell ===== */
html{font-size:16px;-webkit-text-size-adjust:100%}
body{overflow-x:hidden}
.rh-main{min-width:0}
.rh-content{box-sizing:border-box}
.rh-sidebar{flex:0 0 250px}
.rh-topbar{position:sticky;top:0;z-index:120}
@media (min-width:1400px){.rh-sidebar{flex-basis:270px}.rh-content{max-width:1320px}.rh-feature-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media (min-width:901px){.rh-mobile-bottom{display:none!important}.rh-sidebar{display:block}.rh-content{padding-left:26px;padding-right:26px}}
@media (max-width:900px){
  .rh-sidebar{width:82px;flex-basis:82px;padding:14px 8px;}
  .rh-side-title,.rh-nav-btn span{display:none}
  .rh-nav-btn{justify-content:center;padding:12px 8px;min-height:44px}
  .rh-nav-btn i{width:auto;font-size:18px}
  .rh-main{min-width:0}
  .rh-content{padding:16px}
  .rh-feature-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .rh-home-hero{padding:22px}
}
@media (max-width:640px){
  body{background:#07090d!important;color:#f8fafc!important}
  .doctor-bg{background:linear-gradient(rgba(0,0,0,.30),rgba(0,0,0,.50)),url('https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=1200&q=80')!important;background-size:cover!important;background-attachment:fixed!important}
  #hub-bg-layer,#hub-bg-overlay{display:block!important}
  .rh-topbar{height:62px;padding:0 12px;position:fixed;top:0;left:0;right:0}
  .rh-brand{min-width:0}
  .rh-brand-mark{width:36px!important;height:36px!important}
  .rh-top-actions{gap:6px!important}
  .rh-top-actions .rh-icon-btn{width:36px!important;height:36px!important}
  .rh-user-name,.rh-user>div:nth-child(2){display:none}
  .rh-sidebar{display:none!important}
  .rh-main{margin-left:0!important;width:100%!important;padding-bottom:88px}
  .rh-content{padding:12px;width:100%;max-width:none}
  .rh-page-head{margin-bottom:14px}
  .rh-page-title{font-size:21px}
  .rh-page-sub{font-size:11px}
  .rh-home-hero{padding:18px;border-radius:16px}
  .rh-hero-title{font-size:22px}
  .rh-feature-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .rh-feature{min-height:104px;padding:12px;border-radius:14px}
  .rh-feature-icon{width:36px;height:36px;margin-bottom:8px}
  .rh-feature b{font-size:12px}.rh-feature p{font-size:10px}
  .rh-stat{padding:12px}.rh-stat-value{font-size:18px}
  .rh-mobile-bottom{display:grid!important;grid-template-columns:repeat(5,1fr);position:fixed;left:0;right:0;bottom:0;height:70px;padding-bottom:env(safe-area-inset-bottom);background:rgba(6,8,12,.98)!important;backdrop-filter:blur(16px);border-top:1px solid rgba(255,255,255,.12);z-index:500;box-shadow:0 -8px 28px rgba(0,0,0,.4)}
  .rh-mobile-bottom button{border:0;background:transparent;color:#94a3b8;font-size:10px;font-weight:700;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}
  .rh-mobile-bottom i{display:block;font-size:17px;margin-bottom:2px}
  .rh-mobile-bottom .rh-active{color:#ef2b2b!important}
  .rh-old-section>div{border-radius:15px}
  #section-focus .grid.lg\:grid-cols-\[1\.2fr_\.8fr\]{grid-template-columns:1fr!important}
  #focus-timer-display{font-size:clamp(42px,14vw,66px)!important}
  .grid.md\:grid-cols-2,.grid.md\:grid-cols-3,.grid.lg\:grid-cols-2{grid-template-columns:1fr!important}
  .overflow-x-auto{-webkit-overflow-scrolling:touch}
  input,select,textarea,button{font-size:15px}
}
@media (max-width:380px){.rh-feature-grid{grid-template-columns:1fr}.rh-mobile-bottom button{font-size:9px}.rh-mobile-bottom i{font-size:15px}}

/* ===== RATHOD HUB / PW-STYLE DESKTOP + MOBILE VISUAL SYSTEM ===== */
:root{--rh-red:#ef2b2b;--rh-red2:#ff3b30;--rh-bg:#07090d;--rh-panel:rgba(10,13,18,.88);--rh-line:rgba(255,255,255,.16);--rh-muted:#aeb4bf;--rh-white:#f8fafc}
html,body{background:#07090d!important;color:var(--rh-white)!important}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}
.doctor-bg{background:linear-gradient(rgba(0,0,0,.30),rgba(0,0,0,.44)),url('https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=1920&q=80')!important;background-size:cover!important;background-position:center!important;background-attachment:fixed!important}
#hub-bg-overlay{background:rgba(0,0,0,.20)!important}
#app{background:transparent!important}
.rh-topbar{position:fixed!important;left:0;right:0;top:0;height:70px!important;background:rgba(5,7,10,.92)!important;border-bottom:1px solid rgba(255,255,255,.12)!important;backdrop-filter:blur(16px);padding:0 20px!important;z-index:500;display:flex;align-items:center;justify-content:space-between}
.rh-brand{display:flex;align-items:center;gap:10px;min-width:215px;font-weight:900;letter-spacing:.01em;color:#fff!important}
.rh-brand-mark{width:38px!important;height:38px!important;border-radius:12px!important;background:rgba(239,43,43,.12)!important;border:1px solid rgba(239,43,43,.55)!important;color:var(--rh-red)!important;display:flex;align-items:center;justify-content:center}
.rh-top-actions{display:flex;align-items:center;gap:10px!important}
.rh-icon-btn{background:rgba(255,255,255,0.06)!important;color:#fff!important;border:1px solid rgba(255,255,255,.14)!important;border-radius:10px;width:38px;height:38px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:.18s}
.rh-icon-btn:hover{color:var(--rh-red)!important;border-color:rgba(239,43,43,.5)!important}
.rh-user{display:flex!important;align-items:center;gap:9px;padding-left:12px;border-left:1px solid rgba(255,255,255,.14)}
.rh-user-name{color:#fff!important;font-weight:800!important}
.rh-user span{color:var(--rh-red)!important}
#app>main{max-width:none!important;width:100%!important;margin:0!important;padding:0!important;display:block!important;padding-top:70px!important}
#app>main>.flex{display:block!important}
.rh-sidebar{position:fixed!important;left:0;top:70px;bottom:0;width:216px!important;flex:none!important;padding:18px 10px!important;background:rgba(5,7,10,.94)!important;border-right:1px solid rgba(255,255,255,.13)!important;overflow-y:auto;z-index:450}
.rh-side-title{color:#777f8d!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:.12em!important;padding:11px 12px 7px!important}
.rh-side-sep{height:1px;background:rgba(255,255,255,.08);margin:9px 10px}
.rh-nav-btn{width:100%!important;background:transparent!important;color:#eef1f5!important;border:1px solid transparent!important;border-radius:10px!important;padding:10px 12px!important;min-height:42px!important;display:flex!important;align-items:center!important;gap:13px!important;text-align:left!important;font-weight:750!important;font-size:14px!important;transition:.18s ease!important}
.rh-nav-btn i{width:20px!important;text-align:center!important;color:#f4f6f8!important;font-size:16px!important}
.rh-nav-btn:hover{background:rgba(239,43,43,.10)!important;color:#fff!important;border-color:rgba(239,43,43,.28)!important}
.rh-nav-btn:hover i{color:var(--rh-red)!important}
.rh-nav-btn.rh-active{background:linear-gradient(90deg,rgba(239,43,43,.22),rgba(239,43,43,.06))!important;border-color:var(--rh-red)!important;box-shadow:inset 3px 0 0 var(--rh-red),0 0 18px rgba(239,43,43,.08)!important;color:#fff!important}
.rh-nav-btn.rh-active i{color:var(--rh-red)!important}
.rh-main{margin-left:216px!important;width:calc(100% - 216px)!important;min-width:0!important}
.rh-content{max-width:none!important;width:100%!important;padding:22px 22px 30px!important}
.rh-page-head{color:#fff!important;border-bottom:1px solid rgba(255,255,255,.10);padding-bottom:14px}
.rh-page-title,.rh-page-title *{color:#fff!important;font-weight:900!important}
.rh-page-sub{color:#aeb4bf!important}
.rh-home-grid{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px;align-items:start}
.rh-home-main{min-width:0;display:flex;flex-direction:column;gap:18px}
.rh-home-rail{display:flex;flex-direction:column;gap:16px;position:sticky;top:90px}
.rh-rail-card{background:rgba(7,10,14,.84);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(0,0,0,.20);backdrop-filter:blur(10px)}
.rh-rail-title{display:flex;align-items:center;justify-content:space-between;font-weight:900;font-size:15px;margin-bottom:12px}
.rh-rail-title a{color:var(--rh-red);font-size:11px;font-weight:800}
.rh-home-hero{background:linear-gradient(110deg,rgba(8,10,14,.72),rgba(8,10,14,.30));border:1px solid rgba(255,255,255,.16)!important;border-radius:18px!important;box-shadow:0 15px 40px rgba(0,0,0,.24);overflow:hidden}
.rh-hero-kicker{color:#ff6a6a!important;letter-spacing:.12em!important}
.rh-hero-title{color:#fff!important;font-weight:900!important}
.rh-home-hero b{color:#fff!important}
.rh-section-title{color:#fff!important;font-weight:900!important;font-size:18px!important}
.rh-feature-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px!important}
.rh-feature{background:rgba(8,11,15,.84)!important;border:1px solid rgba(255,255,255,.18)!important;color:#fff!important;border-radius:14px!important;min-height:115px!important;padding:15px!important;transition:.18s ease;box-shadow:0 8px 24px rgba(0,0,0,.15)}
.rh-feature:hover{transform:translateY(-2px);border-color:rgba(239,43,43,.75)!important;background:rgba(20,10,12,.88)!important}
.rh-feature-icon{color:var(--rh-red)!important;background:rgba(239,43,43,.10)!important;border:1px solid rgba(239,43,43,.24)!important}
.rh-feature b{color:#fff!important}.rh-feature p{color:#aeb4bf!important}
.rh-live,.rh-stat{background:rgba(7,10,14,.86)!important;border:1px solid rgba(255,255,255,.15)!important;color:#fff!important;border-radius:14px!important}
#section-home button{color:#fff}
#section-home .bg-slate-50,#section-home .bg-slate-100{background:rgba(15,18,23,.9)!important;border-color:rgba(255,255,255,.14)!important;color:#fff!important}
#section-home .text-slate-700,#section-home .text-slate-600,#section-home .text-slate-500,#section-home .text-slate-400,#section-home .text-slate-300{color:#d5d9df!important}
#app .text-slate-50,#app .text-slate-100,#app .text-slate-200,#app .text-slate-300,#app .text-slate-400,#app .text-slate-500,#app .text-slate-600,#app .text-slate-700,#app .text-gray-300,#app .text-gray-400,#app .text-gray-500{color:#f1f3f5!important}
#app .text-slate-500,#app .text-slate-400{color:#b7bdc7!important}
#app h1,#app h2,#app h3,#app h4,#app label,#app b,#app strong{color:#fff}
#app input,#app textarea,#app select{background:rgba(3,6,10,.92)!important;color:#fff!important;border-color:rgba(255,255,255,.18)!important}
#app input::placeholder,#app textarea::placeholder{color:#7f8792!important}
#app .bg-slate-800\/95,#app .bg-slate-900\/95,#app .bg-slate-900\/90,#app .bg-slate-900\/80,#app .bg-slate-900\/70{background:rgba(8,11,15,.90)!important;border-color:rgba(255,255,255,.14)!important}
#app .bg-slate-700{background:#1a1e25!important}
#app .border-slate-700,#app .border-slate-200,#app .border-slate-300{border-color:rgba(255,255,255,.16)!important}
#app .text-indigo-500,#app .text-indigo-600,#app .text-indigo-400,#app .text-teal-300,#app .text-teal-400,#app .text-teal-500,#app .text-purple-300,#app .text-violet-300,#app .text-sky-300{color:var(--rh-red)!important}
#app .bg-indigo-600,#app .bg-indigo-500,#app .bg-teal-600,#app .bg-teal-500,#app .bg-purple-600{background:var(--rh-red)!important}
#app .bg-indigo-600:hover,#app .bg-indigo-500:hover,#app .bg-teal-600:hover,#app .bg-teal-500:hover,#app .bg-purple-600:hover{background:#ff4141!important}
#app .rh-page-head button{background:#11151b!important;color:#fff!important;border-color:rgba(255,255,255,.16)!important}
#app .rh-page-head button i{color:var(--rh-red)!important}
.rh-mini-row{display:flex;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.08)}
.rh-mini-row:last-child{border-bottom:0}.rh-mini-avatar{width:34px;height:34px;border-radius:50%;overflow:hidden;background:#252b34;display:flex;align-items:center;justify-content:center;flex:none}.rh-mini-avatar img{width:100%;height:100%;object-fit:cover}.rh-mini-name{flex:1;min-width:0}.rh-mini-name b{display:block;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rh-mini-name span{font-size:9px;color:#9ba3ae!important}.rh-mini-xp{font-size:11px;font-weight:900;color:#fff}.rh-rank{width:23px;color:#ff4a4a;font-weight:900;font-size:11px}
.rh-online-list{display:flex;gap:8px;flex-wrap:wrap}.rh-online-user{width:54px;text-align:center;font-size:9px;color:#cbd0d7!important}.rh-online-avatar{position:relative;width:42px;height:42px;border-radius:50%;margin:auto;background:#252b34;overflow:hidden;border:1px solid rgba(255,255,255,.12)}.rh-online-avatar img{width:100%;height:100%;object-fit:cover}.rh-online-avatar:after{content:"";position:absolute;right:0;bottom:1px;width:9px;height:9px;background:#22c55e;border:2px solid #090b0f;border-radius:50%}
.rh-mobile-bottom{background:rgba(6,8,12,.96)!important;border-top:1px solid rgba(255,255,255,.12)!important}.rh-mobile-bottom button{color:#aeb4bf!important}.rh-mobile-bottom .rh-active{color:var(--rh-red)!important}
@media(max-width:1100px){.rh-home-grid{grid-template-columns:1fr}.rh-home-rail{position:static;display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.rh-feature-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:900px){
 .rh-topbar{height:62px!important;padding:0 12px!important}.rh-brand{min-width:auto}.rh-brand>div:last-child{display:block!important;font-size:12px}.rh-brand>div:last-child>div:last-child{display:none}.rh-brand-mark{width:36px!important;height:36px!important}
 #app>main{padding-top:62px!important}.rh-sidebar{display:none!important}.rh-main{margin-left:0!important;width:100%!important}.rh-content{padding:14px!important}.rh-home-grid{display:block}.rh-home-rail{display:grid;grid-template-columns:1fr 1fr;margin-top:2px}.rh-feature-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.rh-top-actions{gap:3px!important}.rh-user-name{display:none!important}
}
@media(max-width:640px){
 .doctor-bg{background:linear-gradient(rgba(0,0,0,.18),rgba(0,0,0,.30)),url('https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=1200&q=80')!important;background-size:cover!important;background-attachment:fixed!important}
 #hub-bg-layer,#hub-bg-overlay{display:block!important;opacity:1!important}.rh-topbar{height:58px!important}.rh-brand>div:last-child{font-size:11px}.rh-content{padding:10px 10px 88px!important}.rh-page-title{font-size:20px!important}.rh-page-sub{font-size:10px!important}.rh-home-hero{padding:16px!important}.rh-hero-title{font-size:22px!important}.rh-feature-grid{gap:8px!important}.rh-feature{min-height:92px!important;padding:11px!important}.rh-feature-icon{width:34px!important;height:34px!important}.rh-feature b{font-size:12px!important}.rh-feature p{font-size:9px!important}.rh-home-rail{grid-template-columns:1fr!important}.rh-rail-card{padding:13px!important}.rh-top-actions .rh-icon-btn{width:34px!important;height:34px!important}.rh-top-actions .rh-icon-btn:nth-child(1),.rh-top-actions .rh-icon-btn:nth-child(3){display:none!important}
}
</style>
</head>
<body class="doctor-bg min-h-screen font-sans">

<div id="hub-bg-layer" style="position:fixed;inset:0;z-index:-2;background-repeat:no-repeat;"></div>
<div id="hub-bg-overlay" style="position:fixed;inset:0;z-index:-1;background:rgba(0,0,0,.6);"></div>

<div id="toast" class="hidden fixed top-4 right-4 z-[9999] max-w-sm px-4 py-3 rounded-xl shadow-2xl text-sm font-semibold transition-all"></div>

<!-- AUTH -->
<section id="auth-screen" class="min-h-screen flex items-center justify-center p-4">
<div class="bg-slate-800/95 border border-slate-700 p-7 rounded-2xl shadow-2xl w-full max-w-md backdrop-blur-md">
<div class="text-center mb-6">
<div class="inline-block bg-teal-500/20 p-4 rounded-full text-teal-400 mb-3 text-3xl"><i class="fa-solid fa-book-medical"></i></div>
<h1 class="text-2xl font-bold text-teal-400">RATHOD HUB</h1>
<p class="text-xs tracking-wider uppercase text-slate-400 mt-1">NEET Library & Community</p>
</div>

<div class="grid grid-cols-2 bg-slate-900 p-1 rounded-xl mb-5">
<button id="tab-login" onclick="showAuth('login')" class="py-2 rounded-lg bg-teal-600 text-sm font-bold">Login</button>
<button id="tab-signup" onclick="showAuth('signup')" class="py-2 rounded-lg text-sm font-bold text-slate-400">Create Account</button>
</div>

<form id="auth-form" class="space-y-4">
<div id="name-wrap" class="hidden">
<label class="block text-xs uppercase text-slate-400 mb-1">Name</label>
<input id="auth-name" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5" placeholder="Your Name">
</div>
<div>
<label class="block text-xs uppercase text-slate-400 mb-1">Email ID</label>
<input id="auth-email" type="email" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5" placeholder="name@example.com">
</div>
<div>
<label class="block text-xs uppercase text-slate-400 mb-1">Password</label>
<input id="auth-password" type="password" minlength="6" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5" placeholder="Minimum 6 characters">
</div>
<div id="pfp-wrap" class="hidden">
<label class="block text-xs uppercase text-slate-400 mb-1">Profile Picture</label>
<input id="auth-pfp" type="file" accept="image/*" class="w-full text-xs text-slate-400">
</div>
<button id="auth-btn" class="w-full bg-teal-600 hover:bg-teal-500 py-3 rounded-lg font-bold">Login</button>
<p id="auth-note" class="text-xs text-slate-400 text-center"></p>
</form>
<div id="forgot-wrap" class="text-center mt-3">
<button type="button" id="forgot-toggle" onclick="toggleForgotForm()" class="text-xs text-teal-400 hover:text-teal-300 underline">Forgot Password?</button>
</div>
<form id="forgot-form" class="hidden mt-3 space-y-2 bg-slate-900/70 border border-slate-700 rounded-xl p-3">
<label class="block text-xs uppercase text-slate-400 mb-1">Reset Email</label>
<input id="forgot-email" type="email" required placeholder="name@example.com" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm">
<button id="forgot-btn" class="w-full bg-teal-700 hover:bg-teal-600 py-2.5 rounded-lg text-sm font-bold">Send OTP</button>
</form>
<div id="password-reset-modal" class="hidden fixed inset-0 z-[200] bg-black/80 p-4 flex items-center justify-center">
  <div class="w-full max-w-md bg-slate-800 border border-slate-700 rounded-2xl p-5 shadow-2xl">
    <div class="flex items-center justify-between mb-4">
      <div><h3 class="font-bold text-lg text-white">Reset Password</h3><p class="text-xs text-slate-400 mt-1">Email में आया OTP code डालें</p></div>
      <i class="fa-solid fa-shield-halved text-teal-400 text-xl"></i>
    </div>
    <form id="password-reset-form" class="space-y-3">
      <input id="reset-otp" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="8" pattern="[0-9]{6,8}" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white text-center text-xl tracking-[.35em]" placeholder="123456">
      <p id="reset-otp-email" class="text-xs text-slate-400 text-center"></p>
      <button type="button" id="verify-otp-btn" class="w-full bg-teal-600 hover:bg-teal-500 py-3 rounded-lg font-bold text-white">Verify Code</button>
      <div id="new-password-fields" class="hidden space-y-3">
        <input id="new-password" type="password" minlength="6" autocomplete="new-password" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white" placeholder="New password (minimum 6 characters)">
        <input id="confirm-password" type="password" minlength="6" autocomplete="new-password" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white" placeholder="Confirm new password">
        <button id="save-password-btn" type="submit" class="w-full bg-teal-600 hover:bg-teal-500 py-3 rounded-lg font-bold text-white">Update Password</button>
      </div>
      <button type="button" id="resend-reset-btn" class="w-full text-xs text-teal-400 hover:text-teal-300 underline">Resend code</button>
    </form>
  </div>
</div>
</div>
</section>

<!-- APP -->
<div id="app" class="hidden min-h-screen flex flex-col">
<header class="rh-topbar">
 <div class="rh-brand"><div class="rh-brand-mark"><i class="fa-solid fa-graduation-cap"></i></div><div><div>RATHOD HUB</div><div style="font-size:9px;color:#8b93a0;font-weight:600;letter-spacing:.08em">NEET LEARNING PLATFORM</div></div></div>
 <div class="rh-top-actions">
  <button class="rh-icon-btn sm:hidden" onclick="openMobileMenu()" title="All Features"><i class="fa-solid fa-bars"></i></button>
  <button class="rh-icon-btn" onclick="switchTab('focus')" title="Focus Timer"><i class="fa-solid fa-stopwatch"></i></button>
  <button class="rh-icon-btn" onclick="requestFocusNotifications();toast('Notifications permission requested 🔔')" title="Notifications"><i class="fa-regular fa-bell"></i></button>
  <button class="rh-icon-btn" onclick="switchTab('leaderboard')" title="Leaderboard"><i class="fa-solid fa-trophy"></i></button>
  <div class="rh-user"><div id="nav-pfp" class="w-9 h-9 rounded-full overflow-hidden border border-indigo-200 bg-slate-100 flex items-center justify-center shrink-0"></div><div><div id="nav-name" class="rh-user-name">User</div><span id="user-badge" class="text-[9px] uppercase font-bold text-indigo-600">Member</span></div><button onclick="openProfile()" class="rh-icon-btn" title="Profile"><i class="fa-solid fa-chevron-down"></i></button></div>
 </div>
</header>

<main class="flex-1 max-w-4xl w-full mx-auto p-4 md:p-6 space-y-5">
<div class="flex flex-1 min-w-0">
<aside class="rh-sidebar">
 <div class="rh-side-title">Learn Online</div>
 <button onclick="switchTab('home')" id="btn-home" class="rh-nav-btn rh-active"><i class="fa-solid fa-house"></i><span>Home</span></button>
 <button onclick="switchTab('ai')" id="btn-ai" class="rh-nav-btn"><i class="fa-solid fa-circle-question"></i><span>AI Doubt</span></button>
 <button onclick="switchTab('quiz')" id="btn-quiz" class="rh-nav-btn"><i class="fa-solid fa-brain"></i><span>AI Quiz</span></button>
 <div class="rh-side-sep"></div>
 <div class="rh-side-title">Study</div>
 <button onclick="switchTab('materials')" id="btn-materials" class="rh-nav-btn"><i class="fa-solid fa-folder-open"></i><span>Study Material</span></button>
 <button onclick="switchTab('focus')" id="btn-focus" class="rh-nav-btn"><i class="fa-solid fa-stopwatch"></i><span>Focus Timer</span></button>
 <button onclick="switchTab('studyrooms')" id="btn-studyrooms" class="rh-nav-btn"><i class="fa-solid fa-door-open"></i><span>Study Rooms</span></button>
 <button onclick="switchTab('diary')" id="btn-diary" class="rh-nav-btn"><i class="fa-solid fa-calendar-check"></i><span>Study Diary</span></button>
 <button onclick="switchTab('vault')" id="btn-vault" class="rh-nav-btn"><i class="fa-solid fa-lock"></i><span>My Vault</span></button>
 <div class="rh-side-sep"></div>
 <div class="rh-side-title">Community</div>
 <button onclick="switchTab('community')" id="btn-community" class="rh-nav-btn"><i class="fa-solid fa-users"></i><span>Community</span></button>
 <button onclick="switchTab('chatroom')" id="btn-chatroom" class="rh-nav-btn"><i class="fa-solid fa-comments"></i><span>Live Chat</span></button>
 <button onclick="switchTab('stories')" id="btn-stories" class="rh-nav-btn"><i class="fa-solid fa-circle-play"></i><span>Stories</span></button>
 <div class="rh-side-sep"></div>
 <div class="rh-side-title">Practice & Fun</div>
 <button onclick="switchTab('games')" id="btn-games" class="rh-nav-btn"><i class="fa-solid fa-gamepad"></i><span>Games</span></button>
 <button onclick="switchTab('hubevents')" id="btn-hubevents" class="rh-nav-btn"><i class="fa-solid fa-bolt"></i><span>Live Events</span></button>
 <button onclick="switchTab('leaderboard')" id="btn-leaderboard" class="rh-nav-btn"><i class="fa-solid fa-trophy"></i><span>Leaderboard</span></button>
 <div class="rh-side-sep"></div>
 <button onclick="openProfile()" class="rh-nav-btn"><i class="fa-solid fa-user"></i><span>My Profile</span></button>
 <button onclick="logout()" class="rh-nav-btn" style="color:#dc4b4b"><i class="fa-solid fa-right-from-bracket"></i><span>Logout</span></button>
</aside>
<div class="rh-main flex-1 min-w-0">
<main class="rh-content space-y-5">
<div id="admin-panel" class="hidden bg-slate-800/95 border border-red-500/30 rounded-2xl p-5 shadow-xl">
<div class="flex justify-between items-center mb-3">
<h3 class="font-bold text-red-300"><i class="fa-solid fa-shield-halved mr-2"></i>Admin Material Upload</h3>
<span class="text-[10px] bg-red-500/10 text-red-300 px-2 py-1 rounded">ADMIN ONLY</span>
</div>
<form id="material-form" class="space-y-3">
<input id="mat-title" required placeholder="Material title" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<textarea id="mat-desc" placeholder="Short description" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"></textarea>
<div class="grid md:grid-cols-2 gap-3">
<select id="mat-category" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<option>Biology</option><option>Chemistry</option><option>Physics</option><option>PYQ</option><option>Test</option><option>Notes</option><option>Other</option>
</select>
<input id="mat-file" type="file" required accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,image/*" class="text-xs text-slate-400">
</div>
<button id="mat-btn" class="w-full bg-red-600 hover:bg-red-500 py-2.5 rounded-lg text-sm font-bold">Upload Material</button>
</form>
</div>

<div id="admin-bg-panel" class="hidden bg-slate-800/95 border border-red-500/30 rounded-2xl p-5 shadow-xl">
<div class="flex justify-between items-center mb-3">
<h3 class="font-bold text-red-300"><i class="fa-solid fa-image mr-2"></i>Background Settings</h3>
<span class="text-[10px] bg-red-500/10 text-red-300 px-2 py-1 rounded">ADMIN ONLY</span>
</div>
<div class="space-y-3">
<div>
<label class="block text-xs uppercase text-slate-400 mb-1">Upload Image</label>
<input id="bg-upload" type="file" accept="image/*" class="w-full text-xs text-slate-400">
</div>
<div>
<label class="block text-xs uppercase text-slate-400 mb-1">Or Image URL</label>
<input id="bg-url" placeholder="https://..." class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
</div>
<div class="grid grid-cols-2 gap-3">
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Overlay Darkness <span id="bg-overlay-val"></span></label><input id="bg-overlay" type="range" min="0" max="1" step="0.05" class="w-full"></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Blur (px) <span id="bg-blur-val"></span></label><input id="bg-blur" type="range" min="0" max="20" step="1" class="w-full"></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Opacity <span id="bg-opacity-val"></span></label><input id="bg-opacity" type="range" min="0.1" max="1" step="0.05" class="w-full"></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Size</label><select id="bg-size" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-sm"><option value="cover">Cover</option><option value="contain">Contain</option></select></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Position</label><select id="bg-position" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-sm"><option value="center">Center</option><option value="top">Top</option><option value="bottom">Bottom</option></select></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Attachment</label><select id="bg-fixed" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-sm"><option value="true">Fixed</option><option value="false">Scroll</option></select></div>
</div>
<div class="flex gap-2 pt-2">
<button type="button" onclick="previewBackground()" class="flex-1 bg-slate-700 hover:bg-slate-600 py-2.5 rounded-lg text-sm font-bold">Preview</button>
<button type="button" onclick="applyBackgroundSettings()" class="flex-1 bg-red-600 hover:bg-red-500 py-2.5 rounded-lg text-sm font-bold">Apply Background</button>
<button type="button" onclick="resetBackgroundSettings()" class="flex-1 bg-slate-700 hover:bg-slate-600 py-2.5 rounded-lg text-sm font-bold">Reset to Default</button>
</div>
<p class="text-[10px] text-slate-500">Ye background sabhi users ko globally dikhega. Normal users ise change nahi kar sakte.</p>
</div>
</div>

<!-- HOME DASHBOARD -->
<section id="section-home" class="rh-old-section space-y-5">
 <div class="rh-home-grid">
  <div class="rh-home-main">
 <div class="rh-page-head"><div><div class="rh-page-title">Home</div><div class="rh-page-sub">Aapki NEET preparation ka complete dashboard</div></div><button onclick="switchTab('focus')" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-xs font-bold shadow-sm"><i class="fa-solid fa-stopwatch mr-2"></i>Start Studying</button></div>
 <div class="rh-home-hero"><div class="rh-hero-kicker">YOUR STUDY HUB</div><div class="rh-hero-title">Hello, <span id="home-user-name">Student</span> 👋</div><p style="color:#d2d5dc;font-size:12px;margin-top:6px;position:relative;z-index:1">Aaj ka target complete karo aur apna streak maintain rakho.</p><div class="grid grid-cols-2 md:grid-cols-4 gap-2 mt-5 relative z-10"><div style="background:#ffffff12;border:1px solid #ffffff18;border-radius:12px;padding:12px"><div style="font-size:10px;color:#c9ccd4">TODAY</div><b id="home-study-time" style="font-size:18px">0h 0m</b></div><div style="background:#ffffff12;border:1px solid #ffffff18;border-radius:12px;padding:12px"><div style="font-size:10px;color:#c9ccd4">STREAK</div><b id="home-streak" style="font-size:18px">0 🔥</b></div><div style="background:#ffffff12;border:1px solid #ffffff18;border-radius:12px;padding:12px"><div style="font-size:10px;color:#c9ccd4">XP</div><b id="home-xp" style="font-size:18px">0 XP</b></div><div style="background:#ffffff12;border:1px solid #ffffff18;border-radius:12px;padding:12px"><div style="font-size:10px;color:#c9ccd4">LEVEL</div><b id="home-level" style="font-size:18px">Level 1</b></div></div></div>
 <div class="rh-section-title">Batch Offerings</div>
 <div class="rh-feature-grid">
  <div class="rh-feature" onclick="switchTab('materials')"><div class="rh-feature-icon"><i class="fa-solid fa-folder-open"></i></div><b>All Study Material</b><p>Notes • PDFs • PYQs</p></div>
  <div class="rh-feature" onclick="switchTab('quiz')"><div class="rh-feature-icon"><i class="fa-solid fa-file-circle-question"></i></div><b>AI Tests</b><p>Topic-wise practice</p></div>
  <div class="rh-feature" onclick="switchTab('ai')"><div class="rh-feature-icon"><i class="fa-solid fa-circle-question"></i></div><b>My Doubts</b><p>Ask NEET doubts</p></div>
  <div class="rh-feature" onclick="switchTab('community')"><div class="rh-feature-icon"><i class="fa-solid fa-users"></i></div><b>Community</b><p>Connect with students</p></div>
  <div class="rh-feature" onclick="switchTab('studyrooms')"><div class="rh-feature-icon"><i class="fa-solid fa-door-open"></i></div><b>Study Rooms</b><p>Live study + voice</p></div>
  <div class="rh-feature" onclick="switchTab('focus')"><div class="rh-feature-icon"><i class="fa-solid fa-stopwatch"></i></div><b>Focus Timer</b><p>YPT-style live timer</p></div>
  <div class="rh-feature" onclick="switchTab('vault')"><div class="rh-feature-icon"><i class="fa-solid fa-lock"></i></div><b>My Vault</b><p>Private saved files</p></div>
  <div class="rh-feature" onclick="switchTab('diary')"><div class="rh-feature-icon"><i class="fa-solid fa-calendar-check"></i></div><b>Study Diary</b><p>Daily target planner</p></div>
  <div class="rh-feature" onclick="switchTab('stories')"><div class="rh-feature-icon"><i class="fa-solid fa-circle-play"></i></div><b>Stories</b><p>24h photo & updates</p></div>
  <div class="rh-feature" onclick="switchTab('games')"><div class="rh-feature-icon"><i class="fa-solid fa-gamepad"></i></div><b>1v1 Games</b><p>Chess & Tic Tac Toe</p></div>
  <div class="rh-feature" onclick="switchTab('hubevents')"><div class="rh-feature-icon"><i class="fa-solid fa-bolt"></i></div><b>Live Events</b><p>Daily challenge & Quiz</p></div>
  <div class="rh-feature" onclick="switchTab('leaderboard')"><div class="rh-feature-icon"><i class="fa-solid fa-ranking-star"></i></div><b>Leaderboard</b><p>XP • Level • Rank</p></div>
 </div>
 <div class="grid lg:grid-cols-2 gap-4">
  <div class="rh-live"><div class="flex justify-between items-center"><div><b style="font-size:14px">Live Students</b><p style="font-size:10px;color:#8b93a0;margin-top:3px">Abhi kaun padh raha hai?</p></div><button onclick="switchTab('focus')" style="font-size:10px;color:#635bff;font-weight:800">View all →</button></div><div class="mt-3 flex items-center"><span class="rh-live-dot"></span><b id="home-live-count" style="font-size:13px">0 students studying</b></div></div>
  <div class="rh-live"><div class="flex justify-between items-center"><div><b style="font-size:14px">Quick Access</b><p style="font-size:10px;color:#8b93a0;margin-top:3px">Jahan se last time छोड़ा tha</p></div></div><div class="grid grid-cols-2 gap-2 mt-3"><button onclick="switchTab('materials')" class="bg-slate-50 border border-slate-200 rounded-lg p-2 text-left text-xs font-bold text-slate-700"><i class="fa-solid fa-book mr-2 text-indigo-500"></i>Materials</button><button onclick="switchTab('chatroom')" class="bg-slate-50 border border-slate-200 rounded-lg p-2 text-left text-xs font-bold text-slate-700"><i class="fa-solid fa-comments mr-2 text-indigo-500"></i>Live Chat</button></div></div>
 </div>

  </div>
 <aside class="rh-home-rail">
  <div class="rh-rail-card">
   <div class="rh-rail-title"><span>Leaderboard (Top 5)</span><a href="#" onclick="switchTab('leaderboard');return false">सभी देखें →</a></div>
   <div id="rh-home-leaderboard"></div>
  </div>
  <div class="rh-rail-card">
   <div class="rh-rail-title"><span>Online Students <span style="color:#22c55e">●</span></span><a href="#" onclick="switchTab('focus');return false">सभी देखें →</a></div>
   <div id="rh-home-online" class="rh-online-list"></div>
  </div>
  <div class="rh-rail-card">
   <div class="rh-rail-title"><span>आज का लक्ष्य</span><a href="#" onclick="switchTab('focus');return false">Edit →</a></div>
   <div style="margin-bottom:11px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>पढ़ाई का समय</span><b id="rh-goal-time">0h 0m</b></div><div style="height:7px;background:#252a31;border-radius:20px;margin-top:7px;overflow:hidden"><div id="rh-goal-time-bar" style="height:100%;width:0%;background:#ef2b2b;border-radius:20px"></div></div></div>
   <div><div style="display:flex;justify-content:space-between;font-size:11px"><span>Focus Streak</span><b id="rh-goal-streak">0 🔥</b></div><div style="height:7px;background:#252a31;border-radius:20px;margin-top:7px;overflow:hidden"><div id="rh-goal-streak-bar" style="height:100%;width:0%;background:#ef2b2b;border-radius:20px"></div></div></div>
  </div>
 </aside>

 </div>
</section>

<section id="section-focus" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-teal-500/30 rounded-2xl p-5 shadow-xl">
 <div class="flex justify-between items-start gap-3 flex-wrap">
  <div><h3 class="text-teal-300 font-bold text-xl"><i class="fa-solid fa-stopwatch mr-2"></i>RATHOD HUB FOCUS</h3><p class="text-xs text-slate-400 mt-1">YPT-style live study timer — पढ़ाई करो, streak बनाओ और XP कमाओ.</p></div>
  <div class="flex gap-2 flex-wrap"><button id="focus-notify-btn" onclick="requestFocusNotifications()" class="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-lg text-xs font-bold">🔔 Notifications</button><span id="focus-live-badge" class="bg-emerald-500/10 text-emerald-300 px-3 py-2 rounded-lg text-xs font-bold">● 0 STUDYING</span></div>
 </div>
 <div class="mt-5 grid lg:grid-cols-[1.2fr_.8fr] gap-4">
  <div class="bg-slate-950/80 border border-slate-700 rounded-2xl p-5 text-center">
   <div id="focus-mode-label" class="text-xs uppercase tracking-widest text-slate-500">FOCUS SESSION</div>
   <div id="focus-timer-display" class="text-6xl sm:text-7xl font-black tracking-wider text-teal-300 mt-2 tabular-nums">00:30:00</div>
   <div id="focus-session-status" class="text-xs text-slate-400 mt-2">Ready to study</div>
   <div class="mt-5 h-3 bg-slate-800 rounded-full overflow-hidden"><div id="focus-progress" class="h-full bg-teal-500 transition-all" style="width:0%"></div></div>
   <div class="flex justify-center gap-2 flex-wrap mt-5">
    <button onclick="startFocusTimer()" id="focus-start-btn" class="bg-teal-600 hover:bg-teal-500 px-5 py-3 rounded-xl font-bold">▶ Start</button>
    <button onclick="pauseFocusTimer()" id="focus-pause-btn" class="hidden bg-amber-600 hover:bg-amber-500 px-5 py-3 rounded-xl font-bold">⏸ Pause</button>
    <button onclick="stopFocusTimer()" id="focus-stop-btn" class="hidden bg-red-600 hover:bg-red-500 px-5 py-3 rounded-xl font-bold">■ Stop</button>
    <button onclick="resetFocusTimer()" class="bg-slate-700 hover:bg-slate-600 px-5 py-3 rounded-xl font-bold">↻ Reset</button>
   </div>
  </div>
  <div class="bg-slate-900/80 border border-slate-700 rounded-2xl p-5">
   <div class="grid grid-cols-2 gap-2 mb-4">
    <button onclick="setFocusPreset(25)" class="bg-slate-800 hover:bg-slate-700 rounded-lg py-2 text-xs font-bold">25 min</button><button onclick="setFocusPreset(50)" class="bg-slate-800 hover:bg-slate-700 rounded-lg py-2 text-xs font-bold">50 min</button><button onclick="setFocusPreset(60)" class="bg-slate-800 hover:bg-slate-700 rounded-lg py-2 text-xs font-bold">1 hour</button><button onclick="setFocusPreset(120)" class="bg-slate-800 hover:bg-slate-700 rounded-lg py-2 text-xs font-bold">2 hours</button>
   </div>
   <label class="block text-[10px] uppercase text-slate-400 mb-1">Custom session (minutes)</label><input id="focus-duration" type="number" min="1" max="720" value="30" onchange="setCustomFocusDuration()" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm">
   <label class="block text-[10px] uppercase text-slate-400 mt-3 mb-1">Subject</label><select id="focus-subject" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm"><option>Biology</option><option>Chemistry</option><option>Physics</option><option>Other</option></select>
   <button onclick="startPomodoro()" class="w-full mt-3 bg-indigo-600 hover:bg-indigo-500 py-2.5 rounded-lg text-xs font-bold">🍅 Start 50/10 Pomodoro</button>
  </div>
 </div>
</div>

<div class="grid md:grid-cols-3 gap-4">
 <div class="bg-slate-800/95 border border-amber-500/20 rounded-2xl p-4"><div class="text-xs text-slate-500 uppercase">Today</div><div id="focus-today-time" class="text-2xl font-black text-amber-300 mt-1">0h 0m</div><div class="text-[10px] text-slate-500 mt-1">Study time</div></div>
 <div class="bg-slate-800/95 border border-orange-500/20 rounded-2xl p-4"><div class="text-xs text-slate-500 uppercase">Streak</div><div id="focus-streak" class="text-2xl font-black text-orange-300 mt-1">0 🔥</div><div class="text-[10px] text-slate-500 mt-1">Consecutive study days</div></div>
 <div class="bg-slate-800/95 border border-cyan-500/20 rounded-2xl p-4"><div class="text-xs text-slate-500 uppercase">Sessions</div><div id="focus-sessions" class="text-2xl font-black text-cyan-300 mt-1">0</div><div class="text-[10px] text-slate-500 mt-1">Completed sessions</div></div>
</div>

<div class="bg-slate-800/95 border border-violet-500/20 rounded-2xl p-5">
 <div class="flex justify-between items-center gap-3"><div><h3 class="font-bold text-violet-300">🎯 Daily Goal</h3><p class="text-xs text-slate-400 mt-1">Apna daily study target set karo.</p></div><div class="flex gap-2 items-center"><input id="focus-goal-hours" type="number" min="0.25" max="24" step="0.25" value="4" onchange="saveFocusGoal()" class="w-20 bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-center"><span class="text-xs text-slate-400">hours</span></div></div>
 <div class="flex justify-between text-xs text-slate-400 mt-4 mb-1"><span>Today's progress</span><b id="focus-goal-label">0 / 4h</b></div><div class="h-3 bg-slate-900 rounded-full overflow-hidden"><div id="focus-goal-bar" class="h-full bg-violet-500 transition-all" style="width:0%"></div></div>
</div>

<div class="grid lg:grid-cols-2 gap-4">
 <div class="bg-slate-800/95 border border-cyan-500/20 rounded-2xl p-5"><div class="flex justify-between items-center"><div><h3 class="font-bold text-cyan-300">👥 Who's Studying?</h3><p class="text-xs text-slate-400 mt-1">Live focus sessions</p></div><span id="focus-online-count" class="text-xs text-emerald-300">0 online</span></div><div id="focus-live-users" class="mt-4 space-y-2"></div></div>
 <div class="bg-slate-800/95 border border-emerald-500/20 rounded-2xl p-5"><div class="flex justify-between items-center"><div><h3 class="font-bold text-emerald-300">📊 Last 7 Days</h3><p class="text-xs text-slate-400 mt-1">Daily study time</p></div><span id="focus-week-total" class="text-xs text-slate-400">0h</span></div><div id="focus-week-chart" class="mt-4 grid grid-cols-7 gap-2 items-end h-40"></div></div>
</div>

<div class="bg-slate-800/95 border border-fuchsia-500/20 rounded-2xl p-5"><h3 class="font-bold text-fuchsia-300">🏅 Achievements</h3><div id="focus-achievements" class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4"></div></div>

<div class="bg-slate-800/95 border border-sky-500/20 rounded-2xl p-5"><div class="flex justify-between items-center"><div><h3 class="font-bold text-sky-300">🔔 Study Notifications</h3><p class="text-xs text-slate-400 mt-1">Timer complete, break complete और daily goal पर browser notification.</p></div><span id="focus-notify-status" class="text-xs text-slate-500">Permission not requested</span></div><div class="mt-4 flex gap-2 flex-wrap"><button onclick="requestFocusNotifications()" class="bg-sky-600 hover:bg-sky-500 px-4 py-2 rounded-lg text-xs font-bold">Allow Notifications</button><button onclick="testFocusNotification()" class="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-xs font-bold">Test</button></div></div>
</section>

<section id="section-ai" class="space-y-4">
<div class="bg-slate-800/95 border border-purple-500/30 rounded-2xl p-5">
<h3 class="text-purple-300 font-bold">NEET AI Tutor</h3>
<p class="text-xs text-slate-400 mt-1">Ask a NEET/NCERT doubt. The frontend calls your secure Supabase Edge Function.</p>
<textarea id="ai-input" rows="4" class="mt-4 w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm" placeholder="Hindi, English ya Hinglish mein apna doubt likho..."></textarea>
<button onclick="askAI()" class="mt-3 w-full bg-purple-600 hover:bg-purple-500 py-3 rounded-xl text-sm font-bold">Ask AI</button>
<div id="ai-output" class="hidden mt-4 bg-slate-900 p-4 rounded-xl text-sm whitespace-pre-wrap leading-6"></div>
</div>
</section>

<section id="section-quiz" class="hidden">
<div class="bg-slate-800/95 border border-teal-500/30 rounded-2xl p-5">
<div class="flex gap-2 flex-wrap">
<select id="quiz-subject" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<option>Biology</option><option>Chemistry</option><option>Physics</option>
</select>
<input id="quiz-topic" type="text" maxlength="120"
placeholder="Any topic: कोशिका / पादप जगत / Cell Division"
class="flex-1 min-w-[220px] bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<select id="quiz-count" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<option>5</option><option>10</option><option>20</option>
</select>
<button onclick="generateQuiz()" class="bg-teal-600 hover:bg-teal-500 px-4 py-2 rounded-lg text-sm font-bold">Generate Quiz</button>
</div>
<p class="text-[11px] text-slate-500 mt-2">Topic optional hai. Blank chhodoge to selected subject se questions banenge.</p>
<div id="quiz-box" class="mt-4 space-y-4"></div>
</div>
</section>

<section id="section-materials" class="hidden">
<div class="bg-slate-800/95 rounded-2xl p-5">
<div class="flex gap-2 mb-4">
<input id="material-search" oninput="renderMaterials()" placeholder="Search study material..." class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<select id="material-filter" onchange="renderMaterials()" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"><option value="">All</option><option>Biology</option><option>Chemistry</option><option>Physics</option><option>PYQ</option><option>Test</option><option>Notes</option><option>Other</option></select>
</div>
<div id="materials-box" class="space-y-3"></div>
</div>
</section>

<section id="section-community" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-teal-500/30 rounded-2xl p-5">
<h3 class="text-teal-300 font-bold mb-3">Create Community Post</h3>
<form id="post-form" class="space-y-3">
<input id="post-title" required placeholder="Title" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<textarea id="post-desc" required rows="3" placeholder="Write something..." class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"></textarea>
<input id="post-file" type="file" accept="image/*,.pdf,.doc,.docx,.txt" class="text-xs text-slate-400">
<div class="flex gap-2">
<button type="button" id="record-btn" onclick="toggleRecording()" class="bg-purple-600 px-3 py-2 rounded-lg text-xs font-bold">🎙 Record Voice</button>
<span id="rec-status" class="text-xs text-slate-400 self-center"></span>
</div>
<button id="post-btn" class="w-full bg-teal-600 hover:bg-teal-500 py-3 rounded-lg text-sm font-bold">Post</button>
</form>
</div>
<div class="bg-slate-800/95 rounded-2xl p-5">
<div class="flex justify-between items-center mb-3"><h3 class="font-bold text-slate-300">Community Feed</h3><span id="post-count" class="text-xs text-slate-400"></span></div>
<div id="posts-box" class="space-y-4"></div>
</div>
<div class="bg-slate-800/95 border border-indigo-500/30 rounded-2xl p-5">
 <div class="flex justify-between items-center mb-3"><div><h3 class="font-bold text-indigo-300">👥 People</h3><p class="text-xs text-slate-400 mt-1">Members ko follow/unfollow karo.</p></div><span class="text-[10px] text-slate-500">Following <b id="my-following-count">0</b> • Followers <b id="my-followers-count">0</b></span></div>
 <input id="people-search" oninput="renderPeople()" placeholder="Search members..." class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm mb-3"><div id="people-box" class="space-y-2"></div>
</div>
</section>

<section id="section-chatroom" class="hidden">
<div class="bg-slate-800/95 border border-cyan-500/30 rounded-2xl p-5">
<div class="flex justify-between items-center mb-4">
<div><h3 class="text-cyan-300 font-bold"><i class="fa-solid fa-comments mr-2"></i>Live Chatroom</h3><p class="text-xs text-slate-400 mt-1">Logged-in members ke live study messages.</p></div>
<span class="text-[10px] bg-cyan-500/10 text-cyan-300 px-2 py-1 rounded">LIVE</span>
</div>
<div id="chat-messages" class="h-96 overflow-y-auto bg-slate-900/80 border border-slate-700 rounded-xl p-3 space-y-3">
<div class="text-center py-10 text-slate-500">Loading messages...</div>
</div>
<form id="chat-form" class="flex gap-2 mt-3">
<input id="chat-input" maxlength="1000" autocomplete="off" placeholder="Type a message..." class="flex-1 min-w-0 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm">
<button id="chat-send-btn" class="bg-cyan-600 hover:bg-cyan-500 px-5 py-3 rounded-xl text-sm font-bold"><i class="fa-solid fa-paper-plane mr-1"></i>Send</button>
</form>
</div>
</section>

<section id="section-diary" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-emerald-500/30 rounded-2xl p-5">
<h3 class="text-emerald-300 font-bold"><i class="fa-solid fa-calendar-check mr-2"></i>Daily Study Diary</h3>
<p class="text-xs text-slate-400 mt-1 mb-4">Ek date ke targets save karne par wahi entry update hoti hai.</p>
<form id="diary-form" class="space-y-3">
<input id="diary-date" type="date" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm">
<textarea id="diary-targets" required rows="5" maxlength="5000" placeholder="Aaj ke study targets likho..." class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm"></textarea>
<button id="diary-save-btn" class="w-full bg-emerald-600 hover:bg-emerald-500 py-3 rounded-xl text-sm font-bold">Save Target</button>
</form>
</div>
<div class="bg-slate-800/95 rounded-2xl p-5">
<div class="flex justify-between items-center mb-3"><h3 class="font-bold text-slate-300">Saved Entries</h3><span id="diary-count" class="text-xs text-slate-400"></span></div>
<div id="diary-list" class="space-y-3"></div>
</div>
</section>
<section id="section-stories" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-pink-500/30 rounded-2xl p-5">
<div class="flex justify-between items-center mb-4"><div><h3 class="text-pink-300 font-bold"><i class="fa-solid fa-circle-play mr-2"></i>Stories</h3><p class="text-xs text-slate-400 mt-1">Instagram जैसी story — 24 घंटे बाद expire.</p></div><span class="text-[10px] bg-pink-500/10 text-pink-300 px-2 py-1 rounded">24 HOURS</span></div>
<div id="stories-row" class="flex gap-4 overflow-x-auto pb-2"></div>
<form id="story-form" class="mt-4 space-y-3"><input id="story-file" type="file" accept="image/*,video/*" required class="w-full text-xs text-slate-400"><input id="story-text" maxlength="180" placeholder="Caption (optional)" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"><button class="w-full bg-pink-600 hover:bg-pink-500 py-3 rounded-xl text-sm font-bold">Add Story</button></form>
</div></section>

<section id="section-games" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-cyan-500/30 rounded-2xl p-5"><div class="flex justify-between items-center"><div><h3 class="text-cyan-300 font-bold"><i class="fa-solid fa-gamepad mr-2"></i>Online Games</h3><p class="text-xs text-slate-400 mt-1">Online member को invite करके 1-vs-1 खेलो.</p></div><span id="online-count" class="text-[10px] bg-emerald-500/10 text-emerald-300 px-2 py-1 rounded">0 ONLINE</span></div><div id="online-players" class="mt-4 grid sm:grid-cols-2 gap-2"></div><div id="game-invites" class="mt-4 space-y-2"></div></div>
<div id="game-lobby" class="bg-slate-800/95 rounded-2xl p-5"><div class="grid sm:grid-cols-2 gap-3"><button onclick="startLocalGame()" class="bg-indigo-600 hover:bg-indigo-500 p-4 rounded-xl font-bold text-left"><i class="fa-solid fa-chess-knight text-xl"></i><span class="block mt-2">Chess</span><span class="text-xs text-indigo-200 font-normal">Real legal-move chess</span></button><button onclick="startLocalGame()" class="bg-teal-600 hover:bg-teal-500 p-4 rounded-xl font-bold text-left"><i class="fa-solid fa-table-cells text-xl"></i><span class="block mt-2">Tic Tac Toe</span><span class="text-xs text-teal-100 font-normal">Classic 3×3 — 2 player</span></button></div></div>
<div id="game-board-wrap" class="hidden bg-slate-800/95 border border-slate-700 rounded-2xl p-5"><div class="flex justify-between items-center mb-4"><div><h3 id="game-title" class="font-bold text-lg">Game</h3><p id="game-status" class="text-xs text-slate-400 mt-1"></p></div><button onclick="closeGame()" class="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-lg text-xs font-bold">Back</button></div><div id="chess-board" class="hidden mx-auto max-w-[440px] aspect-square grid grid-cols-8 rounded-xl overflow-hidden border border-slate-600 shadow-2xl"></div><div id="ttt-board" class="hidden mx-auto max-w-[360px] aspect-square grid grid-cols-3 gap-2"></div></div>
</section>

<section id="section-vault" class="hidden space-y-5"><div class="bg-slate-800/95 border border-violet-500/30 rounded-2xl p-5"><div class="flex justify-between items-center mb-3"><div><h3 class="text-violet-300 font-bold"><i class="fa-solid fa-vault mr-2"></i>My Vault</h3><p class="text-xs text-slate-400 mt-1">आपकी private files.</p></div><span class="text-[10px] bg-violet-500/10 text-violet-300 px-2 py-1 rounded">PRIVATE</span></div><form id="vault-form" class="space-y-3"><input id="vault-title" maxlength="120" required placeholder="File name / title" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"><input id="vault-file" type="file" required class="w-full text-xs text-slate-400"><button class="w-full bg-violet-600 hover:bg-violet-500 py-3 rounded-xl text-sm font-bold">Save to Vault</button></form></div><div class="bg-slate-800/95 rounded-2xl p-5"><div class="flex justify-between items-center mb-3"><h3 class="font-bold">Saved Files</h3><span id="vault-count" class="text-xs text-slate-400"></span></div><div id="vault-list" class="space-y-2"></div></div></section>

<section id="section-hubevents" class="hidden space-y-5">
<div id="daily-bio-status" class="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl px-4 py-3 text-xs font-semibold"><i class="fa-solid fa-dna mr-2"></i>Daily Biology Challenge: हर दिन नए Hindi Biology questions automatically आएंगे.</div>
<div id="hub-admin-composer" class="hidden bg-slate-800/95 border border-red-500/30 rounded-2xl p-5 shadow-xl">
<div class="flex justify-between items-center mb-3">
<h3 class="font-bold text-red-300"><i class="fa-solid fa-calendar-plus mr-2"></i>Create HUB Event</h3>
<span class="text-[10px] bg-red-500/10 text-red-300 px-2 py-1 rounded">ADMIN ONLY</span>
</div>
<form id="hub-event-form" class="space-y-3">
<input id="event-title" required placeholder="Event title" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
<textarea id="event-desc" placeholder="Description" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"></textarea>
<div class="grid md:grid-cols-2 gap-3">
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">Start</label><input id="event-start" type="datetime-local" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"></div>
<div><label class="block text-[10px] uppercase text-slate-400 mb-1">End</label><input id="event-end" type="datetime-local" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"></div>
</div>
<label class="flex items-center gap-2 text-xs text-slate-300"><input id="event-active" type="checkbox" checked>Active</label>
<div class="flex justify-between items-center gap-2"><span class="text-xs text-slate-400">Questions manually add karo — 5 ka fixed limit nahi hai.</span><span id="event-question-count" class="text-[10px] text-amber-300">0 questions</span></div><div id="event-questions" class="space-y-3"></div><button type="button" onclick="addEventQuestion()" class="w-full bg-slate-700 hover:bg-slate-600 py-2.5 rounded-lg text-sm font-bold">＋ Add Question</button>
<button id="event-btn" class="w-full bg-red-600 hover:bg-red-500 py-2.5 rounded-lg text-sm font-bold">Create Event</button>
</form>
<div id="hub-events-list" class="mt-4 space-y-2"></div>
</div>

<div id="hub-no-event" class="bg-slate-800/95 rounded-2xl p-8 text-center text-slate-400">Abhi koi active HUB Event nahi hai.</div>

<div id="hub-active-event" class="hidden space-y-5">
<div class="bg-slate-800/95 border border-amber-500/30 rounded-2xl p-5">
<div class="flex justify-between items-start gap-3 flex-wrap">
<div><h3 id="hub-event-title" class="text-amber-300 font-bold text-lg"></h3><p id="hub-event-desc" class="text-xs text-slate-400 mt-1"></p></div>
<div class="bg-slate-900 border border-amber-500/30 rounded-xl px-4 py-2 text-center"><span class="block text-[10px] uppercase text-slate-500">Ends in</span><b id="hub-countdown" class="text-amber-300 text-lg">--:--:--</b></div>
</div>
<div class="mt-4"><div class="flex justify-between text-xs text-slate-400 mb-1"><span>Daily Progress</span><b id="hub-progress-label">0/5</b></div><div class="h-2 bg-slate-700 rounded-full overflow-hidden"><div id="hub-progress-bar" class="h-full bg-amber-500" style="width:0%"></div></div></div>
</div>
<div id="hub-questions-box" class="space-y-4"></div>
</div>

<div class="bg-slate-800/95 border border-fuchsia-500/30 rounded-2xl p-5 text-center">
<h3 class="text-fuchsia-300 font-bold text-lg mb-1">🎡 Spin & Win</h3>
<p class="text-xs text-slate-400 mb-4">Roz ek spin — XP aur rewards jeeto.</p>
<div class="relative w-56 h-56 mx-auto">
<div id="spin-wheel" class="w-full h-full rounded-full border-4 border-fuchsia-400 shadow-2xl" style="background:conic-gradient(#f59e0b 0 60deg,#ec4899 60deg 120deg,#8b5cf6 120deg 180deg,#06b6d4 180deg 240deg,#10b981 240deg 300deg,#f43f5e 300deg 360deg);transition:transform 3s cubic-bezier(.17,.67,.12,1);">
</div>
<div class="absolute -top-2 left-1/2 -translate-x-1/2 text-2xl">▼</div>
</div>
<button id="spin-btn" onclick="spinWheel()" class="mt-5 bg-fuchsia-600 hover:bg-fuchsia-500 px-6 py-3 rounded-xl font-bold text-sm">Spin Now</button>
<p id="spin-result" class="mt-3 text-sm text-slate-300"></p>
</div>
</section>

<section id="section-studyrooms" class="hidden space-y-5">
<div class="bg-slate-800/95 rounded-2xl p-5">
<h3 class="font-bold text-slate-200"><i class="fa-solid fa-door-open mr-2 text-teal-400"></i>Study Rooms</h3>
<p class="text-xs text-slate-400 mt-1">Room join karo, phir Live Voice दबाकर साथ पढ़ो. Microphone permission allow karna hoga.</p>
</div>
<div id="study-rooms-box" class="grid md:grid-cols-3 gap-4"></div>
</section>

<section id="section-leaderboard" class="hidden"><div class="bg-slate-800/95 rounded-2xl overflow-hidden border border-amber-500/20"><div class="p-5 border-b border-slate-700 flex justify-between items-center"><div><h3 class="text-amber-300 font-bold text-xl"><i class="fa-solid fa-trophy mr-2"></i>Leaderboard</h3><p class="text-xs text-slate-400 mt-1">Rank • Name • XP • Level — सभी members</p></div><div class="text-2xl">🏆</div></div><div class="p-4"><div class="bg-slate-900 rounded-xl p-4 mb-4"><div class="flex justify-between text-sm"><span>My XP</span><b id="my-xp">0 XP</b></div><div class="flex justify-between text-sm mt-2"><span>My Level</span><b id="my-level">Level 1</b></div><div class="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden"><div id="my-xp-bar" class="h-full bg-amber-500" style="width:0%"></div></div></div><div id="leaderboard-list" class="space-y-2"></div></div></div></section>

<div class="mt-8 bg-slate-900/95 border border-slate-700 rounded-2xl p-5 text-center"><div class="text-xs uppercase tracking-wider text-slate-500 mb-3">Join Us / Contact Us</div><div class="flex justify-center gap-3 flex-wrap"><a href="https://t.me/YPTSTUDY1" target="_blank" rel="noopener" class="bg-sky-600 hover:bg-sky-500 px-4 py-2.5 rounded-xl text-sm font-bold"><i class="fa-brands fa-telegram mr-2"></i>Join Group</a><a href="https://t.me/Ashish_Thakur1" target="_blank" rel="noopener" title="Contact Us" aria-label="Contact Us" class="bg-sky-600 hover:bg-sky-500 w-11 h-11 rounded-full text-lg font-bold flex items-center justify-center"><i class="fa-brands fa-telegram"></i></a></div></div>
</main></div></div></div>

<nav class="rh-mobile-bottom">
  <button onclick="switchTab('home')" id="mob-home" class="rh-active"><i class="fa-solid fa-house"></i>Home</button>
  <button onclick="switchTab('materials')" id="mob-materials"><i class="fa-solid fa-book"></i>Study</button>
  <button onclick="switchTab('focus')" id="mob-focus"><i class="fa-solid fa-stopwatch"></i>Focus</button>
  <button onclick="switchTab('chatroom')" id="mob-chat"><i class="fa-solid fa-comments"></i>Chat</button>
  <button onclick="openMobileMenu()" id="mob-more"><i class="fa-solid fa-bars"></i>More</button>
</nav>

<!-- MOBILE ALL FEATURES DRAWER -->
<div id="mobile-menu-drawer" class="hidden fixed inset-0 z-[600] bg-black/80 p-4 flex flex-col justify-end backdrop-blur-sm sm:hidden">
  <div class="bg-slate-900 border border-slate-700 rounded-3xl p-5 space-y-4 max-h-[85vh] overflow-y-auto">
    <div class="flex justify-between items-center border-b border-slate-800 pb-3">
      <b class="text-white text-base">All Features & Modules</b>
      <button onclick="closeMobileMenu()" class="text-slate-400 hover:text-white text-lg">✕</button>
    </div>
    <div class="grid grid-cols-3 gap-2 text-center text-xs">
      <button onclick="switchTab('ai');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-circle-question text-red-400 text-lg"></i><span>AI Doubt</span></button>
      <button onclick="switchTab('quiz');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-brain text-teal-400 text-lg"></i><span>AI Quiz</span></button>
      <button onclick="switchTab('materials');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-folder-open text-amber-400 text-lg"></i><span>Materials</span></button>
      <button onclick="switchTab('focus');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-stopwatch text-red-500 text-lg"></i><span>Focus</span></button>
      <button onclick="switchTab('studyrooms');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-door-open text-cyan-400 text-lg"></i><span>Study Rooms</span></button>
      <button onclick="switchTab('diary');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-calendar-check text-emerald-400 text-lg"></i><span>Study Diary</span></button>
      <button onclick="switchTab('vault');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-lock text-purple-400 text-lg"></i><span>My Vault</span></button>
      <button onclick="switchTab('community');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-users text-indigo-400 text-lg"></i><span>Community</span></button>
      <button onclick="switchTab('chatroom');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-comments text-sky-400 text-lg"></i><span>Live Chat</span></button>
      <button onclick="switchTab('stories');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-circle-play text-pink-400 text-lg"></i><span>Stories</span></button>
      <button onclick="switchTab('games');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-gamepad text-fuchsia-400 text-lg"></i><span>1v1 Games</span></button>
      <button onclick="switchTab('hubevents');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-bolt text-amber-300 text-lg"></i><span>Live Events</span></button>
      <button onclick="switchTab('leaderboard');closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-trophy text-yellow-400 text-lg"></i><span>Leaderboard</span></button>
      <button onclick="openProfile();closeMobileMenu()" class="bg-slate-800 p-3 rounded-xl flex flex-col items-center gap-2"><i class="fa-solid fa-user-pen text-slate-300 text-lg"></i><span>Profile</span></button>
      <button onclick="logout()" class="bg-red-950/60 border border-red-500/30 p-3 rounded-xl flex flex-col items-center gap-2 text-red-400"><i class="fa-solid fa-right-from-bracket text-lg"></i><span>Logout</span></button>
    </div>
  </div>
</div>

<div id="story-viewer" class="hidden fixed inset-0 z-[110] bg-black/95 p-4 flex items-center justify-center"><button onclick="closeStoryViewer()" class="absolute top-5 right-5 text-2xl">✕</button><div id="story-viewer-content" class="max-w-lg w-full max-h-[90vh] text-center"></div></div>

<!-- PROFILE MODAL -->
<div id="profile-modal" class="hidden fixed inset-0 z-[90] bg-black/80 p-4 flex items-center justify-center">
<div class="bg-slate-800 rounded-2xl p-6 w-full max-w-md">
<div class="flex justify-between"><h3 class="font-bold">My Profile</h3><button onclick="closeProfile()">✕</button></div>
<form id="profile-form" class="space-y-3 mt-4">
<input id="profile-name" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2">
<input id="profile-pfp" type="file" accept="image/*" class="w-full text-xs text-slate-400">
<button class="w-full bg-teal-600 py-2.5 rounded-lg font-bold">Save Profile</button>
</form>
</div>
</div>

<script>
const SUPABASE_URL='https://fezyljxjbgefaqroxorl.supabase.co';
const SUPABASE_KEY='sb_publishable_UQ0y1axzT6jsesDmz1JHPA_j2budIh3';
const {createClient}=supabase;
const db=createClient(SUPABASE_URL,SUPABASE_KEY);

let session=null,user=null,profile=null,materials=[],posts=[],chatMessages=[],diaryEntries=[];
let mediaRecorder=null,audioChunks=[],recordedAudioBlob=null,isRecording=false;
let authMode='login';
let chatChannel=null;

function toast(msg,ok=true){const t=document.getElementById('toast');t.textContent=msg;t.className=`fixed top-4 right-4 z-[9999] max-w-sm px-4 py-3 rounded-xl shadow-2xl text-sm font-semibold transition-all ${ok?'bg-emerald-600 text-white':'bg-red-600 text-white'}`;t.classList.remove('hidden');setTimeout(()=>t.classList.add('hidden'),3500)}
function esc(v=''){return String(v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
function safeUrl(u){try{const x=new URL(u);return ['https:','http:'].includes(x.protocol)?x.href:'#'}catch{return '#'}}

function openMobileMenu(){document.getElementById('mobile-menu-drawer')?.classList.remove('hidden')}
function closeMobileMenu(){document.getElementById('mobile-menu-drawer')?.classList.add('hidden')}

function showAuth(mode){
 authMode=mode;
 document.getElementById('name-wrap').classList.toggle('hidden',mode==='login');
 document.getElementById('pfp-wrap').classList.toggle('hidden',mode==='login');
 document.getElementById('auth-name').required=mode==='signup';
 document.getElementById('tab-login').className=mode==='login'?'py-2 rounded-lg bg-teal-600 text-sm font-bold':'py-2 rounded-lg text-sm font-bold text-slate-400';
 document.getElementById('tab-signup').className=mode==='signup'?'py-2 rounded-lg bg-teal-600 text-sm font-bold':'py-2 rounded-lg text-sm font-bold text-slate-400';
 document.getElementById('auth-btn').textContent=mode==='login'?'Login':'Create Account';
 document.getElementById('auth-note').textContent=mode==='login'?'Use your registered email and password.':'A confirmation email may be required by your Supabase settings.';
}
document.getElementById('auth-form').addEventListener('submit',async e=>{
 e.preventDefault();const email=document.getElementById('auth-email').value.trim().toLowerCase(),password=document.getElementById('auth-password').value;
 const btn=document.getElementById('auth-btn');btn.disabled=true;btn.textContent='Please wait...';
 try{
  if(authMode==='signup'){
   const name=document.getElementById('auth-name').value.trim(),pfp=document.getElementById('auth-pfp').files[0];
   const {data,error}=await db.auth.signUp({email,password,options:{data:{name}}});if(error)throw error;
   if(data.user && pfp) await uploadProfilePic(data.user.id,pfp);
   toast('Account created. Check email if confirmation is enabled.');
   showAuth('login');
  }else{
   const {error}=await db.auth.signInWithPassword({email,password});if(error)throw error;
   await boot();
  }
 }catch(err){toast(err.message||'Authentication failed',false)}finally{btn.disabled=false;btn.textContent=authMode==='login'?'Login':'Create Account'}
});

async function uploadProfilePic(uid,file){
 const ext=(file.name.split('.').pop()||'jpg').replace(/[^a-z0-9]/gi,'');const path=`profiles/${uid}.${ext}`;
 const {error}=await db.storage.from('materials').upload(path,file,{upsert:true,contentType:file.type});if(error)throw error;
 const {data}=db.storage.from('materials').getPublicUrl(path);await db.from('profiles').update({pfp_url:data.publicUrl}).eq('id',uid);return data.publicUrl;
}
async function boot(){
 const r=await db.auth.getSession();session=r.data.session;if(!session)return;
 user=session.user;
 const {data,error}=await db.from('profiles').select('*').eq('id',user.id).maybeSingle();
 if(error) {toast('Profile setup failed. Run the SQL setup file first.',false);return}
 profile=data||{id:user.id,name:user.email,role:'member',xp:0,level:1};
 document.getElementById('auth-screen').classList.add('hidden');document.getElementById('app').classList.remove('hidden');
 document.getElementById('nav-name').textContent=profile.name||user.email;
 document.getElementById('user-badge').textContent=profile.role==='admin'?'ADMIN':'MEMBER';
 if(profile.pfp_url)document.getElementById('nav-pfp').innerHTML=`<img src="${safeUrl(profile.pfp_url)}" class="w-full h-full object-cover">`;
 document.getElementById('admin-panel').classList.toggle('hidden',profile.role!=='admin');
 document.getElementById('admin-bg-panel').classList.toggle('hidden',profile.role!=='admin');
 document.getElementById('hub-admin-composer').classList.toggle('hidden',profile.role!=='admin');
 setDefaultDiaryDate(); await Promise.all([loadMaterials(),loadPosts(),loadPeople(),loadChatMessages(),loadDiary(),loadStories(),loadVault(),loadLeaderboard(),loadHubEvents(),loadSpinStatus()]); await initGamePresence(); subscribeToChat(); renderStudyRooms();
 if(profile.role==='admin')populateBackgroundForm();
 initFocusSystem(); applyRHSectionHeaders(); renderHomeDashboard(); switchTab('home');
}
db.auth.onAuthStateChange((event,s)=>{if(event==='SIGNED_OUT')cleanupChatSubscription();if(s&&!session)setTimeout(boot,0)});
async function cleanupFocusSystem(){if(focusInterval)clearInterval(focusInterval);focusInterval=null;if(focusHeartbeat)clearInterval(focusHeartbeat);focusHeartbeat=null;if(focusChannel){try{await db.removeChannel(focusChannel)}catch(e){}focusChannel=null}focusReady=false}
async function logout(){await cleanupChatSubscription();await cleanupGamePresence();await cleanupFocusSystem();stopAllVoiceAndRooms();await db.auth.signOut();location.reload()}

function switchTab(tab){
  ['home','ai','quiz','materials','community','chatroom','diary','stories','games','vault','hubevents','studyrooms','leaderboard','focus'].forEach(x=>{
    const sec=document.getElementById('section-'+x); if(sec)sec.classList.add('hidden');
    const btn=document.getElementById('btn-'+x); if(btn)btn.classList.remove('rh-active');
  });
  const target=document.getElementById('section-'+tab); if(target)target.classList.remove('hidden');
  const active=document.getElementById('btn-'+tab); if(active)active.classList.add('rh-active');
  ['mob-home','mob-materials','mob-focus','mob-chat','mob-more'].forEach(id=>{const b=document.getElementById(id);if(b)b.classList.remove('rh-active')});
  const mobMap={home:'mob-home',materials:'mob-materials',focus:'mob-focus',chatroom:'mob-chat'};if(mobMap[tab])document.getElementById(mobMap[tab])?.classList.add('rh-active');
  if(tab==='home')renderHomeDashboard();
  if(tab==='focus')renderFocusDashboard();
  if(tab==='chatroom')scrollChatToBottom();
  if(tab==='stories')loadStories();
  if(tab==='games')renderOnlinePlayers();
  if(tab==='vault')loadVault();
  if(tab==='leaderboard')loadLeaderboard();
  if(tab==='hubevents')loadHubEvents();
  if(tab==='studyrooms')renderStudyRooms();
  if(tab==='community')loadPeople();
}
const RH_SECTION_META={
 ai:['AI Doubt','Ask and solve your NEET doubts','fa-circle-question','indigo'],
 quiz:['AI Quiz','Practice topic-wise questions','fa-brain','teal'],
 materials:['Study Material','All notes, PDFs, PYQs and study files','fa-folder-open','amber'],
 community:['Community','Posts, students and discussions','fa-users','violet'],
 chatroom:['Live Chat','Live student discussion and doubts','fa-comments','sky'],
 diary:['Study Diary','Track your daily preparation','fa-calendar-check','emerald'],
 stories:['Stories','See what the community is sharing','fa-circle-play','pink'],
 games:['Games','Play Chess and Tic Tac Toe with students','fa-gamepad','fuchsia'],
 vault:['My Vault','Your private saved files','fa-lock','violet'],
 hubevents:['Live Events','Upcoming tests, challenges and events','fa-bolt','amber'],
 studyrooms:['Study Rooms','Join a room and study together','fa-door-open','teal'],
 leaderboard:['Leaderboard','XP, level and rank','fa-trophy','amber'],
 focus:['Focus Timer','YPT-style live study timer and statistics','fa-stopwatch','indigo']
};
function applyRHSectionHeaders(){
 Object.entries(RH_SECTION_META).forEach(([key,m])=>{const sec=document.getElementById('section-'+key);if(!sec||sec.querySelector('.rh-inner-head'))return;const h=document.createElement('div');h.className='rh-page-head rh-inner-head';h.innerHTML=`<div><div class="rh-page-title"><i class="fa-solid ${m[2]} mr-2" style="color:#635bff"></i>${m[0]}</div><div class="rh-page-sub">${m[1]}</div></div><button onclick="switchTab('home')" class="bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 px-3 py-2 rounded-xl text-xs font-bold"><i class="fa-solid fa-house mr-1"></i>Home</button>`;sec.prepend(h);});
}
function renderHomeDashboard(){
  if(!profile)return;
  const n=profile.name||user?.email||'Student';
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
  set('home-user-name',n); set('home-study-time',formatMinutesSimple(getFocusTodayMinutes())); set('home-streak',(getFocusStreak())+' 🔥');
  set('home-xp',((profile.xp||0))+' XP'); set('home-level','Level '+(profile.level||1));
  renderRHHomeRail();
}
function formatMinutesSimple(m){m=Math.max(0,Math.round(Number(m)||0));return Math.floor(m/60)+'h '+(m%60)+'m'}

function getFocusTodayMinutes(){
  const st=readFocusStats();
  const today=localDay();
  const todaySec=(st.sessions||[]).filter(x=>x.date===today).reduce((a,x)=>a+Number(x.seconds||0),0);
  return Math.round(todaySec/60);
}

function getFocusStreak(){
  const st=readFocusStats();
  return focusStreak(st.sessions||[]);
}

async function loadChatMessages(){
 if(!user)return;
 const {data,error}=await db.from('chat_messages').select('id,user_id,name,message,created_at').order('created_at',{ascending:false}).limit(50);
 if(error){console.error(error);document.getElementById('chat-messages').innerHTML='<div class="text-center py-10 text-slate-500">Chatroom table setup required.</div>';return}
 chatMessages=(data||[]).reverse();renderChatMessages();
}
function renderChatMessages(){
 const box=document.getElementById('chat-messages');
 box.innerHTML=chatMessages.length?chatMessages.map(m=>`<div class="${m.user_id===user?.id?'ml-auto bg-cyan-500/10 border-cyan-500/20':'mr-auto bg-slate-800 border-slate-700'} border rounded-xl p-3 max-w-[88%]"><div class="flex justify-between gap-3 items-center mb-1"><b class="text-xs ${m.user_id===user?.id?'text-cyan-300':'text-teal-300'}">${esc(m.name||'Member')}</b><span class="text-[9px] text-slate-500 shrink-0">${esc(new Date(m.created_at).toLocaleString())}</span></div><p class="text-sm text-slate-200 whitespace-pre-wrap break-words">${esc(m.message)}</p></div>`).join(''):'<div class="text-center py-10 text-slate-500">No messages yet. Start the conversation.</div>';
 scrollChatToBottom();
}
function scrollChatToBottom(){const box=document.getElementById('chat-messages');requestAnimationFrame(()=>{box.scrollTop=box.scrollHeight})}
async function subscribeToChat(){
 if(!user)return;
 if(chatChannel){try{await db.removeChannel(chatChannel)}catch(e){}}
 chatChannel=db.channel('public:chat_messages')
  .on('postgres_changes',{event:'INSERT',schema:'public',table:'chat_messages'},payload=>{
    const message=payload.new;if(!message)return;
    const idx=chatMessages.findIndex(m=>m.id===message.id||(m.tempId&&m.tempId===message.id));
    if(idx>=0){ chatMessages[idx]=message; }
    else if(!chatMessages.some(m=>m.id===message.id)){
      chatMessages.push(message);
      if(chatMessages.length>50)chatMessages.shift();
    }
    renderChatMessages();
  })
  .subscribe();
}
async function cleanupChatSubscription(){
 if(!chatChannel)return;
 const channel=chatChannel;chatChannel=null;await db.removeChannel(channel);
}
document.getElementById('chat-form').addEventListener('submit',async e=>{
 e.preventDefault();if(!user||!profile)return toast('Please login to chat.',false);
 const input=document.getElementById('chat-input'),message=input.value.trim();if(!message)return;
 const btn=document.getElementById('chat-send-btn');btn.disabled=true;
 const tempMsg={id:'temp_'+Date.now(),user_id:user.id,name:profile.name||user.email||'Member',message,created_at:new Date().toISOString()};
 chatMessages.push(tempMsg);renderChatMessages();input.value='';
 try{
  const {data,error}=await db.from('chat_messages').insert({user_id:user.id,name:profile.name||user.email||'Member',message}).select().single();
  if(error)throw error;
  if(data){
    const idx=chatMessages.findIndex(m=>m.id===tempMsg.id);
    if(idx>=0)chatMessages[idx]=data;
    renderChatMessages();
  }
 }catch(err){toast(err.message||'Message send failed',false);loadChatMessages()}finally{btn.disabled=false}
});

function localDateValue(date=new Date()){const offset=date.getTimezoneOffset();return new Date(date.getTime()-offset*60000).toISOString().slice(0,10)}
function setDefaultDiaryDate(){if(!document.getElementById('diary-date').value)document.getElementById('diary-date').value=localDateValue()}
async function loadDiary(){
 if(!user)return;
 const {data,error}=await db.from('user_diary').select('id,user_id,date,targets,created_at').eq('user_id',user.id).order('date',{ascending:false});
 if(error){console.error(error);document.getElementById('diary-list').innerHTML='<div class="text-center py-10 text-slate-500">Diary table setup required.</div>';return}
 diaryEntries=data||[];renderDiary();
}
function renderDiary(){
 document.getElementById('diary-count').textContent=`${diaryEntries.length} entries`;
 document.getElementById('diary-list').innerHTML=diaryEntries.length?diaryEntries.map(d=>`<div class="bg-slate-900/80 border border-emerald-500/20 rounded-xl p-4"><div class="flex justify-between gap-3 items-start"><div class="min-w-0"><span class="text-xs font-bold text-emerald-300">${esc(d.date)}</span><p class="text-sm text-slate-300 whitespace-pre-wrap break-words mt-2">${esc(d.targets)}</p></div><div class="flex gap-2 shrink-0"><button onclick="editDiary('${d.id}')" class="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-lg text-xs font-bold">Edit</button><button onclick="deleteDiary('${d.id}')" class="bg-red-600 hover:bg-red-500 px-3 py-2 rounded-lg text-xs font-bold">Delete</button></div></div></div>`).join(''):'<div class="text-center py-10 text-slate-500">No diary entries saved.</div>';
}
document.getElementById('diary-form').addEventListener('submit',async e=>{
 e.preventDefault();if(!user)return toast('Please login to save diary.',false);
 const date=document.getElementById('diary-date').value,targets=document.getElementById('diary-targets').value.trim();if(!date||!targets)return;
 const btn=document.getElementById('diary-save-btn');btn.disabled=true;btn.textContent='Saving...';
 try{
  const {error}=await db.from('user_diary').upsert({user_id:user.id,date,targets},{onConflict:'user_id,date'});if(error)throw error;
  document.getElementById('diary-targets').value='';setDefaultDiaryDate();toast('Diary saved');await loadDiary();
 }catch(err){toast(err.message||'Diary save failed',false)}finally{btn.disabled=false;btn.textContent='Save Target'}
});
function editDiary(id){
 const entry=diaryEntries.find(d=>String(d.id)===String(id));if(!entry)return;
 document.getElementById('diary-date').value=entry.date;document.getElementById('diary-targets').value=entry.targets;document.getElementById('diary-form').scrollIntoView({behavior:'smooth',block:'start'});document.getElementById('diary-targets').focus();
}
async function deleteDiary(id){
 if(!user||!confirm('Delete this diary entry?'))return;
 const {error}=await db.from('user_diary').delete().eq('id',id).eq('user_id',user.id);if(error)toast(error.message,false);else{toast('Diary entry deleted');await loadDiary()}
}

document.getElementById('material-form').addEventListener('submit',async e=>{
 e.preventDefault();if(profile?.role!=='admin')return toast('Admin only',false);
 const file=document.getElementById('mat-file').files[0];if(!file)return;
 const btn=document.getElementById('mat-btn');btn.disabled=true;btn.textContent='Uploading...';
 try{
  const path=`materials/${crypto.randomUUID()}_${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;
  const {error:up}=await db.storage.from('materials').upload(path,file,{contentType:file.type});if(up)throw up;
  const {data:url}=db.storage.from('materials').getPublicUrl(path);
  const {error}=await db.from('posts').insert({author_id:user.id,author:profile.name,title:document.getElementById('mat-title').value.trim(),desc:document.getElementById('mat-desc').value.trim(),file_name:file.name,file_url:url.publicUrl,file_type:file.type,file_size:file.size,category:document.getElementById('mat-category').value,is_material:true});
  if(error)throw error;document.getElementById('material-form').reset();toast('Material uploaded');await loadMaterials();switchTab('materials');
 }catch(err){toast(err.message||'Upload failed',false)}finally{btn.disabled=false;btn.textContent='Upload Material'}
});

async function loadMaterials(){
 const {data,error}=await db.from('posts').select('*').eq('is_material',true).order('created_at',{ascending:false});if(error){console.error(error);return}materials=data||[];renderMaterials();
}
function renderMaterials(){
 const q=document.getElementById('material-search').value.toLowerCase(),cat=document.getElementById('material-filter').value;
 const arr=materials.filter(m=>(!q||`${m.title} ${m.desc} ${m.category}`.toLowerCase().includes(q))&&(!cat||m.category===cat));
 document.getElementById('materials-box').innerHTML=arr.length?arr.map(m=>`<div class="bg-slate-900/80 border border-amber-500/20 p-4 rounded-xl flex justify-between gap-3 items-center"><div class="min-w-0"><span class="text-[10px] bg-amber-500/10 text-amber-300 px-2 py-1 rounded">${esc(m.category||'Study')}</span><h4 class="font-bold text-sm mt-2">${esc(m.title)}</h4><p class="text-xs text-slate-400">${esc(m.desc||'')}</p><p class="text-[10px] text-slate-500 mt-1">${esc(m.file_name||'File')}</p></div><div class="flex gap-2 shrink-0"><a target="_blank" href="${safeUrl(m.file_url)}" class="bg-amber-500 text-slate-950 px-3 py-2 rounded-lg text-xs font-bold">Open</a>${profile?.role==='admin'?`<button onclick="deleteMaterial('${m.id}')" class="bg-red-600 px-3 py-2 rounded-lg text-xs font-bold">Delete</button>`:''}</div></div>`).join(''):'<div class="text-center py-10 text-slate-500">No material found.</div>';
}
async function deleteMaterial(id){if(profile?.role!=='admin')return; if(!confirm('Delete this material?'))return;const {error}=await db.from('posts').delete().eq('id',id);if(error)toast(error.message,false);else{toast('Deleted');await loadMaterials()}}

document.getElementById('post-form').addEventListener('submit',async e=>{
 e.preventDefault();const btn=document.getElementById('post-btn');btn.disabled=true;btn.textContent='Posting...';
 try{
  const file=document.getElementById('post-file').files[0];let url=null,type=null,name=null;
  if(file){const path=`community/${crypto.randomUUID()}_${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;const {error}=await db.storage.from('materials').upload(path,file,{contentType:file.type});if(error)throw error;url=db.storage.from('materials').getPublicUrl(path).data.publicUrl;type=file.type;name=file.name}
  let voiceUrl=null;if(recordedAudioBlob){const path=`community/voice_${crypto.randomUUID()}.webm`;const {error}=await db.storage.from('materials').upload(path,recordedAudioBlob,{contentType:'audio/webm'});if(error)throw error;voiceUrl=db.storage.from('materials').getPublicUrl(path).data.publicUrl}
  const {error}=await db.from('posts').insert({author_id:user.id,author:profile.name,pfp_url:profile.pfp_url,title:document.getElementById('post-title').value.trim(),desc:document.getElementById('post-desc').value.trim(),file_name:name,file_url:url,file_type:type,voice_url:voiceUrl,is_material:false});
  if(error)throw error;document.getElementById('post-form').reset();recordedAudioBlob=null;toast('Post published');await loadPosts();
 }catch(err){toast(err.message||'Post failed',false)}finally{btn.disabled=false;btn.textContent='Post'}
});

let people=[],followingIds=new Set(),followerCount=0;
async function loadPeople(){if(!user)return;const [{data:pd,error:pe},{data:fd,error:fe},{data:rd,error:re}]=await Promise.all([db.from('profiles').select('id,name,pfp_url,role').order('name',{ascending:true}).limit(200),db.from('hub_follows').select('following_id').eq('follower_id',user.id),db.from('hub_follows').select('follower_id').eq('following_id',user.id)]);if(pe||fe||re){console.warn(pe||fe||re);const b=document.getElementById('people-box');if(b)b.innerHTML='<div class="text-xs text-slate-500 p-3">Follow system ready.</div>';return}people=(pd||[]).filter(p=>p.id!==user.id);followingIds=new Set((fd||[]).map(x=>x.following_id));followerCount=(rd||[]).length;updateFollowCounts();renderPeople()}
function updateFollowCounts(){document.getElementById('my-following-count')?.replaceChildren(document.createTextNode(followingIds.size));document.getElementById('my-followers-count')?.replaceChildren(document.createTextNode(followerCount))}
function renderPeople(){const box=document.getElementById('people-box');if(!box)return;const q=(document.getElementById('people-search')?.value||'').toLowerCase().trim();const arr=people.filter(p=>!q||String(p.name||'Member').toLowerCase().includes(q));box.innerHTML=arr.length?arr.map(p=>{const f=followingIds.has(p.id);return `<div class="bg-slate-900/80 border border-slate-700 rounded-xl p-3 flex items-center gap-3"><div class="w-10 h-10 rounded-full overflow-hidden bg-slate-700 flex items-center justify-center">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}" class="w-full h-full object-cover">`:'👤'}</div><div class="min-w-0 flex-1"><b class="block truncate text-sm">${esc(p.name||'Member')}</b><span class="text-[10px] text-slate-500">${p.role==='admin'?'ADMIN':'MEMBER'}</span></div><button onclick="toggleFollow('${p.id}')" class="${f?'bg-slate-700':'bg-indigo-600 hover:bg-indigo-500'} px-3 py-2 rounded-lg text-xs font-bold">${f?'Following':'Follow'}</button></div>`}).join(''):'<div class="text-center py-6 text-slate-500 text-sm">Koi member nahi mila.</div>'}
async function toggleFollow(targetId){if(!user||targetId===user.id)return;const f=followingIds.has(targetId);try{if(f){const {error}=await db.from('hub_follows').delete().eq('follower_id',user.id).eq('following_id',targetId);if(error)throw error;followingIds.delete(targetId);toast('Unfollowed')}else{const {error}=await db.from('hub_follows').insert({follower_id:user.id,following_id:targetId});if(error&&error.code!=='23505')throw error;followingIds.add(targetId);toast('Following ✓')}updateFollowCounts();renderPeople()}catch(e){toast(e.message||'Follow action failed',false)}}

let communityChannel=null;
async function loadPosts(){
  const {data,error}=await db.from('posts').select('*').eq('is_material',false).order('created_at',{ascending:false});
  if(error){console.error(error);return}
  posts=data||[];
  renderPosts();
  if(!communityChannel&&user){
    communityChannel=db.channel('public:posts')
      .on('postgres_changes',{event:'*',schema:'public',table:'posts'},()=>{loadPosts();loadMaterials()})
      .subscribe();
  }
}
function renderPosts(){
 document.getElementById('post-count').textContent=`${posts.length} posts`;
 document.getElementById('posts-box').innerHTML=posts.length?posts.map(p=>{
 const likes=Array.isArray(p.likes)?p.likes:[], comments=Array.isArray(p.comments)?p.comments:[],liked=likes.includes(user.id);
 return `<article class="bg-slate-900/80 border border-slate-700 rounded-2xl p-4 space-y-3">
 <div class="flex justify-between"><div class="flex gap-3 items-center"><div class="w-9 h-9 rounded-full overflow-hidden bg-slate-800">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}" class="w-full h-full object-cover">`:'<div class="h-full flex items-center justify-center">👤</div>'}</div><div><b class="text-sm">${esc(p.author)}</b><div class="text-[10px] text-slate-500">${new Date(p.created_at).toLocaleString()}</div></div></div>${profile.role==='admin'||p.author_id===user.id?`<button onclick="deletePost('${p.id}')" class="text-red-400 text-xs">Delete</button>`:''}</div>
 <h4 class="font-bold text-teal-300">${esc(p.title)}</h4><p class="text-sm text-slate-300 whitespace-pre-wrap">${esc(p.desc)}</p>
 ${p.file_url?(p.file_type?.startsWith('image/')?`<img onclick="window.open('${safeUrl(p.file_url)}','_blank')" src="${safeUrl(p.file_url)}" class="max-h-80 max-w-full rounded-xl cursor-pointer">`:`<a target="_blank" href="${safeUrl(p.file_url)}" class="block bg-slate-800 p-3 rounded-xl text-sm">📎 ${esc(p.file_name||'Attached file')}</a>`):''}
 ${p.voice_url?`<audio controls src="${safeUrl(p.voice_url)}" class="w-full"></audio>`:''}
 <div class="flex justify-between border-t border-slate-800 pt-3"><button onclick="toggleLike('${p.id}')" class="${liked?'text-red-400':''}">♥ ${likes.length}</button><span class="text-xs text-slate-500">${comments.length} comments</span></div>
 <div class="space-y-2">${comments.map(c=>`<div class="bg-slate-800 rounded-lg p-2 text-xs"><b class="text-teal-300">${esc(c.author)}:</b> ${esc(c.text)} ${c.image_url?`<br><img src="${safeUrl(c.image_url)}" class="max-h-32 rounded mt-1">`:''}</div>`).join('')}</div>
 <div class="flex gap-2"><input id="comment-${p.id}" class="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs" placeholder="Write a reply..."><input id="replyfile-${p.id}" type="file" accept="image/*" class="w-24 text-[9px]"><button onclick="addComment('${p.id}')" class="bg-teal-600 px-3 rounded-lg text-xs font-bold">Reply</button></div>
 </article>`}).join(''):'<div class="text-center py-10 text-slate-500">No posts yet.</div>';
}

async function toggleLike(id){
 const p = posts.find(x => String(x.id) === String(id));
 if(!p){ toast('Post not found',false); return; }
 let likes = Array.isArray(p.likes) ? [...p.likes] : [];
 if(likes.includes(user.id)){ likes = likes.filter(x => x !== user.id); }else{ likes.push(user.id); }
 const { error } = await db.from('posts').update({ likes }).eq('id', p.id);
 if(error){ console.error(error); toast(error.message,false); return; }
 await loadPosts();
}

async function addComment(id){
 const input = document.getElementById('comment-'+id);
 const file = document.getElementById('replyfile-'+id).files[0];
 const text = input.value.trim();
 if(!text && !file) return;
 const p = posts.find(x => String(x.id) === String(id));
 if(!p){ toast('Post not found',false); return; }
 let comments = Array.isArray(p.comments) ? [...p.comments] : [];
 let image_url = null;
 try{
  if(file){
   const path = `community/replies/${crypto.randomUUID()}_${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;
   const { error } = await db.storage.from('materials').upload(path,file,{contentType:file.type});
   if(error) throw error;
   image_url = db.storage.from('materials').getPublicUrl(path).data.publicUrl;
  }
  comments.push({ author: profile.name, text, image_url, user_id: user.id, date: new Date().toISOString() });
  const { error } = await db.from('posts').update({ comments }).eq('id', p.id);
  if(error) throw error;
  input.value = '';
  document.getElementById('replyfile-'+id).value = '';
  await loadPosts();
 }catch(err){ console.error(err); toast(err.message,false); }
}

async function deletePost(id){if(!confirm('Delete this post?'))return;const {error}=await db.from('posts').delete().eq('id',id);if(error)toast(error.message,false);else{toast('Deleted');await loadPosts();await loadMaterials()}}

async function toggleRecording(){
 if(!isRecording){try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});mediaRecorder=new MediaRecorder(stream);audioChunks=[];mediaRecorder.ondataavailable=e=>audioChunks.push(e.data);mediaRecorder.onstop=()=>{recordedAudioBlob=new Blob(audioChunks,{type:'audio/webm'});stream.getTracks().forEach(t=>t.stop());document.getElementById('rec-status').textContent='Voice recorded ✓'};mediaRecorder.start();isRecording=true;document.getElementById('record-btn').textContent='🎙 Stop Recording';document.getElementById('rec-status').textContent='Recording...'}catch(e){toast('Microphone permission denied',false)}}else{mediaRecorder.stop();isRecording=false;document.getElementById('record-btn').textContent='🎙 Record Voice'}}

async function awardQuizXP(correct){if(!correct||!user)return;try{const next=Number(profile.xp||0)+10;const level=Math.max(1,Math.floor(next/500)+1);const{error}=await db.from('profiles').update({xp:next,level}).eq('id',user.id);if(error)throw error;profile.xp=next;profile.level=level;toast('+10 XP 🎉');renderHomeDashboard();loadLeaderboard();}catch(e){console.warn('XP update failed',e)}}

/* ==================== RATHOD HUB NEW FEATURES ==================== */
let stories=[],vaultItems=[],leaderboard=[];
const XP_LEVEL_SIZE=500;
function levelFromXp(x){return Math.max(1,Math.floor(Number(x||0)/XP_LEVEL_SIZE)+1)}
function xpPercent(x){return Math.min(100,(Number(x||0)%XP_LEVEL_SIZE)/XP_LEVEL_SIZE*100)}

/* Stories */
async function loadStories(){if(!user)return;const{data,error}=await db.from('stories').select('*').gt('expires_at',new Date().toISOString()).order('created_at',{ascending:false});if(error){document.getElementById('stories-row').innerHTML='<div class="text-xs text-slate-500 p-3">Stories table setup required.</div>';return}stories=data||[];renderStories()}
function renderStories(){const box=document.getElementById('stories-row');box.innerHTML=stories.length?stories.map(s=>`<button onclick="openStory('${s.id}')" class="shrink-0 w-20 text-center"><div class="w-16 h-16 mx-auto rounded-full p-[2px] bg-gradient-to-br from-pink-500 via-purple-500 to-amber-400"><div class="w-full h-full rounded-full overflow-hidden bg-slate-900 border-2 border-slate-900">${s.media_type?.startsWith('video/')?`<video src="${safeUrl(s.media_url)}" class="w-full h-full object-cover"></video>`:`<img src="${safeUrl(s.media_url)}" class="w-full h-full object-cover">`}</div></div><span class="block truncate text-[10px] mt-1">${esc(s.name||'Member')}${s.user_id===user.id?' • You':''}</span></button>`).join(''):'<div class="text-xs text-slate-500 p-3">अभी कोई active story नहीं है.</div>'}
document.getElementById('story-form').addEventListener('submit',async e=>{e.preventDefault();const file=document.getElementById('story-file').files[0];if(!file)return;const b=e.target.querySelector('button');b.disabled=true;b.textContent='Uploading...';try{if(!/^image\/|^video\//.test(file.type))throw new Error('केवल image/video story allowed.');const path=`stories/${user.id}/${crypto.randomUUID()}_${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;const{error:up}=await db.storage.from('materials').upload(path,file,{contentType:file.type});if(up)throw up;const media_url=db.storage.from('materials').getPublicUrl(path).data.publicUrl;const{error}=await db.from('stories').insert({user_id:user.id,name:profile.name||user.email,media_url,media_type:file.type,caption:document.getElementById('story-text').value.trim(),expires_at:new Date(Date.now()+86400000).toISOString()});if(error)throw error;e.target.reset();toast('Story added for 24 hours');loadStories()}catch(err){toast(err.message||'Story failed',false)}finally{b.disabled=false;b.textContent='Add Story'}})
function openStory(id){const s=stories.find(x=>String(x.id)===String(id));if(!s)return;document.getElementById('story-viewer-content').innerHTML=`<div class="text-left mb-2"><b>${esc(s.name||'Member')}</b><div class="text-xs text-slate-400">Expires ${new Date(s.expires_at).toLocaleString()}</div></div>${s.media_type?.startsWith('video/')?`<video controls autoplay class="max-h-[75vh] w-full rounded-2xl bg-black" src="${safeUrl(s.media_url)}"></video>`:`<img class="max-h-[75vh] w-full rounded-2xl object-contain bg-black" src="${safeUrl(s.media_url)}">`}${s.caption?`<p class="mt-3 text-sm">${esc(s.caption)}</p>`:''}`;document.getElementById('story-viewer').classList.remove('hidden')}
function closeStoryViewer(){document.getElementById('story-viewer').classList.add('hidden');document.getElementById('story-viewer-content').innerHTML=''}

/* Presence + game invites */
let gamePresence=null,gameEvents=null,gameRoom=null;
let currentGame={type:null,online:false,roomId:null,role:null,chess:null,ttt:null,selected:null,gameOver:false,connected:false};

async function initGamePresence(){
  if(!user)return;
  if(gamePresence)try{await db.removeChannel(gamePresence)}catch(e){}
  gamePresence=db.channel('rathod-hub-online',{config:{presence:{key:user.id}}})
    .on('presence',{event:'sync'},renderOnlinePlayers)
    .on('presence',{event:'join'},renderOnlinePlayers)
    .on('presence',{event:'leave'},renderOnlinePlayers)
    .subscribe(async status=>{
      if(status==='SUBSCRIBED'){
        await gamePresence.track({
          user_id:user.id,
          name:profile?.name||user.email||'Member',
          pfp_url:profile?.pfp_url||null
        });
        renderOnlinePlayers();
      }
    });

  if(gameEvents)try{await db.removeChannel(gameEvents)}catch(e){}
  gameEvents=db.channel('rathod-hub-game-invites',{config:{broadcast:{self:false}}})
    .on('broadcast',{event:'invite'},x=>receiveInvite(x.payload))
    .on('broadcast',{event:'invite-answer'},x=>receiveInviteAnswer(x.payload))
    .subscribe();
}

async function cleanupGameRoom(){
  if(gameRoom){
    try{await gameRoom.untrack()}catch(e){}
    try{await db.removeChannel(gameRoom)}catch(e){}
    gameRoom=null;
  }
}
async function cleanupGamePresence(){
  await cleanupGameRoom();
  if(gamePresence){try{await gamePresence.untrack()}catch(e){}try{await db.removeChannel(gamePresence)}catch(e){}gamePresence=null}
  if(gameEvents){try{await db.removeChannel(gameEvents)}catch(e){}gameEvents=null}
}

function renderOnlinePlayers(){
  if(!gamePresence||!user)return;
  const state=gamePresence.presenceState(),people=[];
  Object.values(state).flat().forEach(p=>{
    if(p.user_id&&p.user_id!==user.id&&!people.some(x=>x.user_id===p.user_id))people.push(p);
  });
  document.getElementById('online-count').textContent=`${people.length+1} ONLINE`;
  document.getElementById('online-players').innerHTML=people.length?
    people.map(p=>`<div class="bg-slate-900 border border-slate-700 rounded-xl p-3 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 min-w-0">
        <div class="w-9 h-9 rounded-full overflow-hidden bg-slate-700 shrink-0">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}" class="w-full h-full object-cover">`:'👤'}</div>
        <div class="min-w-0"><b class="text-sm truncate block">${esc(p.name||'Member')}</b><span class="text-[10px] text-emerald-400">● Online</span></div>
      </div>
      <div class="flex gap-1">
        <button onclick="invitePlayer('${p.user_id}','${esc(p.name||'Member')}','chess')" class="bg-indigo-600 px-2 py-1.5 rounded-lg text-[10px] font-bold">Chess</button>
        <button onclick="invitePlayer('${p.user_id}','${esc(p.name||'Member')}','tictactoe')" class="bg-teal-600 px-2 py-1.5 rounded-lg text-[10px] font-bold">Tic Tac</button>
      </div>
    </div>`).join(''):
    '<div class="text-xs text-slate-500 sm:col-span-2 p-3">अभी कोई दूसरा member online नहीं है.</div>';
}

async function gameSend(event,payload){
  if(gameEvents)await gameEvents.send({type:'broadcast',event,payload});
}
async function roomSend(event,payload){
  if(gameRoom)await gameRoom.send({type:'broadcast',event,payload});
}

async function invitePlayer(targetId,targetName,type){
  if(!gameEvents)return toast('Online connection तैयार नहीं है.',false);
  if(currentGame.online)return toast('पहले current game खत्म करें.',false);
  const roomId=crypto.randomUUID();
  await gameSend('invite',{
    targetId,fromId:user.id,fromName:profile?.name||user.email||'Member',
    game:type,roomId
  });
  toast(`${targetName} को ${type==='chess'?'Chess':'Tic Tac Toe'} invite भेज दिया.`);
}

function receiveInvite(p){
  if(!p||p.targetId!==user.id)return;
  const box=document.getElementById('game-invites');
  const d=document.createElement('div');
  d.className='bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 flex justify-between items-center gap-2';
  d.innerHTML=`<span class="text-xs"><b>${esc(p.fromName)}</b> ने ${p.game==='chess'?'Chess':'Tic Tac Toe'} invite भेजा.</span><span class="flex gap-1"><button class="bg-emerald-600 px-2 py-1 rounded text-[10px] font-bold">Accept</button><button class="bg-slate-700 px-2 py-1 rounded text-[10px]">Decline</button></span>`;
  d.querySelectorAll('button')[0].onclick=async()=>{
    if(currentGame.online)return toast('आप पहले से game में हैं.',false);
    await gameSend('invite-answer',{targetId:p.fromId,fromId:user.id,accepted:true,game:p.game,roomId:p.roomId});
    await startOnlineGame(p.game,p.roomId,'guest');
    d.remove();
  };
  d.querySelectorAll('button')[1].onclick=()=>d.remove();
  box.prepend(d);
}

function receiveInviteAnswer(p){
  if(!p||p.targetId!==user.id||!p.accepted)return;
  startOnlineGame(p.game,p.roomId,'host');
}

async function startOnlineGame(type,roomId,role){
  if(currentGame.online){
    if(currentGame.roomId===roomId)return;
    return toast('पहले current game खत्म करें.',false);
  }
  await cleanupGameRoom();

  currentGame={
    type,online:true,roomId,role,
    chess:type==='chess'?new Chess():null,
    ttt:type==='tictactoe'?Array(9).fill(''):null,
    selected:null,gameOver:false,connected:false
  };

  document.getElementById('game-lobby').classList.add('hidden');
  document.getElementById('game-board-wrap').classList.remove('hidden');
  renderGame();

  gameRoom=db.channel('rathod-match-'+roomId,{
    config:{broadcast:{self:true},presence:{key:user.id}}
  })
  .on('presence',{event:'sync'},async()=>{
    if(!currentGame.online||currentGame.roomId!==roomId)return;

    const members=Object.values(gameRoom.presenceState()).flat()
      .filter(p=>p&&p.user_id)
      .filter((p,i,a)=>a.findIndex(x=>x.user_id===p.user_id)===i);

    currentGame.connected=members.length>=2;

    if(currentGame.connected){
      document.getElementById('game-status').textContent=
        currentGame.type==='chess'
          ? `${currentGame.role==='host'?'White':'Black'} ready • ${currentGame.chess.turn()==='w'?'White':'Black'} की turn`
          : `${currentGame.role==='host'?'X':'O'} ready • Online match`;

      if(currentGame.role==='host'){
        await roomSend('state',{
          roomId,type,
          fen:type==='chess'?currentGame.chess.fen():null,
          ttt:type==='tictactoe'?currentGame.ttt.slice():null,
          gameOver:currentGame.gameOver
        });
      }
    }else{
      currentGame.connected=false;
      document.getElementById('game-status').textContent='Opponent connect होने का इंतज़ार...';
    }
    renderGame();
  })
  .on('broadcast',{event:'move-request'},x=>receiveMoveRequest(x.payload))
  .on('broadcast',{event:'state'},x=>receiveGameState(x.payload))
  .on('broadcast',{event:'game-end'},x=>receiveGameEnd(x.payload))
  .subscribe(async status=>{
    if(status==='SUBSCRIBED'){
      await gameRoom.track({
        user_id:user.id,role,
        name:profile?.name||user.email||'Member'
      });
      document.getElementById('game-status').textContent='Connecting opponent...';
    }
  });
}
async function receiveMoveRequest(p){
  if(!p||p.roomId!==currentGame.roomId||!currentGame.connected||currentGame.role!=='host'||currentGame.gameOver)return;
  if(p.fromId===user.id)return;

  if(currentGame.type==='tictactoe'){
    const board=currentGame.ttt, count=board.filter(Boolean).length;
    if(count%2!==1||p.mark!=='O'||!Number.isInteger(p.index)||p.index<0||p.index>8||board[p.index])return;

    board[p.index]='O';
    const result=tttResult(board);
    currentGame.gameOver=!!result;

    await roomSend('state',{
      roomId:currentGame.roomId,type:'tictactoe',
      ttt:board.slice(),gameOver:currentGame.gameOver
    });
    renderTtt();

    if(result)await roomSend('game-end',{roomId:currentGame.roomId,message:result});
    return;
  }

  if(currentGame.type==='chess'){
    if(currentGame.chess.turn()!=='b'||!p.from||!p.to)return;
    let legal=null;
    try{legal=currentGame.chess.move({from:p.from,to:p.to,promotion:'q'})}catch(e){legal=null}
    if(!legal)return;

    currentGame.gameOver=currentGame.chess.isGameOver();
    currentGame.selected=null;
    renderChess();

    await roomSend('state',{
      roomId:currentGame.roomId,type:'chess',
      fen:currentGame.chess.fen(),gameOver:currentGame.gameOver
    });

    if(currentGame.gameOver){
      await roomSend('game-end',{roomId:currentGame.roomId,message:chessResult()});
    }
  }
}

function receiveGameState(p){
  if(!p||p.roomId!==currentGame.roomId)return;
  try{
    if(p.type==='tictactoe'){
      currentGame.ttt=Array.isArray(p.ttt)?p.ttt.slice(0,9):currentGame.ttt;
      currentGame.gameOver=!!p.gameOver;
      renderTtt();
    }else if(p.type==='chess'&&p.fen){
      currentGame.chess=new Chess(p.fen);
      currentGame.gameOver=!!p.gameOver;
      currentGame.selected=null;
      renderChess();
    }
  }catch(e){console.warn('Game state sync failed',e)}
}

function receiveGameEnd(p){
  if(p?.roomId!==currentGame.roomId)return;
  currentGame.gameOver=true;
  document.getElementById('game-status').textContent=p.message||'Game over';
}

function startLocalGame(){
  toast('पहले ONLINE user को invite करें.',false);
}

async function closeGame(){
  await cleanupGameRoom();
  document.getElementById('game-board-wrap').classList.add('hidden');
  document.getElementById('game-lobby').classList.remove('hidden');
  currentGame={type:null,online:false,roomId:null,role:null,chess:null,ttt:null,selected:null,gameOver:false,connected:false};
}

function renderGame(){
  document.getElementById('chess-board').classList.toggle('hidden',currentGame.type!=='chess');
  document.getElementById('ttt-board').classList.toggle('hidden',currentGame.type!=='tictactoe');
  document.getElementById('game-title').textContent=currentGame.type==='chess'?'♟ Chess — Online 2 Player':'⭕ Tic Tac Toe — Online 2 Player';
  if(currentGame.type==='chess')renderChess();
  if(currentGame.type==='tictactoe')renderTtt();
}

function tttResult(b){
  const w=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
  const win=w.find(x=>b[x[0]]&&b[x[0]]===b[x[1]]&&b[x[0]]===b[x[2]]);
  if(win)return`Winner: ${b[win[0]]}`;
  return b.every(Boolean)?'Draw!':null;
}

function renderTtt(){
  const b=currentGame.ttt||Array(9).fill('');
  document.getElementById('ttt-board').innerHTML=b.map((v,i)=>
    `<button onclick="tttMove(${i})" ${v||currentGame.gameOver?'disabled':''} class="bg-slate-900 border border-slate-700 hover:bg-slate-700 disabled:opacity-80 rounded-xl text-5xl font-black ${v==='X'?'text-cyan-300':'text-pink-300'}">${v||''}</button>`
  ).join('');

  if(currentGame.gameOver){
    document.getElementById('game-status').textContent=tttResult(b)||'Game over';
    return;
  }
  const count=b.filter(Boolean).length;
  const turn=count%2?'O':'X';
  const mine=currentGame.role==='host'?'X':'O';
  document.getElementById('game-status').textContent=`${turn} की turn • आप: ${mine} • Online match`;
}

async function tttMove(i){
  if(currentGame.type!=='tictactoe'||!currentGame.online||!currentGame.connected||currentGame.gameOver)return;
  const b=currentGame.ttt;
  if(b[i])return;

  const count=b.filter(Boolean).length;
  const turn=count%2?'O':'X';
  const mine=currentGame.role==='host'?'X':'O';

  if(turn!==mine)return toast('Opponent की turn है.',false);

  if(currentGame.role==='host'){
    b[i]='X';
    const result=tttResult(b);
    currentGame.gameOver=!!result;
    await roomSend('state',{
      roomId:currentGame.roomId,type:'tictactoe',
      ttt:b.slice(),gameOver:currentGame.gameOver
    });
    renderTtt();
    if(result)await roomSend('game-end',{roomId:currentGame.roomId,message:result});
  }else{
    await roomSend('move-request',{
      roomId:currentGame.roomId,fromId:user.id,index:i,mark:'O'
    });
  }
}

function renderChess(){
  const board=document.getElementById('chess-board');
  const u={p:'♟',r:'♜',n:'♞',b:'♝',q:'♛',k:'♚',P:'♙',R:'♖',N:'♘',B:'♗',Q:'♕',K:'♔'};
  const arr=currentGame.chess.board(),sel=currentGame.selected;

  board.innerHTML=arr.map((row,r)=>row.map((cell,c)=>{
    const p=cell?u[cell.color==='w'?cell.type.toUpperCase():cell.type]:'';
    const dark=(r+c)%2;
    const sq='abcdefgh'[c]+(8-r);
    const chosen=sel===sq;
    return `<button onclick="chessClick(${r},${c})" ${currentGame.gameOver?'disabled':''} title="${sq}" class="flex items-center justify-center text-[clamp(25px,7vw,50px)] ${dark?'bg-slate-600':'bg-slate-300'} ${cell?.color==='w'?'text-white':'text-slate-950'} ${chosen?'ring-4 ring-yellow-400 ring-inset':''} disabled:opacity-90">${p}</button>`;
  }).join('')).join('');

  const turn=currentGame.chess.turn()==='w'?'White':'Black';
  const mine=currentGame.role==='host'?'White':'Black';
  if(!currentGame.connected){document.getElementById('game-status').textContent='Opponent connect होने का इंतज़ार...';return;}
  document.getElementById('game-status').textContent=currentGame.chess.isGameOver()?
    chessResult():
    `${turn} to move • आप: ${mine} • Online match${currentGame.chess.in_check()?' • CHECK':''}`;
}

function chessResult(){
  if(currentGame.chess.isCheckmate())
    return`Checkmate — ${currentGame.chess.turn()==='w'?'Black':'White'} wins!`;
  if(currentGame.chess.isDraw())return'Draw!';
  return'Game over';
}

async function chessClick(r,c){
  if(!currentGame.online||currentGame.type!=='chess'||!currentGame.connected||currentGame.gameOver)return;

  const sq='abcdefgh'[c]+(8-r);
  const piece=currentGame.chess.get(sq);
  const mine=currentGame.role==='host'?'w':'b';

  if(currentGame.chess.turn()!==mine)
    return toast('Opponent की turn है.',false);

  if(!currentGame.selected){
    if(piece&&piece.color===mine){
      currentGame.selected=sq;
      renderChess();
    }
    return;
  }

  const from=currentGame.selected;

  if(from===sq){
    currentGame.selected=null;
    renderChess();
    return;
  }

  try{
    const test=new Chess(currentGame.chess.fen());
    const legal=test.move({from,to:sq,promotion:'q'});

    if(!legal){
      if(piece&&piece.color===mine){
        currentGame.selected=sq;
        renderChess();
      }else{
        currentGame.selected=null;
        renderChess();
      }
      return;
    }

    currentGame.selected=null;

    if(currentGame.role==='host'){
      currentGame.chess.move({from,to:sq,promotion:'q'});
      currentGame.gameOver=currentGame.chess.isGameOver();
      renderChess();

      await roomSend('state',{
        roomId:currentGame.roomId,
        type:'chess',
        fen:currentGame.chess.fen(),
        gameOver:currentGame.gameOver
      });

      if(currentGame.gameOver){
        await roomSend('game-end',{
          roomId:currentGame.roomId,
          message:chessResult()
        });
      }
    }else{
      renderChess();
      await roomSend('move-request',{
        roomId:currentGame.roomId,
        fromId:user.id,
        from,to:sq
      });
    }
  }catch(e){
    console.warn('Chess move failed',e);
    currentGame.selected=null;
    renderChess();
  }
}

/* Vault */
async function loadVault(){if(!user)return;const{data,error}=await db.from('vault').select('*').eq('user_id',user.id).order('created_at',{ascending:false});if(error){document.getElementById('vault-list').innerHTML='<div class="text-xs text-slate-500 p-3">Vault table setup required.</div>';return}vaultItems=data||[];renderVault()}
function fmtBytes(n){n=Number(n||0);if(n<1024)return n+' B';if(n<1048576)return(n/1024).toFixed(1)+' KB';if(n<1073741824)return(n/1048576).toFixed(1)+' MB';return(n/1073741824).toFixed(1)+' GB'}
function renderVault(){document.getElementById('vault-count').textContent=`${vaultItems.length} files`;document.getElementById('vault-list').innerHTML=vaultItems.length?vaultItems.map(v=>`<div class="bg-slate-900 border border-slate-700 rounded-xl p-3 flex justify-between items-center gap-3"><div class="min-w-0"><b class="text-sm block truncate">${esc(v.title||v.file_name||'File')}</b><span class="text-[10px] text-slate-500">${esc(v.file_name||'')} • ${fmtBytes(v.file_size)}</span></div><div class="flex gap-2"><button onclick="openVaultFile('${v.id}')" class="bg-violet-600 px-3 py-2 rounded-lg text-xs font-bold">Open</button><button onclick="deleteVault('${v.id}')" class="bg-red-600 px-3 py-2 rounded-lg text-xs font-bold">Delete</button></div></div>`).join(''):'<div class="text-center py-8 text-slate-500 text-sm">Vault खाली है.</div>';}
document.getElementById('vault-form').addEventListener('submit',async e=>{e.preventDefault();const f=document.getElementById('vault-file').files[0];if(!f)return;const b=e.target.querySelector('button');b.disabled=true;b.textContent='Saving...';try{const path=`vault/${user.id}/${crypto.randomUUID()}_${f.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;const{error:up}=await db.storage.from('vault').upload(path,f,{contentType:f.type});if(up)throw up;const{error}=await db.from('vault').insert({user_id:user.id,title:document.getElementById('vault-title').value.trim(),file_name:f.name,file_type:f.type,file_size:f.size,storage_path:path});if(error)throw error;e.target.reset();toast('Saved to private vault');loadVault()}catch(err){toast(err.message||'Vault save failed',false)}finally{b.disabled=false;b.textContent='Save to Vault'}})
async function openVaultFile(id){const v=vaultItems.find(x=>String(x.id)===String(id));if(!v)return;const{data,error}=await db.storage.from('vault').createSignedUrl(v.storage_path,3600);if(error)return toast(error.message,false);window.open(data.signedUrl,'_blank','noopener')}
async function deleteVault(id){const v=vaultItems.find(x=>String(x.id)===String(id));if(!v||!confirm('Delete this vault file?'))return;const{error}=await db.from('vault').delete().eq('id',id).eq('user_id',user.id);if(error)return toast(error.message,false);if(v.storage_path)await db.storage.from('vault').remove([v.storage_path]);toast('Vault file deleted');loadVault()}

/* Leaderboard */
async function loadLeaderboard(){if(!user)return;const{data,error}=await db.from('profiles').select('id,name,pfp_url,role,xp,level').order('xp',{ascending:false}).limit(100);if(error){document.getElementById('leaderboard-list').innerHTML='<div class="text-xs text-slate-500 p-3">Leaderboard ke liye profiles table check karein.</div>';return}leaderboard=(data||[]).map(p=>({...p,xp:Number(p.xp||0),level:Number(p.level||levelFromXp(p.xp))}));renderLeaderboard();renderRHHomeRail()}
function renderLeaderboard(){const me=leaderboard.find(p=>p.id===user.id)||{xp:Number(profile.xp||0),level:Number(profile.level||levelFromXp(profile.xp))};document.getElementById('my-xp').textContent=`${me.xp} XP`;document.getElementById('my-level').textContent=`Level ${me.level}`;document.getElementById('my-xp-bar').style.width=xpPercent(me.xp)+'%';const medals=['🥇','🥈','🥉'];document.getElementById('leaderboard-list').innerHTML=leaderboard.map((p,i)=>`<div class="bg-slate-900/80 border ${p.id===user.id?'border-amber-500/50':'border-slate-700'} rounded-xl p-3 flex items-center gap-3"><div class="w-9 text-center font-bold text-lg">${medals[i]||('#'+(i+1))}</div><div class="w-9 h-9 rounded-full overflow-hidden bg-slate-700">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}" class="w-full h-full object-cover">`:'👤'}</div><div class="min-w-0 flex-1"><b class="block truncate text-sm">${esc(p.name||'Member')}${p.id===user.id?' (You)':''}</b><span class="text-[10px] text-slate-500">Level ${p.level}</span></div><b class="text-sm text-amber-300">${p.xp} XP</b></div>`).join('')||'<div class="text-center py-8 text-slate-500">No members found.</div>';}

function renderRHHomeRail(){
  const lb=document.getElementById('rh-home-leaderboard');
  if(lb && Array.isArray(leaderboard)){
    const top=leaderboard.slice(0,5);
    lb.innerHTML=top.map((p,i)=>`<div class="rh-mini-row"><div class="rh-rank">#${i+1}</div><div class="rh-mini-avatar">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}">`:'👤'}</div><div class="rh-mini-name"><b>${esc(p.name||'Member')}</b><span>Level ${p.level||1}</span></div><div class="rh-mini-xp">${Number(p.xp||0).toLocaleString()} XP</div></div>`).join('') || '<div style="font-size:11px;color:#9ba3ae">No members yet.</div>';
  }
  const online=document.getElementById('rh-home-online');
  if(online){
    const src=document.querySelectorAll('#focus-live-users [data-live-user]');
    const nodes=[...src].slice(0,6);
    online.innerHTML=nodes.map(n=>{const name=n.getAttribute('data-live-user')||'Student';return `<div class="rh-online-user"><div class="rh-online-avatar">${n.querySelector('img')?`<img src="${n.querySelector('img').src}">`:'👤'}</div><div style="margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(name)}</div></div>`}).join('') || '<span style="font-size:11px;color:#9ba3ae">अभी कोई live study नहीं कर रहा.</span>';
  }
  const mins=getFocusTodayMinutes();
  const goal=360;
  const gb=document.getElementById('rh-goal-time-bar'); if(gb)gb.style.width=Math.min(100,Math.round(mins/goal*100))+'%';
  const gt=document.getElementById('rh-goal-time'); if(gt)gt.textContent=formatMinutesSimple(mins);
  const streak=getFocusStreak(); const sb=document.getElementById('rh-goal-streak-bar'); if(sb)sb.style.width=Math.min(100,Math.round(streak/30*100))+'%'; const gs=document.getElementById('rh-goal-streak'); if(gs)gs.textContent=streak+' 🔥';
}

/* ==================== AI DOUBT TUTOR (FIXED) ==================== */
async function askAI(){
  const q = document.getElementById('ai-input').value.trim();
  const out = document.getElementById('ai-output');
  if(!q) return;

  out.classList.remove('hidden');
  out.textContent = 'AI is thinking...';

  try {
    const { data, error } = await db.functions.invoke('ai-chat', {
      body: { question: q }
    });

    if (error) throw error;

    out.textContent = data?.answer || (typeof data === 'string' ? data : 'No answer returned.');
  } catch(e) {
    console.error('AI Doubt Error:', e);
    out.textContent = 'AI request failed. Please try again.\n\n' + (e.message || 'Request failed.');
  }
}

/* ==================== AI QUIZ GENERATOR (FIXED) ==================== */
async function generateQuiz(){
  const subject = document.getElementById('quiz-subject').value;
  const topic = document.getElementById('quiz-topic').value.trim();
  const count = Number(document.getElementById('quiz-count').value) || 5;
  const box = document.getElementById('quiz-box');

  box.textContent = 'Generating AI quiz...';

  try {
    const { data, error } = await db.functions.invoke('daily-bio-event', {
      body: {
        count: count,
        topic: `${subject} - ${topic || 'NCERT Important Topics'}`
      }
    });

    if (error) throw error;

    const qs = Array.isArray(data?.questions) ? data.questions : [];

    if (!qs.length) throw new Error("No questions returned by AI");

    box.innerHTML = qs.map((x, i) => {
      const answer = Number(x.correct_index ?? x.answer ?? 0);
      const options = Array.isArray(x.options) ? x.options : [];

      return `<div class="bg-slate-900 p-4 rounded-xl">
        <b class="text-teal-300">Q${i+1}. ${esc(x.question)}</b>
        <div class="grid md:grid-cols-2 gap-2 mt-3">
          ${options.map((o, j) => `
            <button
              onclick="
                const bs=this.parentElement.querySelectorAll('button');
                bs.forEach(b=>b.disabled=true);
                bs[${answer}]?.classList.add('bg-green-600');
                if(${j}!==${answer}) this.classList.add('bg-red-600');
                awardQuizXP(${j}===${answer});
              "
              class="bg-slate-800 hover:bg-slate-700 p-2 rounded-lg text-left text-sm">
              ${esc(o)}
            </button>
          `).join('')}
        </div>
      </div>`;
    }).join('');
  } catch(e) {
    console.error('Quiz Error:', e);
    box.textContent = 'Quiz request failed. Please try again.\n\n' + (e.message || 'Request failed.');
  }
}

function openProfile(){document.getElementById('profile-name').value=profile.name||'';document.getElementById('profile-modal').classList.remove('hidden')}
function closeProfile(){document.getElementById('profile-modal').classList.add('hidden')}
document.getElementById('profile-form').addEventListener('submit',async e=>{e.preventDefault();try{const name=document.getElementById('profile-name').value.trim(),file=document.getElementById('profile-pfp').files[0];let pfp=profile.pfp_url;if(file)pfp=await uploadProfilePic(user.id,file);const {error}=await db.from('profiles').update({name,pfp_url:pfp}).eq('id',user.id);if(error)throw error;profile={...profile,name,pfp_url:pfp};document.getElementById('nav-name').textContent=name;if(pfp)document.getElementById('nav-pfp').innerHTML=`<img src="${safeUrl(pfp)}" class="w-full h-full object-cover">`;closeProfile();toast('Profile updated')}catch(err){toast(err.message,false)}});

showAuth('login');
boot();

/* ==================== GLOBAL BACKGROUND (ADMIN CONTROLLED) ==================== */
let siteSettings=null;
async function loadSiteSettings(){
 const {data,error}=await db.from('site_settings').select('*').eq('id',1).maybeSingle();
 if(error){console.warn('site_settings load failed',error);return}
 siteSettings=data||null;
 applyBackgroundToPage(siteSettings);
}
function applyBackgroundToPage(s){
 const layer=document.getElementById('hub-bg-layer'),overlay=document.getElementById('hub-bg-overlay');
 if(!layer||!overlay)return;
 if(!s||!s.background_url){
  layer.style.backgroundImage='';layer.style.filter='';layer.style.opacity='';
  overlay.style.background='rgba(0,0,0,.6)';
  return;
 }
 const url=safeUrl(s.background_url);
 layer.style.backgroundImage=url==='#'?'':`url("${url.replace(/"/g,'%22')}")`;
 layer.style.backgroundSize=s.background_size||'cover';
 layer.style.backgroundPosition=s.background_position||'center';
 layer.style.backgroundAttachment=s.background_fixed===false?'scroll':'fixed';
 layer.style.filter=`blur(${Number(s.background_blur||0)}px)`;
 layer.style.opacity=String(s.background_opacity==null?1:s.background_opacity);
 overlay.style.background=`rgba(0,0,0,${s.background_overlay==null?0.6:s.background_overlay})`;
}
function readBgFormValues(overrideUrl){
 return {
  background_url:overrideUrl!==undefined?overrideUrl:(document.getElementById('bg-url').value.trim()||null),
  background_overlay:Number(document.getElementById('bg-overlay').value),
  background_blur:Number(document.getElementById('bg-blur').value),
  background_opacity:Number(document.getElementById('bg-opacity').value),
  background_size:document.getElementById('bg-size').value,
  background_position:document.getElementById('bg-position').value,
  background_fixed:document.getElementById('bg-fixed').value==='true'
 };
}
function updateBgRangeLabels(){
 document.getElementById('bg-overlay-val').textContent=document.getElementById('bg-overlay').value;
 document.getElementById('bg-blur-val').textContent=document.getElementById('bg-blur').value+'px';
 document.getElementById('bg-opacity-val').textContent=document.getElementById('bg-opacity').value;
}
['bg-overlay','bg-blur','bg-opacity'].forEach(id=>{const el=document.getElementById(id);if(el)el.addEventListener('input',updateBgRangeLabels)});
function populateBackgroundForm(){
 const s=siteSettings||{};
 document.getElementById('bg-url').value=s.background_url||'';
 document.getElementById('bg-overlay').value=s.background_overlay==null?0.6:s.background_overlay;
 document.getElementById('bg-blur').value=s.background_blur==null?0:s.background_blur;
 document.getElementById('bg-opacity').value=s.background_opacity==null?1:s.background_opacity;
 document.getElementById('bg-size').value=s.background_size||'cover';
 document.getElementById('bg-position').value=s.background_position||'center';
 document.getElementById('bg-fixed').value=String(s.background_fixed==null?true:s.background_fixed);
 updateBgRangeLabels();
}
function previewBackground(){
 const file=document.getElementById('bg-upload').files[0];
 applyBackgroundToPage(readBgFormValues(file?URL.createObjectURL(file):undefined));
 toast('Preview applied (not saved yet)');
}
async function applyBackgroundSettings(){
 if(profile?.role!=='admin')return toast('Admin only',false);
 try{
  let url=document.getElementById('bg-url').value.trim()||null;
  const file=document.getElementById('bg-upload').files[0];
  if(file){
   const path=`backgrounds/${crypto.randomUUID()}_${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;
   const {error:upErr}=await db.storage.from('materials').upload(path,file,{contentType:file.type});
   if(upErr)throw upErr;
   url=db.storage.from('materials').getPublicUrl(path).data.publicUrl;
  }
  const values=readBgFormValues(url);
  const {error}=await db.from('site_settings').update({...values,updated_by:user.id,updated_at:new Date().toISOString()}).eq('id',1);
  if(error)throw error;
  siteSettings={...(siteSettings||{}),...values,id:1};
  document.getElementById('bg-upload').value='';
  applyBackgroundToPage(siteSettings);populateBackgroundForm();
  toast('Background applied for all users');
 }catch(err){toast(err.message||'Background update failed',false)}
}
async function resetBackgroundSettings(){
 if(profile?.role!=='admin')return toast('Admin only',false);
 try{
  const defaults={background_url:null,background_overlay:0.6,background_blur:0,background_opacity:1,background_position:'center',background_size:'cover',background_fixed:true};
  const {error}=await db.from('site_settings').update({...defaults,updated_by:user.id,updated_at:new Date().toISOString()}).eq('id',1);
  if(error)throw error;
  siteSettings={...(siteSettings||{}),...defaults,id:1};
  document.getElementById('bg-upload').value='';
  applyBackgroundToPage(siteSettings);populateBackgroundForm();
  toast('Background reset to default');
 }catch(err){toast(err.message||'Reset failed',false)}
}
loadSiteSettings();

/* ==================== FORGOT PASSWORD / PASSWORD RECOVERY ==================== */
function toggleForgotForm(){
  const form=document.getElementById('forgot-form');
  const opening=form.classList.contains('hidden');
  form.classList.toggle('hidden');
  if(opening) setTimeout(()=>document.getElementById('forgot-email')?.focus(),50);
}

async function sendPasswordResetEmail(e){
 e.preventDefault();
 const email=document.getElementById('forgot-email').value.trim().toLowerCase();
 const btn=document.getElementById('forgot-btn');
 if(!email)return;
 btn.disabled=true;btn.textContent='Sending...';
 try{
  const {error}=await db.auth.resetPasswordForEmail(email);
  if(error)throw error;
  document.getElementById('reset-otp-email').textContent='Code भेजा गया: '+email;
  document.getElementById('password-reset-modal').classList.remove('hidden');
  document.getElementById('forgot-form').classList.add('hidden');
  document.getElementById('reset-otp').focus();
  toast('Reset code email पर भेज दिया गया 📩');
 }catch(err){
  console.error('Password reset request failed:',err);
  toast(err?.message||'Reset code भेजने में समस्या हुई',false);
 }finally{
  btn.disabled=false;btn.textContent='Send OTP';
 }
}

document.getElementById('forgot-form').addEventListener('submit',sendPasswordResetEmail);

let passwordResetEmail='';
let passwordResetVerified=false;
function openPasswordResetModal(email){
 const modal=document.getElementById('password-reset-modal');
 if(modal) modal.classList.remove('hidden');
 if(email) passwordResetEmail=email;
 document.getElementById('reset-otp-email').textContent=passwordResetEmail?'Code भेजा गया: '+passwordResetEmail:'';
 document.getElementById('new-password-fields').classList.add('hidden');
 document.getElementById('verify-otp-btn').classList.remove('hidden');
 document.getElementById('reset-otp').focus();
}
function closePasswordResetModal(){
 const modal=document.getElementById('password-reset-modal');
 if(modal) modal.classList.add('hidden');
 document.getElementById('password-reset-form')?.reset();
 document.getElementById('new-password-fields')?.classList.add('hidden');
 passwordResetVerified=false;
}

document.getElementById('verify-otp-btn').addEventListener('click',async()=>{
 const otp=document.getElementById('reset-otp').value.trim();
 const email=passwordResetEmail || document.getElementById('forgot-email').value.trim().toLowerCase();
 const btn=document.getElementById('verify-otp-btn');
 if(!email)return toast('Reset email नहीं मिला. फिर से Forgot Password करें.',false);
 if(!/^\d{6,8}$/.test(otp))return toast('Kripya valid 6 ya 8-digit OTP code enter karein.',false);
 btn.disabled=true;btn.textContent='Verifying...';
 try{
  const {data,error}=await db.auth.verifyOtp({email,token:otp,type:'recovery'});
  if(error)throw error;
  passwordResetEmail=email;
  passwordResetVerified=true;
  document.getElementById('new-password-fields').classList.remove('hidden');
  btn.classList.add('hidden');
  document.getElementById('reset-otp').disabled=true;
  document.getElementById('new-password').focus();
  toast('Code verified ✅ अब नया password बनाएं');
 }catch(err){
  console.error('Recovery OTP verification failed:',err);
  toast(err?.message||'Code गलत या expire हो गया है.',false);
 }finally{
  btn.disabled=false;
  if(!passwordResetVerified)btn.textContent='Verify Code';
 }
});

document.getElementById('password-reset-form').addEventListener('submit',async e=>{
 e.preventDefault();
 if(!passwordResetVerified)return toast('पहले email वाला code verify करें.',false);
 const password=document.getElementById('new-password').value;
 const confirm=document.getElementById('confirm-password').value;
 const btn=document.getElementById('save-password-btn');
 if(password.length<6)return toast('Password कम से कम 6 characters का होना चाहिए.',false);
 if(password!==confirm)return toast('दोनों passwords समान नहीं हैं.',false);
 btn.disabled=true;btn.textContent='Updating...';
 try{
  const {error}=await db.auth.updateUser({password});
  if(error)throw error;
  toast('Password successfully changed ✅');
  closePasswordResetModal();
  await boot();
 }catch(err){
  console.error('Password update failed:',err);
  toast(err?.message||'Password update failed',false);
 }finally{
  btn.disabled=false;btn.textContent='Update Password';
 }
});

document.getElementById('resend-reset-btn').addEventListener('click',async()=>{
 const email=passwordResetEmail || document.getElementById('forgot-email').value.trim().toLowerCase();
 if(!email)return toast('Email नहीं मिला. फिर से Forgot Password करें.',false);
 try{
  const {error}=await db.auth.resetPasswordForEmail(email);
  if(error)throw error;
  document.getElementById('reset-otp').value='';
  document.getElementById('reset-otp').disabled=false;
  document.getElementById('new-password-fields').classList.add('hidden');
  document.getElementById('verify-otp-btn').classList.remove('hidden');
  passwordResetVerified=false;
  toast('नया reset code भेज दिया गया 📩');
 }catch(err){toast(err?.message||'Code resend नहीं हुआ',false)}
});

db.auth.onAuthStateChange((event,s)=>{
 if(event==='PASSWORD_RECOVERY'){
   session=s||null;
   user=s?.user||null;
 }
});

/* ==================== HUB EVENTS + DAILY AI BIOLOGY QUESTIONS ==================== */
let hubEvents=[],hubActiveEvent=null,hubDailyAnswered={};
let eventQuestionCount=0;
let isAutoSeedingEvents=false;

function addEventQuestion(){
 const box=document.getElementById('event-questions');if(!box)return;
 const i=eventQuestionCount++;
 const wrap=document.createElement('div');wrap.id=`event-question-${i}`;
 wrap.className='bg-slate-900/70 border border-slate-700 rounded-xl p-3 space-y-2';
 wrap.innerHTML=`<div class="flex justify-between items-center gap-2"><b class="text-xs text-amber-300">Question ${i+1}</b><button type="button" onclick="removeEventQuestion(${i})" class="text-red-400 text-xs font-bold">✕ Remove</button></div><input id="eq-q-${i}" required placeholder="Question ${i+1}" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"><div class="grid grid-cols-2 gap-2">${Array.from({length:4}).map((__,j)=>`<div class="flex items-center gap-2"><input type="radio" name="eq-correct-${i}" value="${j}" ${j===0?'checked':''}><input id="eq-o-${i}-${j}" required placeholder="Option ${j+1}" class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs"></div>`).join('')}</div>`;
 box.appendChild(wrap);updateEventQuestionNumbers();
}
function removeEventQuestion(i){document.getElementById(`event-question-${i}`)?.remove();updateEventQuestionNumbers()}
function updateEventQuestionNumbers(){const items=[...document.querySelectorAll('#event-questions > div')];items.forEach((el,n)=>{el.querySelector('b')?.replaceChildren(document.createTextNode(`Question ${n+1}`));});const c=document.getElementById('event-question-count');if(c)c.textContent=`${items.length} question${items.length===1?'':'s'}`}
function renderEventQuestionInputs(){const box=document.getElementById('event-questions');if(!box)return;box.innerHTML='';eventQuestionCount=0;updateEventQuestionNumbers()}
renderEventQuestionInputs();

async function loadHubEvents(){
 if(!user)return;
 const {data,error}=await db.from('hub_events').select('*').order('created_at',{ascending:false});
 if(error){console.error(error);return}
 hubEvents=data||[];
 markDailyBioStatus();
 const now=new Date();
 hubActiveEvent=hubEvents.find(e=>e.is_active&&new Date(e.start_at)<=now&&new Date(e.ends_at)>now)||null;

 // Automatic AI Generation if no active event found today
 if(!hubActiveEvent && !isAutoSeedingEvents){
   autoSeedDailyBioEvent();
 }

 const daily=hubEvents.find(isDailyBioEvent);
 if(daily&&daily.id&&localStorage.getItem('rh_daily_bio_notified')!==daily.id){
   if('Notification' in window && Notification.permission==='granted') new Notification('🧬 Daily Biology Challenge',{body:'Aaj ke naye Hindi Biology questions ready hain.'});
   localStorage.setItem('rh_daily_bio_notified',daily.id);
 }
 await renderHubActiveEvent();
 if(profile?.role==='admin')renderHubEventsAdminList();
}

async function autoSeedDailyBioEvent(){
  isAutoSeedingEvents = true;
  try {
    const today = localDateValue();
    const start_at = new Date(`${today}T00:00:00`).toISOString();
    const ends_at = new Date(`${today}T23:59:59.999`).toISOString();

    const { data: aiRes, error: aiErr } = await db.functions.invoke('daily-bio-event', {
      body: { count: 5 }
    });

    if (aiErr) throw aiErr;

    const questions = Array.isArray(aiRes?.questions) ? aiRes.questions : [];
    if (!questions.length) throw new Error("No AI questions returned");

    const { data: refreshed } = await db.from('hub_events').select('*').order('created_at', { ascending: false });
    hubEvents = refreshed || [];
    const now = new Date();
    hubActiveEvent = hubEvents.find(e => e.is_active && new Date(e.start_at) <= now && new Date(e.ends_at) > now) || {
      id: 'daily_bio_ai_' + today,
      title: 'Daily Biology Challenge',
      description: `NEET NCERT Hindi Biology (${aiRes.provider || 'AI'} Generated) — Daily +100 XP`,
      start_at,
      ends_at,
      is_active: true,
      questions
    };

    renderHubActiveEvent();
  } catch(e) {
    console.error("Auto AI seeding failed:", e);
  } finally {
    isAutoSeedingEvents = false;
  }
}

function isDailyBioEvent(ev){
  if(!ev) return false;
  const title=String(ev.title||'').toLowerCase();
  return title.includes('daily biology') || title.includes('daily bio') || title.includes('दैनिक जीवविज्ञान');
}
function markDailyBioStatus(){
  const el=document.getElementById('daily-bio-status');
  if(!el)return;
  const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata'}).format(new Date());
  const ev=hubEvents.find(isDailyBioEvent) || hubActiveEvent;
  if(ev){
    const q=Array.isArray(ev.questions)?ev.questions.length:5;
    el.innerHTML=`<i class="fa-solid fa-dna mr-2"></i><b>Daily Biology Challenge</b> • ${q} Hindi questions • ${today} • Active`;
  }
}
async function renderHubActiveEvent(){
 const box=document.getElementById('hub-active-event'),none=document.getElementById('hub-no-event');
 if(!box||!none)return;
 if(!hubActiveEvent){box.classList.add('hidden');none.classList.remove('hidden');hubDailyAnswered={};return}
 none.classList.add('hidden');box.classList.remove('hidden');
 document.getElementById('hub-event-title').textContent=(isDailyBioEvent(hubActiveEvent)?'🧬 ':'')+hubActiveEvent.title;
 document.getElementById('hub-event-desc').textContent=hubActiveEvent.description||'';
 await loadHubDailyAnswers();
}
async function loadHubDailyAnswers(){
 if(!user||!hubActiveEvent)return;
 const today=localDateValue();
 if(!String(hubActiveEvent.id).startsWith('daily_bio_ai_')){
   const {data,error}=await db.from('hub_daily_answers').select('question_index').eq('user_id',user.id).eq('event_id',hubActiveEvent.id).eq('answer_date',today);
   hubDailyAnswered={};
   if(error){console.error(error)}else{(data||[]).forEach(r=>hubDailyAnswered[r.question_index]=true)}
 }
 renderHubQuestions();
}

function renderHubQuestions(){
 const box=document.getElementById('hub-questions-box');if(!box)return;
 const qs=Array.isArray(hubActiveEvent?.questions)?hubActiveEvent.questions:[];
 const correctCount=Object.keys(hubDailyAnswered).length;
 document.getElementById('hub-progress-label').textContent=`${correctCount}/${qs.length}`;
 document.getElementById('hub-progress-bar').style.width=(qs.length?correctCount/qs.length*100:0)+'%';
 box.innerHTML=qs.map((q,i)=>{
  const locked=!!hubDailyAnswered[i];
  const opts=Array.isArray(q.options)?q.options:[];
  return `<div class="bg-slate-800/95 border ${locked?'border-emerald-500/50 bg-emerald-950/20':'border-slate-700'} rounded-2xl p-4 transition-all">
  <div class="flex justify-between items-start gap-2"><b class="text-sm text-white">Q${i+1}. ${esc(q.question)}</b>${locked?'<span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded shrink-0 font-bold">✓ Solved (+100 XP)</span>':''}</div>
  <div class="grid md:grid-cols-2 gap-2 mt-3" id="hub-q-opts-${i}">
    ${opts.map((o,j)=>`<button ${locked?'disabled':''} onclick="answerHubQuestion(${i},${j},this)" class="bg-slate-900 hover:bg-slate-700 disabled:opacity-75 disabled:cursor-not-allowed p-3 rounded-lg text-left text-sm border border-slate-700 text-slate-200 transition-all">${esc(o)}</button>`).join('')}
  </div>
  </div>`;
 }).join('')||'<div class="text-center text-slate-500 py-6">Questions available nahi hain.</div>';
}

async function answerHubQuestion(qIndex,optIndex,btnElem){
 if(!user)return toast('Pehle login karein.',false);
 if(!hubActiveEvent)return toast('Koi active event nahi mila.',false);
 if(hubDailyAnswered[qIndex])return toast('Ye question aap pehle hi solve kar chuke hain.',false);
 
 const q=hubActiveEvent.questions[qIndex];if(!q)return;
 const parent=document.getElementById(`hub-q-opts-${qIndex}`);
 const buttons=parent?parent.querySelectorAll('button'):[];

 if(Number(optIndex)!==Number(q.correct_index)){
  if(btnElem){
    btnElem.classList.add('bg-red-600','border-red-500','text-white');
    setTimeout(()=>{
      btnElem.classList.remove('bg-red-600','border-red-500','text-white');
    },1500);
  }
  toast('Galat jawab! Sahi option select karein.',false);
  return;
 }

 if(btnElem)btnElem.classList.add('bg-emerald-600','border-emerald-500','text-white');
 buttons.forEach(b=>b.disabled=true);

 const today=localDateValue();
 try{
   if(!String(hubActiveEvent.id).startsWith('daily_bio_ai_')){
     const {error}=await db.from('hub_daily_answers').insert({
       user_id:user.id,
       event_id:hubActiveEvent.id,
       answer_date:today,
       question_index:qIndex,
       is_correct:true,
       xp_awarded:100
     });
     if(error&&error.code!=='23505') throw error;
   }

   hubDailyAnswered[qIndex]=true;
   await grantXP(100);
   toast('Sahi Jawab! +100 XP 🎉');
   renderHubQuestions();
 }catch(err){
   console.error('Answer save failed:',err);
   toast(err.message||'Answer save nahi ho saka.',false);
   buttons.forEach(b=>b.disabled=false);
 }
}

function tickHubCountdown(){
 const el=document.getElementById('hub-countdown');if(!el)return;
 if(!hubActiveEvent){el.textContent='--:--:--';return}
 const diff=new Date(hubActiveEvent.ends_at)-new Date();
 if(diff<=0){el.textContent='00:00:00';if(user)loadHubEvents();return}
 const h=Math.floor(diff/3600000),m=Math.floor(diff%3600000/60000),s=Math.floor(diff%60000/1000);
 el.textContent=`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
setInterval(tickHubCountdown,1000);
setInterval(()=>{if(user)loadHubEvents()},30000);
setInterval(()=>{if(user)renderHomeDashboard()},5000);

function renderHubEventsAdminList(){
 const box=document.getElementById('hub-events-list');if(!box)return;
 box.innerHTML=hubEvents.length?hubEvents.map(ev=>{
  const now=new Date(),live=ev.is_active&&new Date(ev.start_at)<=now&&new Date(ev.ends_at)>now;
  return `<div class="bg-slate-900/70 border border-slate-700 rounded-xl p-3 flex justify-between items-center gap-2">
   <div class="min-w-0"><b class="text-sm block truncate">${esc(ev.title)}</b><span class="text-[10px] ${live?'text-emerald-400':'text-slate-500'}">${live?'● LIVE':(ev.is_active?'Scheduled/Ended':'Inactive')}</span></div>
   <div class="flex gap-2 shrink-0"><button onclick="toggleEventActive('${ev.id}',${!ev.is_active})" class="bg-slate-700 hover:bg-slate-600 px-2 py-1.5 rounded-lg text-[10px] font-bold">${ev.is_active?'Deactivate':'Activate'}</button><button onclick="deleteHubEvent('${ev.id}')" class="bg-red-600 hover:bg-red-500 px-2 py-1.5 rounded-lg text-[10px] font-bold">Delete</button></div>
  </div>`;
 }).join(''):'<div class="text-xs text-slate-500 p-3">Koi event nahi banaya gaya.</div>';
}
async function toggleEventActive(id,val){
 const {error}=await db.from('hub_events').update({is_active:val}).eq('id',id);
 if(error)toast(error.message,false);else await loadHubEvents();
}
async function deleteHubEvent(id){
 if(!confirm('Delete this event?'))return;
 const {error}=await db.from('hub_events').delete().eq('id',id);
 if(error)toast(error.message,false);else{toast('Event deleted');await loadHubEvents()}
}
document.getElementById('hub-event-form').addEventListener('submit',async e=>{
 e.preventDefault();
 if(profile?.role!=='admin')return toast('Admin only',false);
 const btn=document.getElementById('event-btn');btn.disabled=true;btn.textContent='Creating...';
 try{
  const items=[...document.querySelectorAll('#event-questions > div')];
  if(!items.length)throw new Error('Kam se kam 1 question add karo.');
  const questions=items.map(el=>{const qInput=el.querySelector('input[id^="eq-q-"]');const idx=qInput.id.replace('eq-q-','');const options=Array.from({length:4}).map((__,j)=>document.getElementById(`eq-o-${idx}-${j}`).value.trim());const correctEl=el.querySelector(`input[name="eq-correct-${idx}"]:checked`);return {question:qInput.value.trim(),options,correct_index:Number(correctEl?.value||0)}});
  if(questions.some(q=>!q.question||q.options.some(o=>!o)))throw new Error('Har question aur 4 options bharna zaroori hai.');
  const start_at=new Date(document.getElementById('event-start').value).toISOString();
  const ends_at=new Date(document.getElementById('event-end').value).toISOString();
  if(new Date(ends_at)<=new Date(start_at))throw new Error('End time start time se baad hona chahiye.');
  const {error}=await db.from('hub_events').insert({
   title:document.getElementById('event-title').value.trim(),
   description:document.getElementById('event-desc').value.trim(),
   start_at,ends_at,
   is_active:document.getElementById('event-active').checked,
   questions,created_by:user.id
  });
  if(error)throw error;
  e.target.reset();document.getElementById('event-active').checked=true;renderEventQuestionInputs();
  toast('HUB Event created');await loadHubEvents();
 }catch(err){toast(err.message||'Event create failed',false)}
 finally{btn.disabled=false;btn.textContent='Create Event'}
});

async function grantXP(amount){
 if(!user||!profile||!amount)return;
 const next=Number(profile.xp||0)+Number(amount);
 const level=levelFromXp(next);
 const {error}=await db.from('profiles').update({xp:next,level}).eq('id',user.id);
 if(error){console.warn('XP update failed',error);return}
 profile.xp=next;profile.level=level;
 renderHomeDashboard();
 const lb=document.getElementById('section-leaderboard');
 if(lb&&!lb.classList.contains('hidden'))loadLeaderboard();
}

/* ==================== SPIN & WIN ==================== */
let hubSpinToday=null;
const SPIN_REWARDS=[
 {label:'+50 XP',xp:50,angle:30},
 {label:'+100 XP',xp:100,angle:90},
 {label:'+150 XP',xp:150,angle:150},
 {label:'+250 XP',xp:250,angle:210},
 {label:'⚡ Streak Boost (+75 XP)',xp:75,angle:270},
 {label:'🎁 Rare Mystery Reward (+300 XP)',xp:300,angle:330}
];
async function loadSpinStatus(){
 if(!user)return;
 const today=localDateValue();
 const {data,error}=await db.from('hub_spins').select('user_id,spin_date,reward,xp_awarded').eq('user_id',user.id).eq('spin_date',today).maybeSingle();
 if(error){console.error(error);return}
 hubSpinToday=data||null;
 renderSpinStatus();
}
function renderSpinStatus(){
 const btn=document.getElementById('spin-btn'),res=document.getElementById('spin-result');
 if(!btn||!res)return;
 if(hubSpinToday){
  btn.disabled=true;btn.textContent='Spin Used';
  res.textContent=`Aaj ka spin already use ho chuka hai. Reward: +${hubSpinToday.xp_awarded} XP`;
 }else{
  btn.disabled=false;btn.textContent='Spin Now';res.textContent='';
 }
}
async function spinWheel(){
 if(!user)return;
 if(hubSpinToday)return toast('Aaj ka spin already use ho chuka hai.',false);
 const btn=document.getElementById('spin-btn');btn.disabled=true;
 const pick=SPIN_REWARDS[Math.floor(Math.random()*SPIN_REWARDS.length)];
 const today=localDateValue();
 const {error}=await db.from('hub_spins').insert({user_id:user.id,spin_date:today,reward:pick.label,xp_awarded:pick.xp});
 if(error){
  if(error.code==='23505'){await loadSpinStatus();toast('Aaj ka spin already use ho chuka hai.',false);}
  else{toast(error.message||'Spin failed',false);btn.disabled=false;}
  return;
 }
 hubSpinToday={reward:pick.label,xp_awarded:pick.xp,spin_date:today};
 const wheel=document.getElementById('spin-wheel');
 if(wheel)wheel.style.transform=`rotate(${5*360+(360-pick.angle)}deg)`;
 await grantXP(pick.xp);
 setTimeout(()=>{toast(`🎉 ${pick.label}!`);renderSpinStatus()},3000);
}

/* ==================== STUDY ROOMS + LIVE VOICE ==================== */
const STUDY_ROOMS=[
 {key:'physics',name:'Physics Room',icon:'⚛️'},
 {key:'biology',name:'Biology Room',icon:'🧬'},
 {key:'general',name:'General Study',icon:'📚'}
];
const MAX_VOICE_USERS=5;
const RTC_CONFIG={iceServers:[
 {urls:'stun:stun.l.google.com:19302'},
 {urls:'stun:stun1.l.google.com:19302'}
]};
let roomChannels={},voiceState={};

function studyRoomCardHtml(r){
 return `<div id="room-card-${r.key}" class="bg-slate-800/95 border border-teal-500/20 rounded-2xl p-4">
  <div class="flex justify-between items-start"><div><h4 class="font-bold">${r.icon} ${r.name}</h4><span id="room-count-${r.key}" class="text-[10px] bg-emerald-500/10 text-emerald-300 px-2 py-1 rounded">0 online</span></div></div>
  <div id="room-members-${r.key}" class="mt-3 flex flex-wrap gap-1"></div>
  <div class="mt-4 flex gap-2">
   <button id="room-join-${r.key}" onclick="joinStudyRoom('${r.key}')" class="flex-1 bg-teal-600 hover:bg-teal-500 py-2 rounded-lg text-xs font-bold">Join</button>
   <button id="room-leave-${r.key}" onclick="leaveStudyRoom('${r.key}')" class="hidden flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-xs font-bold">Leave</button>
  </div>
  <div id="room-voice-${r.key}" class="hidden mt-3 pt-3 border-t border-slate-700">
   <div class="flex justify-between items-center"><span class="text-[10px] uppercase text-slate-400">🎙 Live Voice</span><span id="room-voice-count-${r.key}" class="text-[10px] text-fuchsia-300">0/${MAX_VOICE_USERS}</span></div>
   <div id="room-speakers-${r.key}" class="mt-2 flex flex-wrap gap-1"></div>
   <div class="mt-2 flex gap-2">
    <button id="voice-join-${r.key}" onclick="joinVoice('${r.key}')" class="flex-1 bg-fuchsia-600 hover:bg-fuchsia-500 py-2 rounded-lg text-xs font-bold">Join Voice</button>
    <button id="voice-mute-${r.key}" onclick="toggleMute('${r.key}')" class="hidden flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-xs font-bold">Mute</button>
    <button id="voice-leave-${r.key}" onclick="leaveVoice('${r.key}')" class="hidden flex-1 bg-red-600 hover:bg-red-500 py-2 rounded-lg text-xs font-bold">Leave Voice</button>
   </div>
   <div id="room-audio-${r.key}" class="hidden"></div>
  </div>
 </div>`;
}
function renderStudyRooms(){
 const box=document.getElementById('study-rooms-box');if(!box||!user)return;
 if(!box.dataset.built){box.innerHTML=STUDY_ROOMS.map(studyRoomCardHtml).join('');box.dataset.built='1'}
 STUDY_ROOMS.forEach(r=>ensureRoomChannel(r.key));
}
function ensureRoomChannel(key){
 if(!user)return null;
 if(roomChannels[key])return roomChannels[key];
 const ch=db.channel('study-room-'+key,{config:{presence:{key:user.id},broadcast:{self:false}}});
 const rc={channel:ch,joined:false,ready:null};roomChannels[key]=rc;
 ch.on('presence',{event:'sync'},()=>renderRoomMembers(key))
  .on('presence',{event:'join'},()=>renderRoomMembers(key))
  .on('presence',{event:'leave'},({leftPresences})=>{
   renderRoomMembers(key);
   (leftPresences||[]).forEach(p=>{if(p?.user_id){closePeer(key,p.user_id);removeVoiceReservation(key,p.user_id)}});
  })
  .on('broadcast',{event:'voice-signal'},x=>handleVoiceSignal(key,x.payload));
 rc.ready=new Promise((resolve,reject)=>{
  const timeout=setTimeout(()=>reject(new Error('Realtime connection timeout')),10000);
  ch.subscribe(status=>{
   if(status==='SUBSCRIBED'){clearTimeout(timeout);resolve(true)}
   else if(status==='CHANNEL_ERROR'||status==='TIMED_OUT'){clearTimeout(timeout);reject(new Error('Realtime channel connection failed'))}
  });
 });
 rc.ready.catch(e=>console.warn('Room channel:',key,e));
 return rc;
}
function getVoicePeople(key){
 const rc=roomChannels[key];if(!rc)return [];
 const state=rc.channel.presenceState();
 return Object.values(state).flat().filter((p,i,a)=>p&&p.user_id&&p.voice&&a.findIndex(x=>x.user_id===p.user_id)===i);
}
function renderRoomMembers(key){
 const rc=roomChannels[key];if(!rc)return;
 const state=rc.channel.presenceState();
 const people=Object.values(state).flat().filter((p,i,a)=>p&&p.user_id&&a.findIndex(x=>x.user_id===p.user_id)===i);
 const countEl=document.getElementById(`room-count-${key}`);if(countEl)countEl.textContent=`${people.length} online`;
 const membersEl=document.getElementById(`room-members-${key}`);
 if(membersEl)membersEl.innerHTML=people.length?people.map(p=>`<span class="text-[10px] bg-slate-900 border border-slate-700 rounded-full px-2 py-1">${esc(p.name||'Member')}</span>`).join(''):'<span class="text-[10px] text-slate-500">Koi member nahi</span>';
 const speakers=people.filter(p=>p.voice);
 const vc=document.getElementById(`room-voice-count-${key}`);if(vc)vc.textContent=`${speakers.length}/${MAX_VOICE_USERS} in voice`;
 const sp=document.getElementById(`room-speakers-${key}`);
 if(sp)sp.innerHTML=speakers.length?speakers.map(p=>`<span class="text-[10px] bg-fuchsia-500/10 text-fuchsia-300 border border-fuchsia-500/30 rounded-full px-2 py-1">🎙 ${esc(p.name||'Member')}</span>`).join(''):'<span class="text-[10px] text-slate-500">Koi bol nahi raha</span>';
 const vb=document.getElementById(`voice-join-${key}`);
 if(vb&&!ensureVoiceState(key).joined)vb.disabled=speakers.length>=MAX_VOICE_USERS;
}
async function joinStudyRoom(key){
 const rc=ensureRoomChannel(key);if(!rc||rc.joined)return;
 try{await rc.ready;await rc.channel.track({user_id:user.id,name:profile?.name||user.email||'Member',voice:false})}
 catch(e){console.error(e);return toast('Study room connect nahi ho pa raha.',false)}
 rc.joined=true;
 document.getElementById(`room-join-${key}`).classList.add('hidden');
 document.getElementById(`room-leave-${key}`).classList.remove('hidden');
 document.getElementById(`room-voice-${key}`).classList.remove('hidden');
 renderRoomMembers(key);
}
async function leaveStudyRoom(key){
 await leaveVoice(key);
 const rc=roomChannels[key];if(!rc||!rc.joined)return;
 try{await rc.channel.untrack()}catch(e){}
 rc.joined=false;
 document.getElementById(`room-join-${key}`).classList.remove('hidden');
 document.getElementById(`room-leave-${key}`).classList.add('hidden');
 document.getElementById(`room-voice-${key}`).classList.add('hidden');
}
function ensureVoiceState(key){
 if(!voiceState[key])voiceState[key]={joined:false,muted:false,stream:null,peers:{},pendingIce:{},heartbeat:null};
 return voiceState[key];
}
async function reserveVoiceSlot(key){
 const {data,error}=await db.rpc('join_hub_voice_room',{p_room:key});
 if(error)throw error;
 if(!data?.ok)throw new Error(data?.message||`Voice room full`);
 return data;
}
async function releaseVoiceSlot(key){
 try{await db.rpc('leave_hub_voice_room',{p_room:key})}catch(e){console.warn('voice slot release failed',e)}
}
function startVoiceHeartbeat(key){
 const vs=ensureVoiceState(key);clearInterval(vs.heartbeat);
 vs.heartbeat=setInterval(async()=>{
  if(!vs.joined)return;
  try{const {data}=await db.rpc('join_hub_voice_room',{p_room:key});if(!data?.ok)await leaveVoice(key)}catch(e){console.warn('voice heartbeat failed',e)}
 },30000);
}
function stopVoiceHeartbeat(key){const vs=voiceState[key];if(vs?.heartbeat)clearInterval(vs.heartbeat);if(vs)vs.heartbeat=null}
async function joinVoice(key){
 const vs=ensureVoiceState(key);if(vs.joined)return;
 const rc=roomChannels[key];if(!rc||!rc.joined)return toast('Pehle room join karein.',false);
 if(!window.isSecureContext&&location.hostname!=='localhost')return toast('Live Voice ke liye HTTPS zaroori hai.',false);
 if(!navigator.mediaDevices?.getUserMedia)return toast('Microphone support nahi hai.',false);
 const current=getVoicePeople(key);
 if(current.length>=MAX_VOICE_USERS)return toast(`Live Voice full hai.`,false);
 try{
  await rc.ready;
  await reserveVoiceSlot(key);
  try{
   vs.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
  }catch(e){await releaseVoiceSlot(key);throw e}
  vs.joined=true;vs.muted=false;
  await rc.channel.track({user_id:user.id,name:profile?.name||user.email||'Member',voice:true});
  startVoiceHeartbeat(key);
  await rc.channel.send({type:'broadcast',event:'voice-signal',payload:{type:'join',fromId:user.id}});
  document.getElementById(`voice-join-${key}`).classList.add('hidden');
  const mb=document.getElementById(`voice-mute-${key}`);mb.classList.remove('hidden');mb.textContent='Mute';
  document.getElementById(`voice-leave-${key}`).classList.remove('hidden');
  renderRoomMembers(key);
 }catch(e){
  console.error('joinVoice failed',e);
  if(vs.stream)vs.stream.getTracks().forEach(t=>t.stop());vs.stream=null;vs.joined=false;
  toast(e?.message||'Live Voice start nahi hua.',false);
 }
}
function createPeer(key,peerId){
 const vs=ensureVoiceState(key);if(vs.peers[peerId])return vs.peers[peerId];
 let pc;try{pc=new RTCPeerConnection(RTC_CONFIG)}catch(e){console.warn('RTCPeerConnection failed',e);return null}
 if(vs.stream)vs.stream.getTracks().forEach(t=>pc.addTrack(t,vs.stream));
 pc.onicecandidate=e=>{if(e.candidate)roomChannels[key]?.channel.send({type:'broadcast',event:'voice-signal',payload:{type:'ice',fromId:user.id,targetId:peerId,candidate:e.candidate}})};
 pc.ontrack=e=>{
  let audio=document.getElementById(`voice-audio-${key}-${peerId}`);
  if(!audio){audio=document.createElement('audio');audio.id=`voice-audio-${key}-${peerId}`;audio.autoplay=true;audio.playsInline=true;audio.controls=false;document.getElementById(`room-audio-${key}`).appendChild(audio)}
  audio.srcObject=e.streams[0];audio.play().catch(()=>{});
 };
 pc.onconnectionstatechange=()=>{if(['failed','closed','disconnected'].includes(pc.connectionState))closePeer(key,peerId)};
 vs.peers[peerId]=pc;return pc;
}
function closePeer(key,peerId){
 const vs=voiceState[key];if(!vs)return;const pc=vs.peers[peerId];if(pc){try{pc.close()}catch(e){}delete vs.peers[peerId]}
 delete vs.pendingIce?.[peerId];const audio=document.getElementById(`voice-audio-${key}-${peerId}`);if(audio)audio.remove();
}
function removeVoiceReservation(key,peerId){ if(peerId&&peerId!==user.id){} }
async function handleVoiceSignal(key,payload){
 if(!payload||payload.fromId===user.id)return;
 const vs=ensureVoiceState(key),rc=roomChannels[key];if(!rc||!vs.joined)return;
 try{
  if(payload.type==='join'){
   if(String(user.id)>String(payload.fromId))return;
   const pc=createPeer(key,payload.fromId);if(!pc)return;
   const offer=await pc.createOffer();await pc.setLocalDescription(offer);
   await rc.channel.send({type:'broadcast',event:'voice-signal',payload:{type:'offer',fromId:user.id,targetId:payload.fromId,sdp:offer}});
  }else if(payload.type==='offer'&&payload.targetId===user.id){
   const pc=createPeer(key,payload.fromId);if(!pc)return;
   await pc.setRemoteDescription(new RTCSessionDescription(payload.sdp));
   const pending=vs.pendingIce?.[payload.fromId]||[];for(const c of pending)await pc.addIceCandidate(c).catch(()=>{});delete vs.pendingIce[payload.fromId];
   const answer=await pc.createAnswer();await pc.setLocalDescription(answer);
   await rc.channel.send({type:'broadcast',event:'voice-signal',payload:{type:'answer',fromId:user.id,targetId:payload.fromId,sdp:answer}});
  }else if(payload.type==='answer'&&payload.targetId===user.id){
   const pc=vs.peers[payload.fromId];if(pc&&!pc.remoteDescription)await pc.setRemoteDescription(new RTCSessionDescription(payload.sdp));
  }else if(payload.type==='ice'&&payload.targetId===user.id){
   const pc=vs.peers[payload.fromId];if(!pc)return;
   if(pc.remoteDescription?.type)await pc.addIceCandidate(payload.candidate).catch(()=>{});else (vs.pendingIce[payload.fromId]??=[]).push(payload.candidate);
  }else if(payload.type==='leave')closePeer(key,payload.fromId);
 }catch(e){console.warn('Voice signaling failed',e)}
}
function toggleMute(key){
 const vs=voiceState[key];if(!vs||!vs.stream)return;vs.muted=!vs.muted;vs.stream.getAudioTracks().forEach(t=>t.enabled=!vs.muted);
 document.getElementById(`voice-mute-${key}`).textContent=vs.muted?'Unmute':'Mute';
}
async function leaveVoice(key){
 const vs=voiceState[key];if(!vs||!vs.joined)return;
 stopVoiceHeartbeat(key);
 Object.keys(vs.peers).forEach(pid=>closePeer(key,pid));
 if(vs.stream)vs.stream.getTracks().forEach(t=>t.stop());vs.stream=null;vs.joined=false;vs.muted=false;
 const rc=roomChannels[key];if(rc){try{await rc.channel.send({type:'broadcast',event:'voice-signal',payload:{type:'leave',fromId:user.id}})}catch(e){};if(rc.joined)try{await rc.channel.track({user_id:user.id,name:profile?.name||user.email||'Member',voice:false})}catch(e){}}
 await releaseVoiceSlot(key);
 const jb=document.getElementById(`voice-join-${key}`),mb=document.getElementById(`voice-mute-${key}`),lb=document.getElementById(`voice-leave-${key}`),ab=document.getElementById(`room-audio-${key}`);
 if(jb)jb.classList.remove('hidden');if(mb)mb.classList.add('hidden');if(lb)lb.classList.add('hidden');if(ab)ab.innerHTML='';renderRoomMembers(key);
}
function stopAllVoiceAndRooms(){
 Object.keys(voiceState).forEach(key=>{const vs=voiceState[key];if(!vs)return;stopVoiceHeartbeat(key);Object.keys(vs.peers).forEach(pid=>closePeer(key,pid));if(vs.stream)vs.stream.getTracks().forEach(t=>t.stop());try{releaseVoiceSlot(key)}catch(e){}});
 voiceState={};Object.keys(roomChannels).forEach(key=>{const rc=roomChannels[key];if(!rc)return;try{rc.channel.untrack()}catch(e){}try{db.removeChannel(rc.channel)}catch(e){}});roomChannels={};
}
window.addEventListener('pagehide',()=>{try{stopAllVoiceAndRooms()}catch(e){}});
window.addEventListener('beforeunload',()=>{try{stopAllVoiceAndRooms()}catch(e){}});

/* ==================== RATHOD HUB FOCUS / YPT-STYLE TIMER ==================== */
let focusState={duration:1800,remaining:1800,status:'idle',startedAt:null,pausedAt:null,elapsedBeforePause:0,subject:'Biology',pomodoro:false,break:false};
let focusInterval=null,focusChannel=null,focusHeartbeat=null,focusReady=false;
let livePeersMap={};
const FOCUS_KEY_PREFIX='rathod_focus_v2_';
function focusKey(){return FOCUS_KEY_PREFIX+(user?.id||'guest')}
function focusStoreKey(){return focusKey()+'_state'}
function focusStatsKey(){return focusKey()+'_stats'}
function focusDefaultStats(){return {sessions:[],goalHours:4}}
function readFocusStats(){try{return JSON.parse(localStorage.getItem(focusStatsKey())||JSON.stringify(focusDefaultStats()))}catch{return focusDefaultStats()}}
function writeFocusStats(x){localStorage.setItem(focusStatsKey(),JSON.stringify(x))}
function saveFocusState(){if(!user)return;localStorage.setItem(focusStoreKey(),JSON.stringify(focusState))}
function readFocusState(){try{const x=JSON.parse(localStorage.getItem(focusStoreKey())||'null');return x&&Number(x.duration)>0?x:null}catch{return null}}
function fmtFocus(sec){sec=Math.max(0,Math.floor(sec));const h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`}
function fmtHM(sec){sec=Math.max(0,Math.floor(sec));const h=Math.floor(sec/3600),m=Math.floor(sec%3600/60);return `${h}h ${m}m`}
function localDay(d=new Date()){return localDateValue(d)}
function addDays(dateStr,n){const d=new Date(dateStr+'T12:00:00');d.setDate(d.getDate()+n);return localDay(d)}
function focusElapsed(){if(focusState.status!=='running'||!focusState.startedAt)return focusState.elapsedBeforePause||0;return Math.max(0,(Date.now()-focusState.startedAt)/1000)+(focusState.elapsedBeforePause||0)}
function focusRemaining(){if(focusState.status==='running')return Math.max(0,focusState.duration-focusElapsed());return Math.max(0,focusState.remaining)}
function setFocusPreset(min){if(focusState.status==='running')return toast('Timer running hai — pehle pause/stop karo.',false);document.getElementById('focus-duration').value=min;focusState.duration=min*60;focusState.remaining=focusState.duration;focusState.break=false;focusState.pomodoro=false;saveFocusState();renderFocusTimer()}
function setCustomFocusDuration(){if(focusState.status==='running')return;let min=Math.min(720,Math.max(1,Number(document.getElementById('focus-duration').value)||30));document.getElementById('focus-duration').value=min;focusState.duration=min*60;focusState.remaining=focusState.duration;focusState.break=false;focusState.pomodoro=false;saveFocusState();renderFocusTimer()}
function startFocusTimer(){
 if(!user)return toast('Please login first.',false);
 if(focusState.status==='running')return;
 focusState.subject=document.getElementById('focus-subject')?.value||focusState.subject||'Other';
 if(focusState.remaining<=0||focusState.remaining>focusState.duration)focusState.remaining=focusState.duration;
 focusState.startedAt=Date.now();focusState.status='running';focusState.pausedAt=null;saveFocusState();startFocusTicker();broadcastFocus();renderFocusTimer();toast('Focus session started 🔥');
}

function startFocusTicker(){if(focusInterval)clearInterval(focusInterval);focusInterval=setInterval(tickFocus,500);tickFocus()}
function tickFocus(){
 if(!focusReady)return;
 const rem=focusRemaining();focusState.remaining=rem;renderFocusTimer();broadcastFocusThrottled();
 if(focusState.status==='running'&&rem<=0)completeFocusTimer();
}
function pauseFocusTimer(){if(focusState.status!=='running')return;focusState.elapsedBeforePause=focusElapsed();focusState.remaining=Math.max(0,focusState.duration-focusState.elapsedBeforePause);focusState.status='paused';focusState.startedAt=null;focusState.pausedAt=Date.now();saveFocusState();renderFocusTimer();broadcastFocus();toast('Timer paused ⏸️')}
function stopFocusTimer(){
  if(!['running','paused'].includes(focusState.status))return;
  const elapsed=focusState.status==='running'?focusElapsed():focusState.elapsedBeforePause;
  if(elapsed>=60)recordFocusSession(Math.min(elapsed,focusState.duration),focusState.subject);
  focusState={duration:focusState.duration,remaining:focusState.duration,status:'idle',startedAt:null,pausedAt:null,elapsedBeforePause:0,subject:focusState.subject||'Other',pomodoro:false,break:false};
  saveFocusState();
  renderFocusTimer();
  renderFocusDashboard();
  renderHomeDashboard();
  broadcastFocus();
  toast('Session stopped.');
}
function resetFocusTimer(){if(focusState.status==='running')return toast('Running timer ko reset karne se pehle pause karo.',false);const d=focusState.duration||1800;focusState={duration:d,remaining:d,status:'idle',startedAt:null,pausedAt:null,elapsedBeforePause:0,subject:document.getElementById('focus-subject')?.value||'Biology',pomodoro:false,break:false};saveFocusState();renderFocusTimer();broadcastFocus()}
function startPomodoro(){if(focusState.status==='running')return toast('Timer already running hai.',false);document.getElementById('focus-duration').value=50;focusState={duration:3000,remaining:3000,status:'idle',startedAt:null,pausedAt:null,elapsedBeforePause:0,subject:document.getElementById('focus-subject')?.value||'Biology',pomodoro:true,break:false};saveFocusState();startFocusTimer()}
function completeFocusTimer(){
  if(focusState.status!=='running')return;
  const wasBreak=!!focusState.break;
  const studied=Math.min(focusState.duration,Math.max(0,focusElapsed()));
  focusState.remaining=0;
  focusState.status='idle';
  focusState.startedAt=null;
  focusState.elapsedBeforePause=0;
  saveFocusState();
  renderFocusTimer();
  if(wasBreak){
    notifyFocus('☕ Break complete','Your 10-minute break is over. Ready for the next focus session?');
    toast('Break complete ☕');
    return;
  }
  if(studied>=60)recordFocusSession(studied,focusState.subject);
  notifyFocus('🎉 Focus session complete','Great job! Your study session is complete.');
  toast('Focus complete! 🎉 +25 XP');
  if(user)grantXP(25);
  renderFocusDashboard();
  renderHomeDashboard();
  if(focusState.pomodoro){setTimeout(()=>startPomodoroBreak(),350);}
}
function startPomodoroBreak(){if(focusInterval)clearInterval(focusInterval);focusState={duration:600,remaining:600,status:'idle',startedAt:null,pausedAt:null,elapsedBeforePause:0,subject:focusState.subject||'Other',pomodoro:true,break:true};saveFocusState();renderFocusTimer();startFocusTimer();notifyFocus('🍅 Break time','50-minute focus complete. Take a 10-minute break.');}
function renderFocusTimer(){const d=document.getElementById('focus-timer-display');if(!d)return;const rem=focusRemaining();d.textContent=fmtFocus(rem);const pct=focusState.duration?Math.min(100,Math.max(0,(1-rem/focusState.duration)*100)):0;const bar=document.getElementById('focus-progress');if(bar)bar.style.width=pct+'%';const mode=document.getElementById('focus-mode-label');if(mode)mode.textContent=focusState.break?'BREAK':'FOCUS SESSION';const st=document.getElementById('focus-session-status');if(st)st.textContent=focusState.status==='running'?(focusState.break?'Break running ☕':'Studying now 🔥'):focusState.status==='paused'?'Paused ⏸️':'Ready to study';const sb=document.getElementById('focus-start-btn'),pb=document.getElementById('focus-pause-btn'),xb=document.getElementById('focus-stop-btn');if(sb)sb.classList.toggle('hidden',focusState.status==='running');if(pb)pb.classList.toggle('hidden',focusState.status!=='running');if(xb)xb.classList.toggle('hidden',!['running','paused'].includes(focusState.status));}
function recordFocusSession(seconds,subject){
  if(seconds<60)return;
  const st=readFocusStats();
  const now=new Date();
  st.sessions=Array.isArray(st.sessions)?st.sessions:[];
  st.sessions.push({date:localDay(now),seconds:Math.round(seconds),subject:subject||'Other',at:now.toISOString()});
  st.sessions=st.sessions.slice(-2000);
  writeFocusStats(st);
  renderFocusDashboard();
  renderHomeDashboard();
  broadcastFocus();
  const today=st.sessions.filter(x=>x.date===localDay()).reduce((a,x)=>a+Number(x.seconds||0),0);
  const goal=Number(st.goalHours||4)*3600;
  if(today>=goal&&!st.goalNotifiedDate){st.goalNotifiedDate=localDay();writeFocusStats(st);notifyFocus('🎯 Daily goal complete!','Your study goal for today is complete.');toast('Daily goal complete! 🏆');}
}
function saveFocusGoal(){const st=readFocusStats();let h=Math.min(24,Math.max(.25,Number(document.getElementById('focus-goal-hours').value)||4));st.goalHours=h;writeFocusStats(st);renderFocusDashboard();renderHomeDashboard()}
function renderFocusDashboard(){if(!user)return;const st=readFocusStats(),today=localDay(),todaySec=st.sessions.filter(x=>x.date===today).reduce((a,x)=>a+Number(x.seconds||0),0);const goal=Number(st.goalHours||4);const t=document.getElementById('focus-today-time');if(t)t.textContent=fmtHM(todaySec);const ses=document.getElementById('focus-sessions');if(ses)ses.textContent=st.sessions.length;const gh=document.getElementById('focus-goal-hours');if(gh)gh.value=goal;const gl=document.getElementById('focus-goal-label');if(gl)gl.textContent=`${fmtHM(todaySec)} / ${goal}h`;const gb=document.getElementById('focus-goal-bar');if(gb)gb.style.width=Math.min(100,todaySec/(goal*3600)*100)+'%';const streak=document.getElementById('focus-streak');if(streak)streak.textContent=(focusStreak(st.sessions))+' 🔥';renderFocusWeek(st.sessions);renderFocusAchievements(st.sessions);renderFocusTimer();updateNotifyStatus()}
function focusStreak(sessions){const days=new Set((sessions||[]).filter(x=>Number(x.seconds||0)>=60).map(x=>x.date));let d=localDay();let n=0;while(days.has(d)){n++;d=addDays(d,-1)}return n}
function renderFocusWeek(sessions){const box=document.getElementById('focus-week-chart');if(!box)return;const vals=[];for(let i=6;i>=0;i--){const day=addDays(localDay(),-i);const sec=(sessions||[]).filter(x=>x.date===day).reduce((a,x)=>a+Number(x.seconds||0),0);vals.push({day,sec})}const max=Math.max(1,...vals.map(x=>x.sec));const total=vals.reduce((a,x)=>a+x.sec,0);const wt=document.getElementById('focus-week-total');if(wt)wt.textContent=fmtHM(total);box.innerHTML=vals.map(v=>`<div class="h-full flex flex-col justify-end items-center gap-1"><span class="text-[9px] text-slate-500">${v.sec?fmtHM(v.sec).replace(' ',''):''}</span><div class="w-full bg-emerald-500/70 rounded-t-md" style="height:${Math.max(6,v.sec/max*100)}%" title="${v.day}: ${fmtHM(v.sec)}"></div><span class="text-[9px] text-slate-500">${new Date(v.day+'T12:00:00').toLocaleDateString(undefined,{weekday:'short'}).slice(0,3)}</span></div>`).join('')}
function renderFocusAchievements(sessions){const total=(sessions||[]).reduce((a,x)=>a+Number(x.seconds||0),0),streak=focusStreak(sessions);const items=[['🌱','First Session',sessions.length>=1],['⏱️','1 Hour',total>=3600],['🔥','7 Day Streak',streak>=7],['🏆','10 Hours',total>=36000],['💎','25 Sessions',sessions.length>=25],['🚀','25 Hours',total>=90000],['🧠','50 Sessions',sessions.length>=50],['👑','50 Hour Club',total>=180000]];const box=document.getElementById('focus-achievements');if(box)box.innerHTML=items.map(x=>`<div class="rounded-xl p-3 border ${x[2]?'border-fuchsia-500/40 bg-fuchsia-500/10':'border-slate-700 bg-slate-900/60 opacity-50'}"><div class="text-xl">${x[0]}</div><b class="text-xs block mt-1">${x[1]}</b><span class="text-[9px] text-slate-500">${x[2]?'UNLOCKED':'Locked'}</span></div>`).join('')}
function updateNotifyStatus(){const st=document.getElementById('focus-notify-status'),b=document.getElementById('focus-notify-btn');if(!('Notification'in window)){if(st)st.textContent='Not supported';return}if(st)st.textContent=Notification.permission==='granted'?'Enabled ✓':Notification.permission==='denied'?'Blocked — browser settings check karo':'Permission not requested';if(b)b.textContent=Notification.permission==='granted'?'🔔 Enabled':'🔔 Notifications'}
async function requestFocusNotifications(){if(!('Notification'in window))return toast('Is browser mein notifications supported nahi hain.',false);try{const p=await Notification.requestPermission();updateNotifyStatus();toast(p==='granted'?'Notifications enabled 🔔':p==='denied'?'Notifications blocked.':'Permission not granted.',p==='granted')}catch(e){toast('Notification permission nahi mil paayi.',false)}}
function notifyFocus(title,body){if('Notification'in window&&Notification.permission==='granted'){try{new Notification(title,{body,icon:document.querySelector('link[rel="icon"]')?.href||undefined,tag:'rathod-focus'})}catch(e){}}}
function testFocusNotification(){if('Notification'in window&&Notification.permission==='granted')notifyFocus('🔔 RATHOD HUB Test','Notifications sahi se kaam kar rahi hain.');else requestFocusNotifications()}
let focusLastBroadcast=0;
function broadcastFocusThrottled(){if(Date.now()-focusLastBroadcast<4000)return;broadcastFocus()}
async function broadcastFocus(){
  if(!focusChannel||!user||!focusReady)return;
  focusLastBroadcast=Date.now();
  const payload={
    user_id:user.id,
    name:profile?.name||user.email||'Member',
    pfp_url:profile?.pfp_url||null,
    subject:focusState.subject||'Other',
    status:focusState.status,
    break:!!focusState.break,
    started_at:focusState.startedAt||null,
    remaining:Math.ceil(focusRemaining()),
    updated_at:Date.now()
  };
  livePeersMap[user.id]=payload;
  renderLiveFocusUsers();
  try{
    await focusChannel.track(payload);
    await focusChannel.send({type:'broadcast',event:'timer_ping',payload});
  }catch(e){}
}
function renderLiveFocusUsers(){
  if(!focusChannel)return;
  const state=focusChannel.presenceState();
  Object.values(state).flat().forEach(p=>{
    if(p&&p.user_id){
      livePeersMap[p.user_id]={...(livePeersMap[p.user_id]||{}),...p};
    }
  });

  const now=Date.now();
  const people=Object.values(livePeersMap).filter(p=>{
    if(!p||!p.user_id)return false;
    if(p.user_id===user?.id)return p.status==='running';
    return p.status==='running' && (!p.updated_at || (now - p.updated_at < 60000));
  });

  const badge=document.getElementById('focus-live-badge');if(badge)badge.textContent=`● ${people.length} STUDYING`;
  const c=document.getElementById('focus-online-count');if(c)c.textContent=`${people.length} studying`;
  const countEl=document.getElementById('home-live-count');if(countEl)countEl.textContent=`${people.length} students studying`;
  const box=document.getElementById('focus-live-users');
  if(box){
    box.innerHTML=people.length?people.map(p=>{
      const rem=Number.isFinite(Number(p.remaining))?Number(p.remaining):0;
      return `<div data-live-user="${esc(p.name||'Student')}" class="flex justify-between items-center bg-slate-900 rounded-xl border border-slate-700 p-3"><div class="flex items-center gap-2"><div class="w-8 h-8 rounded-full overflow-hidden bg-slate-800 shrink-0">${p.pfp_url?`<img src="${safeUrl(p.pfp_url)}" class="w-full h-full object-cover">`:'👤'}</div><div><b class="text-sm">${esc(p.name||'Member')}</b><div class="text-[10px] text-slate-500 mt-0.5">${esc(p.subject||'Other')} ${p.break?'• Break':'• Focus'}</div></div></div><div class="text-right"><span class="text-emerald-400 text-xs block">● LIVE</span><span class="text-[10px] text-slate-500">${fmtFocus(rem)}</span></div></div>`
    }).join(''):'<div class="text-center py-6 text-xs text-slate-500">Abhi koi active focus session nahi hai.</div>';
  }
  renderRHHomeRail();
}
async function initFocusSystem(){
  if(!user||focusReady)return;
  focusReady=true;
  const saved=readFocusState();
  if(saved){
    focusState={...focusState,...saved};
    if(focusState.status==='running'&&focusRemaining()<=0){completeFocusTimer()}
    else if(focusState.status==='running')startFocusTicker()
  }else saveFocusState();
  const st=readFocusStats();
  if(!st.goalHours)st.goalHours=4;
  writeFocusStats(st);
  if(focusChannel){try{await db.removeChannel(focusChannel)}catch(e){}}
  focusChannel=db.channel('rathod-hub-focus-live',{config:{presence:{key:user.id},broadcast:{self:false}}})
    .on('presence',{event:'sync'},()=>{renderLiveFocusUsers()})
    .on('presence',{event:'join'},()=>{renderLiveFocusUsers()})
    .on('presence',{event:'leave'},({leftPresences})=>{
      (leftPresences||[]).forEach(lp=>{if(lp?.user_id&&lp.user_id!==user.id)delete livePeersMap[lp.user_id]});
      renderLiveFocusUsers();
    })
    .on('broadcast',{event:'timer_ping'},e=>{
      if(!e?.payload||!e.payload.user_id||e.payload.user_id===user.id)return;
      livePeersMap[e.payload.user_id]={...e.payload,updated_at:Date.now()};
      renderLiveFocusUsers();
    })
    .subscribe(async status=>{
      if(status==='SUBSCRIBED'){
        await broadcastFocus();
        renderLiveFocusUsers();
      }
    });

  if(focusHeartbeat)clearInterval(focusHeartbeat);
  focusHeartbeat=setInterval(()=>{if(focusState.status==='running')broadcastFocus();},20000);

  renderFocusDashboard();
  renderHomeDashboard();
  updateNotifyStatus();
}
</script>
</body>
</html>
