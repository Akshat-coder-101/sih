let sceneUid = 0;

export function sceneFence(uid: number): string {
  return `<svg viewBox="0 0 1280 720" preserveAspectRatio="xMidYMid slice" class="w-full h-full block">
    <defs>
      <linearGradient id="sky${uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#aebfc9"/><stop offset="55%" stop-color="#d9e4e2"/><stop offset="100%" stop-color="#e9efe6"/>
      </linearGradient>
      <linearGradient id="grnd${uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#8a8f5c"/><stop offset="35%" stop-color="#767a4a"/><stop offset="100%" stop-color="#4b4d30"/>
      </linearGradient>
    </defs>
    <rect width="1280" height="470" fill="url(#sky${uid})"/>
    <path d="M0,430 Q320,395 640,415 T1280,405 L1280,470 L0,470 Z" fill="#93967a" opacity="0.55"/>
    <path d="M0,450 Q400,420 800,440 T1280,432 L1280,470 L0,470 Z" fill="#7d8168" opacity="0.6"/>
    <rect y="460" width="1280" height="260" fill="url(#grnd${uid})"/>
    <g opacity="0.22">${Array.from({length:14},(_,i)=>`<ellipse cx="${(i*97+30)%1280}" cy="${540+((i*53)%160)}" rx="${18+((i*13)%20)}" ry="${5+((i*3)%4)}" fill="#3d3f22"/>`).join('')}</g>
    <g stroke="#5b5142" stroke-width="4">
      ${Array.from({length:11},(_,i)=>{const x=40+i*118;const h=150-Math.abs(i-5)*3;return `<line x1="${x}" y1="${478-h*0.15}" x2="${x-6}" y2="${520}" />`;}).join('')}
    </g>
    <g stroke="#2c2a20" stroke-width="2" opacity="0.85">
      <path d="M20,486 Q640,470 1260,488" fill="none"/>
      <path d="M20,500 Q640,486 1260,502" fill="none"/>
      <path d="M20,514 Q640,500 1260,516" fill="none"/>
    </g>
    <g transform="translate(560,470)">
      <ellipse cx="12" cy="152" rx="34" ry="7" fill="#000" opacity="0.22"/>
      <path d="M8,60 Q2,90 8,118 L4,150 L14,150 L17,120 L23,150 L33,150 L27,116 Q34,86 26,58 Z" fill="#2b2f38"/>
      <circle cx="16" cy="46" r="13" fill="#31363f"/>
    </g>
    <g transform="translate(1080,455)" opacity="0.85">
      <rect x="-3" y="0" width="6" height="70" fill="#4a4536"/>
      <rect x="-22" y="-26" width="44" height="26" fill="#5b5646" stroke="#38352a" stroke-width="1"/>
    </g>
  </svg>`;
}

export function sceneGate(uid: number): string {
  return `<svg viewBox="0 0 1280 720" preserveAspectRatio="xMidYMid slice" class="w-full h-full block">
    <defs>
      <linearGradient id="sky2${uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#b7c7d6" /><stop offset="100%" stop-color="#e7edea"/>
      </linearGradient>
      <linearGradient id="road${uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#5b5f63"/><stop offset="100%" stop-color="#34373b"/>
      </linearGradient>
    </defs>
    <rect width="1280" height="440" fill="url(#sky2${uid})"/>
    <rect y="420" width="1280" height="300" fill="#6b7256"/>
    <path d="M470,420 L810,420 L1010,720 L270,720 Z" fill="url(#road${uid})"/>
    <path d="M636,430 L648,430 L600,720 L560,720 Z" fill="#c9c9a8" opacity="0.75"/>
    <g fill="#3f4340">
      <rect x="210" y="330" width="150" height="92" />
      <path d="M205,330 L360,330 L340,300 L225,300 Z" fill="#54584f"/>
      <rect x="255" y="365" width="34" height="57" fill="#8fd8ff" opacity="0.55"/>
    </g>
    <g transform="translate(560,392)">
      <rect x="-8" y="0" width="16" height="46" fill="#2c2f33"/>
      <g transform="rotate(-7 0 0)">
        <rect x="-6" y="-8" width="330" height="17" fill="#e6e6e6"/>
        ${Array.from({length:11},(_,i)=>`<rect x="${-6+i*30}" y="-8" width="15" height="17" fill="#c1272d"/>`).join('')}
      </g>
    </g>
    <g transform="translate(600,560)">
      <ellipse cx="60" cy="118" rx="92" ry="14" fill="#000" opacity="0.28"/>
      <rect x="6" y="34" width="120" height="56" rx="10" fill="#33465c"/>
      <rect x="20" y="10" width="88" height="38" rx="10" fill="#3d5470"/>
      <rect x="30" y="16" width="30" height="26" fill="#9fd6ee" opacity="0.7"/>
      <rect x="64" y="16" width="30" height="26" fill="#9fd6ee" opacity="0.7"/>
      <circle cx="30" cy="92" r="16" fill="#181a1c"/><circle cx="102" cy="92" r="16" fill="#181a1c"/>
      <ellipse cx="10" cy="52" rx="5" ry="7" fill="#ffe9a8"/><ellipse cx="122" cy="52" rx="5" ry="7" fill="#ffe9a8"/>
    </g>
  </svg>`;
}

