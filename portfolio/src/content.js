export const photos = [
  {
    "image": "./assets/waterfront.webp",
    "title": "img_0098.jpg",
    "alt": "ビルの向こうに沈む太陽と、水面に伸びる光",
    "width": 1550,
    "height": 1033
  },
  {
    "image": "./assets/ferris-wheel.webp",
    "title": "img_9936.jpg",
    "alt": "夕暮れの空に浮かぶ観覧車のゴンドラ",
    "width": 1033,
    "height": 1550
  },
  {
    "image": "./assets/fireworks.webp",
    "title": "img_3395.jpg",
    "alt": "橋の上空に広がり、水面に反射する赤と白の花火",
    "width": 1550,
    "height": 1163
  },
  {
    "image": "./assets/img_3578.webp",
    "title": "img_3578.jpg",
    "alt": "赤と青の大きな花火を下から見上げる",
    "width": 1000,
    "height": 1500
  },
  {
    "image": "./assets/golden-fireworks.webp",
    "title": "img_3427.jpg",
    "alt": "夜の橋を背景に大きく開く金色の花火",
    "width": 1550,
    "height": 1240
  },
  {
    "image": "./assets/fireworks-reflection.webp",
    "title": "img_3417.jpg",
    "alt": "夜空に開く緑と赤の花火と橋の照明",
    "width": 1162,
    "height": 1550
  },
  {
    "image": "./assets/img_4366.webp",
    "title": "img_4366.jpg",
    "alt": "夕暮れの光が残る街並みと高層ビル",
    "width": 1500,
    "height": 1000
  }
];

export const profile = {
  heading: 'About me.',
  bio: 'I build for the web, take photos, and write about technology at Tecirc. I’m interested in interfaces that adapt to what people need in the moment.',
  interests: ['Technology','Design','UI/UX','Human–Computer Interaction','Artificial Intelligence','Photography','Web Development'],
  links: [
    {label:'Tecirc',url:'https://4k29.github.io/tecirc/'},
    {label:'Twitter',url:'https://x.com/p_horeer'},
    {label:'Instagram',url:'https://www.instagram.com/__4k29/'},
  ],
};

export const projects = [
  {
    title:'Tecirc',
    category:'Web / Writing',
    description:'An independent site about technology, design, and the experience of using both.',
    image:'./assets/tecirc.webp',
    alt:'Tecirc logo',
    url:'https://4k29.github.io/tecirc/',
    linkLabel:'Visit Tecirc',
  },
];

export const articles = [
  {
    "title": "MacBookにタッチ操作は本当にいらないのか",
    "image": "./assets/note-touch-macbookpro.webp",
    "alt": "MacBookにタッチ操作は本当にいらないのか",
    "url": "https://4k29.github.io/tecirc/notes/touch-MacBookPro/",
    "date": "2026.10.30"
  },
  {
    "title": "AIの先にある未来の話をしよう",
    "image": "./assets/note-ai-future.webp",
    "alt": "AIの先にある未来の話をしよう",
    "url": "https://4k29.github.io/tecirc/notes/ai-future/",
    "date": "2026.09.28"
  },
  {
    "title": "生成できる時代に、非生成コンテンツの価値を考える",
    "image": "./assets/note-ai-and-experience.webp",
    "alt": "生成できる時代に、非生成コンテンツの価値を考える",
    "url": "https://4k29.github.io/tecirc/notes/ai-and-experience/",
    "date": "2026.09.22"
  },
  {
    "title": "iPhone DuoのOSは、「iOS」と呼ぶべきなのか",
    "image": "./assets/note-iphone-duo-os.webp",
    "alt": "iPhone DuoのOSは、「iOS」と呼ぶべきなのか",
    "url": "https://4k29.github.io/tecirc/notes/iphone-duo-os/",
    "date": "2026.09.10"
  },
  {
    "title": "Apple WatchはSiri AIの中核になり得ると思った話",
    "image": "./assets/note-applewatch-siriai.webp",
    "alt": "Apple Watchは、Siri AIの中核になり得る",
    "url": "https://4k29.github.io/tecirc/notes/AppleWatch-SiriAI/",
    "date": "2026.09.10"
  },
  {
    "title": "Nothing Headphone (1) 4ヶ月使用レビュー",
    "image": "./assets/note-nothing-headphone-1.webp",
    "alt": "Nothing Headphone (1)",
    "url": "https://4k29.github.io/tecirc/notes/Nothing-Headphone-1/",
    "date": "2026.07.22"
  },
  {
    "title": "Instantsに思うこと",
    "image": "./assets/note-instants.webp",
    "alt": "Instantsに思うこと",
    "url": "https://4k29.github.io/tecirc/notes/Instants/",
    "date": "2026.05.21"
  },
  {
    "title": "iPhone eシリーズの意義を考える",
    "image": "./assets/note-iphone-e.webp",
    "alt": "iPhone eシリーズの意義を考える",
    "url": "https://4k29.github.io/tecirc/notes/iPhone-e/",
    "date": "2026.03.15"
  }
].sort((a,b)=>(b.date ?? '').localeCompare(a.date ?? ''));

