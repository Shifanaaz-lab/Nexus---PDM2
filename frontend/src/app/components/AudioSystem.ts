// Audio system for critical alerts and system events
class AudioSystem {
  private audioContext: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private enabled: boolean = true;

  constructor() {
    if (typeof window !== 'undefined') {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.masterGain = this.audioContext.createGain();
      this.masterGain.gain.value = 0.3;
      this.masterGain.connect(this.audioContext.destination);
    }
  }

  private createOscillator(frequency: number, type: OscillatorType = 'sine'): OscillatorNode | null {
    if (!this.audioContext || !this.masterGain) return null;
    
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();
    
    oscillator.type = type;
    oscillator.frequency.value = frequency;
    
    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    return oscillator;
  }

  // Critical alert sound - urgent beeping
  playCriticalAlert() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.createOscillator(800, 'square');
    const gainNode = this.audioContext.createGain();
    
    if (!oscillator) return;

    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    // Create urgent beeping pattern
    gainNode.gain.setValueAtTime(0, now);
    for (let i = 0; i < 3; i++) {
      gainNode.gain.setValueAtTime(0.4, now + i * 0.3);
      gainNode.gain.setValueAtTime(0, now + i * 0.3 + 0.1);
    }
    
    oscillator.start(now);
    oscillator.stop(now + 1);
  }

  // Warning sound - softer alert
  playWarning() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.createOscillator(600, 'sine');
    const gainNode = this.audioContext.createGain();
    
    if (!oscillator) return;

    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    gainNode.gain.setValueAtTime(0.3, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
    
    oscillator.start(now);
    oscillator.stop(now + 0.5);
  }

  // System event sound - subtle notification
  playSystemEvent() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.createOscillator(1200, 'sine');
    const gainNode = this.audioContext.createGain();
    
    if (!oscillator) return;

    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    gainNode.gain.setValueAtTime(0.2, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
    
    oscillator.frequency.exponentialRampToValueAtTime(800, now + 0.2);
    
    oscillator.start(now);
    oscillator.stop(now + 0.3);
  }

  // Holographic interaction sound
  playHolographicInteraction() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.createOscillator(1500, 'sine');
    const gainNode = this.audioContext.createGain();
    
    if (!oscillator) return;

    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    gainNode.gain.setValueAtTime(0.15, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
    
    oscillator.frequency.exponentialRampToValueAtTime(2000, now + 0.15);
    
    oscillator.start(now);
    oscillator.stop(now + 0.15);
  }

  // Data streaming sound
  playDataStream() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.createOscillator(400, 'sawtooth');
    const gainNode = this.audioContext.createGain();
    
    if (!oscillator) return;

    oscillator.connect(gainNode);
    gainNode.connect(this.masterGain);
    
    gainNode.gain.setValueAtTime(0.1, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
    
    oscillator.start(now);
    oscillator.stop(now + 0.2);
  }

  // Mode switch sound
  playModeSwitch() {
    if (!this.enabled || !this.audioContext || !this.masterGain) return;

    const now = this.audioContext.currentTime;
    
    // Create a chord for mode switch
    const frequencies = [523.25, 659.25, 783.99]; // C, E, G
    
    frequencies.forEach((freq, index) => {
      const oscillator = this.createOscillator(freq, 'sine');
      const gainNode = this.audioContext!.createGain();
      
      if (!oscillator) return;

      oscillator.connect(gainNode);
      gainNode.connect(this.masterGain!);
      
      gainNode.gain.setValueAtTime(0.15, now + index * 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
      
      oscillator.start(now + index * 0.05);
      oscillator.stop(now + 0.5);
    });
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  setVolume(volume: number) {
    if (this.masterGain) {
      this.masterGain.gain.value = Math.max(0, Math.min(1, volume));
    }
  }
}

export const audioSystem = new AudioSystem();