export function sceneNight(uid: number): string {
  return `<svg viewBox="0 0 1280 720" preserveAspectRatio="xMidYMid slice" class="w-full h-full block">
    <defs>
      <radialGradient id="ngrad${uid}" cx="50%" cy="42%" r="75%">
        <stop offset="0%" stop-color="#173325"/><stop offset="60%" stop-color="#0a1c14"/><stop offset="100%" stop-color="#040d09"/>
      </radialGradient>
      <radialGradient id="hl${uid}" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#eaffef" stop-opacity="0.95"/><stop offset="45%" stop-color="#9dffb8" stop-opacity="0.45"/><stop offset="100%" stop-color="#9dffb8" stop-opacity="0"/>
      </radialGradient>
      <filter id="grain${uid}"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
    </defs>
    <rect width="1280" height="720" fill="url(#ngrad${uid})"/>
    <path d="M0,470 Q320,430 640,455 T1280,440 L1280,720 L0,720 Z" fill="#0e2a1c" opacity="0.8"/>
    <path d="M300,720 Q420,430 640,420 Q860,430 1000,720 Z" fill="#152f22" opacity="0.85"/>
    <path d="M556,470 L568,470 L470,720 L420,720 Z" fill="#274a35" opacity="0.5"/>
    <g opacity="0.55" fill="#0c2318">
      ${Array.from({length:9},(_,i)=>`<path d="M${60+i*140},460 L${90+i*140},390 L${120+i*140},460 Z"/>`).join('')}
    </g>
    <g transform="translate(660,520)">
      <ellipse cx="0" cy="0" rx="150" ry="90" fill="url(#hl${uid})"/>
      <rect x="-58" y="-14" width="116" height="40" rx="8" fill="#0b1f15"/>
      <circle cx="-40" cy="6" r="10" fill="#eaffef"/><circle cx="40" cy="6" r="10" fill="#eaffef"/>
    </g>
    <g transform="translate(430,470)">
      <ellipse cx="0" cy="70" rx="46" ry="60" fill="url(#hl${uid})" opacity="0.7"/>
      <path d="M4,10 Q-2,40 4,68 L0,100 L10,100 L13,70 L19,100 L29,100 L23,66 Q30,36 22,8 Z" fill="#bdf5cf" opacity="0.85"/>
      <circle cx="12" cy="-2" r="10" fill="#d6ffe4" opacity="0.9"/>
    </g>
    <rect width="1280" height="720" filter="url(#grain${uid})" opacity="0.06"/>
  </svg>`;
}

export function getSceneSvg(scene: 'fence' | 'gate' | 'night'): string {
  sceneUid++;
  if (scene === 'gate') return sceneGate(sceneUid);
  if (scene === 'night') return sceneNight(sceneUid);
  return sceneFence(sceneUid);
}
