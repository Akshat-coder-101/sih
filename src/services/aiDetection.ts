import * as tf from '@tensorflow/tfjs';
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import { Alert, DetectionBox } from '../types';

let modelPromise: Promise<cocoSsd.ObjectDetection> | null = null;

export async function loadCocoSsdModel(): Promise<cocoSsd.ObjectDetection> {
  if (!modelPromise) {
    modelPromise = (async () => {
      await tf.ready();
      return await cocoSsd.load({ base: 'lite_mobilenet_v2' });
    })();
  }
  return modelPromise;
}

export function captureFrameWithBoxes(
  videoEl: HTMLVideoElement,
  boxes: DetectionBox[],
  osdMeta: { camName: string; location: string; geo: string; timestamp: string }
): string | null {
  try {
    const canvas = document.createElement('canvas');
    const vw = videoEl.videoWidth || 1280;
    const vh = videoEl.videoHeight || 720;
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // Draw raw video frame
    ctx.drawImage(videoEl, 0, 0, vw, vh);

    // Vignette / dark gradient overlay for security styling
    const gradTop = ctx.createLinearGradient(0, 0, 0, 70);
    gradTop.addColorStop(0, 'rgba(0,0,0,0.7)');
    gradTop.addColorStop(1, 'transparent');
    ctx.fillStyle = gradTop;
    ctx.fillRect(0, 0, vw, 70);

    const gradBottom = ctx.createLinearGradient(0, vh - 70, 0, vh);
    gradBottom.addColorStop(0, 'transparent');
    gradBottom.addColorStop(1, 'rgba(0,0,0,0.85)');
    ctx.fillStyle = gradBottom;
    ctx.fillRect(0, vh - 70, vw, 70);

    // OSD Header & Footer
    ctx.fillStyle = '#00e5b8';
    ctx.font = 'bold 22px "JetBrains Mono", monospace';
    ctx.fillText(`${osdMeta.camName.toUpperCase()} — EVIDENCE CAPTURE`, 24, 38);

    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.font = '16px "JetBrains Mono", monospace';
    ctx.fillText(`${osdMeta.timestamp}  |  ${osdMeta.geo}`, 24, vh - 24);

    // Virtual Fence line (at 74% height)
    const fenceY = vh * 0.74;
    ctx.strokeStyle = 'rgba(255, 71, 87, 0.85)';
    ctx.lineWidth = 3;
    ctx.setLineDash([12, 6]);
    ctx.beginPath();
    ctx.moveTo(0, fenceY);
    ctx.lineTo(vw, fenceY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Bounding Boxes
    boxes.forEach(b => {
      const bx = (b.left / 100) * vw;
      const by = (b.top / 100) * vh;
      const bw = (b.w / 100) * vw;
      const bh = (b.h / 100) * vh;

      const isThreat = b.watch;
      ctx.strokeStyle = isThreat ? '#ff4757' : '#00e5b8';
      ctx.lineWidth = 3;
      ctx.strokeRect(bx, by, bw, bh);

      // Label Tag Chip
      const tagText = b.label.toUpperCase();
      ctx.font = 'bold 16px "JetBrains Mono", monospace';
      const textWidth = ctx.measureText(tagText).width;
      const chipHeight = 28;
      const chipWidth = textWidth + 18;

      ctx.fillStyle = isThreat ? '#ff4757' : '#00e5b8';
      ctx.fillRect(bx, Math.max(0, by - chipHeight), chipWidth, chipHeight);

      ctx.fillStyle = isThreat ? '#ffffff' : '#000000';
      ctx.fillText(tagText, bx + 9, Math.max(19, by - 8));
    });

    return canvas.toDataURL('image/jpeg', 0.85);
  } catch (err) {
    console.error('Failed to capture frame snapshot:', err);
    return null;
  }
}
