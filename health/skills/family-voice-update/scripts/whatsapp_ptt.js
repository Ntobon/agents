// Nota de voz nativa en WhatsApp Web a partir de un archivo de audio.
// Se ejecutan con javascript_tool en la pestaña de WhatsApp Web, con el chat correcto ya abierto.

// ── Bloque 1: input propio para subir el audio (luego: find "claude-audio-input" + file_upload) ──
let i = document.getElementById('claude-audio');
if (!i) {
  i = document.createElement('input');
  i.type = 'file';
  i.id = 'claude-audio';
  i.setAttribute('aria-label', 'claude-audio-input');
  i.style.cssText = 'position:fixed;top:0;left:0;width:10px;height:10px;opacity:0.01;z-index:99999';
  document.body.appendChild(i);
}
document.querySelector('#main header')?.innerText.slice(0, 40);

// ── Bloque 2: micrófono falso + envío automático al terminar (devuelve la duración) ──
const f = document.getElementById('claude-audio').files[0];
const ctx = new AudioContext({ sampleRate: 48000 });
const buf = await ctx.decodeAudioData(await f.arrayBuffer());
const v = (window._voice = { ctx, buf, started: false, ended: false, sent: false });
window._origGUM = window._origGUM || navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
navigator.mediaDevices.getUserMedia = async (c) => {
  if (c && c.audio) {
    await ctx.resume();
    const dest = ctx.createMediaStreamDestination();
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(dest);
    setTimeout(() => { src.start(); v.started = Date.now(); }, 400);
    src.onended = () => {
      v.ended = Date.now();
      setTimeout(() => {
        const b = document.querySelector('footer button[aria-label="Send"]');
        if (b) { b.click(); v.sent = true; }
      }, 700);
    };
    return dest.stream;
  }
  return window._origGUM(c);
};
'listo, duración ' + buf.duration.toFixed(1) + ' s';

// ── Comprobación (después de pulsar "Voice message" y esperar la duración) ──
// JSON.stringify({started: !!window._voice.started, ended: !!window._voice.ended, sent: window._voice.sent})
