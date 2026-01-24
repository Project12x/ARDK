import './wdyr';
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { setupXStateInspector } from './lib/machines/inspector';
import './index.css'

if (import.meta.env.DEV) {
  setupXStateInspector();
}
import App from './App.tsx'

// import { initVaultMiddleware } from './lib/vault-middleware';

console.log("BOOT CHECK: STARTING");

// const root = document.getElementById('root');
// if (root) {
//   root.innerHTML = '<h1 style="color:red; font-size: 50px;">DOM HACK SUCCESS</h1>';
//   console.log("BOOT CHECK: DOM UPDATED");
// } else {
//   console.error("BOOT CHECK: ROOT MISSING");
// }

// initVaultMiddleware();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    {/* <div style={{ color: 'cyan', fontSize: 30, padding: 20 }}>REACT ONLINE</div> */}
  </StrictMode>,
)
