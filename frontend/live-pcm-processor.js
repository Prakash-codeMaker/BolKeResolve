/*
 * Capture mono Float32 microphone input and send fixed 512-sample frames.
 * The main thread converts each frame to signed PCM16 little-endian.
 * Keep the AudioContext's real sample rate: Gnani accepts 16/44.1/48 kHz
 * and resamples 44.1/48 kHz streams server-side. Relabelling decimated audio
 * is avoided so the provider always receives the rate declared at handshake.
 */
class BolkePcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(512);
    this.offset = 0;
  }
  process(inputs) {
    const channels = inputs[0];
    if (!channels || !channels.length) return true;
    const input = channels[0];
    for (let i = 0; i < input.length; i += 1) {
      this.buffer[this.offset++] = input[i];
      if (this.offset === 512) {
        const frame = this.buffer;
        this.port.postMessage(frame, [frame.buffer]);
        this.buffer = new Float32Array(512);
        this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor('bolke-pcm-processor', BolkePcmProcessor);
