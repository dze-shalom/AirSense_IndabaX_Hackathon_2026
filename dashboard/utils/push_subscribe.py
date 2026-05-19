import os
import streamlit as st


def render_push_subscribe_ui(api_base_url: str = ""):
    vapid_key = os.getenv("VAPID_PUBLIC_KEY", "")
    if not vapid_key:
        st.markdown(
            '<div style="font-size:.58rem;color:#8892b0;padding:.3rem 0;">'
            '⚙ Push alerts: set <code>VAPID_PUBLIC_KEY</code> env var to enable.'
            '</div>', unsafe_allow_html=True
        )
        return

    st.markdown(f"""<div id="as-push-ui">
<button id="as-push-btn" onclick="asSubscribePush()" style="
  width:100%;border-radius:6px;padding:.35rem .7rem;font-size:.72rem;font-weight:600;
  cursor:pointer;border:1px solid rgba(100,255,218,0.4);
  background:rgba(100,255,218,0.08);color:#64ffda;font-family:'Open Sans',sans-serif;">
  Get air quality alerts
</button>
<div id="as-push-status" style="font-size:.58rem;color:#8892b0;margin-top:.2rem;"></div>
</div>
<script>
function urlBase64ToUint8Array(base64String){{
  var padding='='.repeat((4-base64String.length%4)%4);
  var base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');
  var raw=atob(base64);
  var arr=new Uint8Array(raw.length);
  for(var i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
  return arr;
}}
async function asSubscribePush(){{
  var status=document.getElementById('as-push-status');
  var btn=document.getElementById('as-push-btn');
  if(!('serviceWorker' in navigator)||!('PushManager' in window)){{
    status.textContent='Push not supported in this browser.';return;
  }}
  try{{
    var perm=await Notification.requestPermission();
    if(perm!=='granted'){{status.textContent='Permission denied.';return;}}
    var reg=await navigator.serviceWorker.ready;
    var sub=await reg.pushManager.subscribe({{
      userVisibleOnly:true,
      applicationServerKey:urlBase64ToUint8Array('{vapid_key}')
    }});
    var resp=await fetch('{api_base_url}/push/subscribe',{{
      method:'POST',headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify(sub.toJSON())
    }});
    if(resp.ok){{
      status.textContent='✓ Alerts enabled for this device.';
      btn.textContent='Alerts enabled';btn.disabled=true;
      btn.style.opacity='0.6';
    }} else {{
      status.textContent='Failed to register. Try again.';
    }}
  }}catch(e){{status.textContent='Error: '+e.message;}}
}}
</script>""", unsafe_allow_html=True)
