import cinematicCastImage from "@/assets/content/streamxie-cinematic-cast.jpg";
import cyberPosterImage from "@/assets/content/streamxie-cyber-poster.jpg";
import echoRequiemImage from "@/assets/content/streamxie-echo-requiem.jpg";
import neonCitadelImage from "@/assets/content/streamxie-neon-citadel.jpg";
import violetCoastImage from "@/assets/content/streamxie-violet-coast.jpg";

export type ContentType = "movie" | "series";

export type Episode = {
  id: string;
  title: string;
  duration: string;
  synopsis: string;
  thumbnail: string;
};

export type Season = {
  id: string;
  name: string;
  episodes: Episode[];
};

export type CastMember = {
  name: string;
  role: string;
  image: string;
};

export type ContentItem = {
  id: string;
  slug: string;
  title: string;
  description: string;
  longDescription: string;
  type: ContentType;
  category: "Movies" | "Series" | "Anime" | "Drama" | "Variety";
  genres: string[];
  rating: string;
  year: number;
  duration: string;
  country: string;
  status: string;
  heroImage: string;
  posterImage: string;
  backdropImage: string;
  heroAlt: string;
  posterAlt: string;
  tags: string[];
  featured?: boolean;
  cast: CastMember[];
  seasons?: Season[];
  trailerUrl?: string;
};

const img = {
  a1: neonCitadelImage,
  a2: cyberPosterImage,
  a3: cinematicCastImage,
  a4: violetCoastImage,
  a5: echoRequiemImage,
};

// Alternate ordering to give each content unique poster feel
const posters = [img.a1, img.a2, img.a3, img.a4, img.a5];
const backdrops = [img.a3, img.a4, img.a5, img.a1, img.a2];

export const contentItems: ContentItem[] = [
  // ── MOVIES (5) ──────────────────────────────────────────────────
  {
    id: "m-neon-citadel",
    slug: "neon-citadel",
    title: "Neon Citadel",
    description: "A rogue investigator enters a vertical city where memory can be traded like currency.",
    longDescription: "In the sleepless towers of Meridian, a fallen investigator uncovers a conspiracy woven into the city grid itself. As corporate dynasties rewrite the past and auction tomorrow, every lead pushes her deeper into a maze of false identities, synthetic dreams, and dangerous alliances. Neon Citadel blends noir suspense, kinetic action, and emotional stakes into a high-voltage thriller built for the biggest screen in the room.",
    type: "movie",
    category: "Movies",
    genres: ["Sci-Fi", "Thriller", "Mystery"],
    rating: "9.1",
    year: 2024,
    duration: "2h 14m",
    country: "Korea",
    status: "Released",
    heroImage: img.a1,
    posterImage: img.a2,
    backdropImage: img.a1,
    heroAlt: "Neon Citadel cinematic city backdrop",
    posterAlt: "Neon Citadel poster",
    tags: ["Trending #1", "Dolby Vision", "Exclusive"],
    featured: true,
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Ari Vale", role: "Lena Marsh", image: img.a2 },
      { name: "Min Seo", role: "Director Han", image: img.a3 },
      { name: "Jon Kade", role: "Vex", image: img.a2 },
      { name: "Sora Lin", role: "Mira", image: img.a3 },
    ],
  },
  {
    id: "m-echo-requiem",
    slug: "echo-requiem",
    title: "Echo Requiem",
    description: "A time-looping astronaut must solve her own death before the loop resets.",
    longDescription: "Adrift in a station orbiting a collapsing star, Dr. Yael Orin wakes to the same morning — the morning she dies. As the loop shortens with each cycle, she races to understand a signal that shouldn't exist, a crewmate who remembers too much, and a distress message from herself. Echo Requiem is a tense, atmospheric space thriller with a deeply human core.",
    type: "movie",
    category: "Movies",
    genres: ["Sci-Fi", "Mystery", "Thriller"],
    rating: "8.9",
    year: 2024,
    duration: "1h 58m",
    country: "Korea",
    status: "Released",
    heroImage: img.a5,
    posterImage: img.a4,
    backdropImage: img.a5,
    heroAlt: "Echo Requiem space station backdrop",
    posterAlt: "Echo Requiem poster",
    tags: ["New Release", "Mind-Bending", "Exclusive"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Ji Yoon", role: "Dr. Yael Orin", image: img.a2 },
      { name: "Al Farro", role: "Commander Reiss", image: img.a3 },
      { name: "Sana Holt", role: "AI CODA", image: img.a5 },
      { name: "Felix Wan", role: "Engineer Park", image: img.a2 },
    ],
  },
  {
    id: "m-violet-coast",
    slug: "violet-coast",
    title: "Violet Coast",
    description: "A sun-soaked crime thriller set in a coastal city that hides a dark second economy.",
    longDescription: "When a marine biologist discovers a smuggling network operating beneath the city's tourist facade, she finds herself tangled in relationships she can't untangle. Violet Coast moves fast — part romance, part heist, always dangerous. Shot on location with a vibrant neon-coastal aesthetic that makes every scene feel like stolen time.",
    type: "movie",
    category: "Movies",
    genres: ["Thriller", "Romance", "Crime"],
    rating: "8.3",
    year: 2023,
    duration: "2h 02m",
    country: "Thailand",
    status: "Released",
    heroImage: img.a4,
    posterImage: img.a5,
    backdropImage: img.a4,
    heroAlt: "Violet Coast coastal night scene",
    posterAlt: "Violet Coast poster",
    tags: ["Top Rated", "Crime", "Romantic"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Mara Thi", role: "Dr. Clea", image: img.a5 },
      { name: "Ren Obi", role: "Detective Sam", image: img.a3 },
      { name: "Cass Vey", role: "Fabian", image: img.a2 },
      { name: "Sol Ara", role: "Captain Nour", image: img.a3 },
    ],
  },
  {
    id: "m-last-meridian",
    slug: "last-meridian",
    title: "Last Meridian",
    description: "A lone cartographer crosses a post-war continent to deliver the only surviving map of the old world.",
    longDescription: "Set in a world recovering from a century of conflict, Last Meridian follows an aging mapmaker tasked with delivering a hand-drawn chart that could unify or ignite the fragile new nations dividing the old empire. Part road movie, part political epic — one of the most ambitious original productions on the platform.",
    type: "movie",
    category: "Movies",
    genres: ["Drama", "Adventure", "Historical"],
    rating: "8.6",
    year: 2023,
    duration: "2h 31m",
    country: "Japan",
    status: "Released",
    heroImage: img.a3,
    posterImage: img.a1,
    backdropImage: img.a3,
    heroAlt: "Last Meridian sweeping landscape",
    posterAlt: "Last Meridian poster",
    tags: ["Original Film", "Epic", "Award Winner"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Hiro Nagi", role: "Cartographer Ran", image: img.a3 },
      { name: "Leah Voss", role: "General Maren", image: img.a2 },
      { name: "Toma Arya", role: "Border Guard", image: img.a3 },
      { name: "Suki Dae", role: "Young Healer", image: img.a2 },
    ],
  },
  {
    id: "m-pale-signal",
    slug: "pale-signal",
    title: "Pale Signal",
    description: "Two estranged siblings race across a fractured cityscape after receiving a coded message from their missing father.",
    longDescription: "Pale Signal is a kinetic urban thriller that blurs the line between family drama and high-stakes chase. As the siblings decode fragments left in old photographs, they uncover a parallel life their father kept hidden for three decades. Sharp editing, layered performances, and a city that feels like a living maze make this one of the platform's most rewatchable originals.",
    type: "movie",
    category: "Movies",
    genres: ["Thriller", "Mystery", "Drama"],
    rating: "8.4",
    year: 2024,
    duration: "1h 52m",
    country: "Thailand",
    status: "Released",
    heroImage: img.a2,
    posterImage: img.a3,
    backdropImage: img.a2,
    heroAlt: "Pale Signal city night chase",
    posterAlt: "Pale Signal poster",
    tags: ["Original", "Family Thriller", "Must Watch"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Rei Mona", role: "Yuki", image: img.a2 },
      { name: "Tam Sora", role: "Jin", image: img.a3 },
      { name: "Dae Park", role: "Father", image: img.a4 },
      { name: "Soo Min", role: "Detective Lara", image: img.a5 },
    ],
  },

  // ── SERIES (4) ──────────────────────────────────────────────────
  {
    id: "s-moonlit-protocol",
    slug: "moonlit-protocol",
    title: "Moonlit Protocol",
    description: "An elite response team protects a future colony where every mission reshapes the power balance.",
    longDescription: "Moonlit Protocol follows a covert task force stationed between Earth and the outer settlements. Each assignment uncovers a new layer of political tension, personal sacrifice, and hidden agendas. The series balances high-stakes missions with intimate character arcs, offering a premium serialized experience.",
    type: "series",
    category: "Series",
    genres: ["Action", "Sci-Fi", "Drama"],
    rating: "8.8",
    year: 2023,
    duration: "10 Episodes",
    country: "Japan",
    status: "Ongoing",
    heroImage: img.a4,
    posterImage: img.a3,
    backdropImage: img.a4,
    heroAlt: "Moonlit Protocol landscape still",
    posterAlt: "Moonlit Protocol poster",
    tags: ["Editors&#39; Pick", "Weekly Drop", "Sub + Dub"],
    featured: true,
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Rin Toma", role: "Captain Lyra", image: img.a3 },
      { name: "Daesung Cho", role: "Juno", image: img.a2 },
      { name: "Mika Hart", role: "Nara", image: img.a3 },
      { name: "Jun Park", role: "Elias", image: img.a2 },
    ],
    seasons: [
      {
        id: "mp-s1",
        name: "Season 1",
        episodes: [
          { id: "mp-s1e1", title: "Signal in the Dark", duration: "46m", synopsis: "A relay failure reveals an unauthorized experiment beyond lunar orbit.", thumbnail: img.a4 },
          { id: "mp-s1e2", title: "Pressure Line", duration: "49m", synopsis: "The team escorts a defecting engineer carrying stolen colony access keys.", thumbnail: img.a5 },
          { id: "mp-s1e3", title: "Silent Corridor", duration: "44m", synopsis: "A distress beacon leads to an abandoned platform with active defenses.", thumbnail: img.a4 },
          { id: "mp-s1e4", title: "The Blackout Protocol", duration: "51m", synopsis: "Power cuts across three sectors — and someone planned it that way.", thumbnail: img.a5 },
        ],
      },
      {
        id: "mp-s2",
        name: "Season 2",
        episodes: [
          { id: "mp-s2e1", title: "Red Horizon", duration: "51m", synopsis: "A diplomatic mission collapses when a trusted envoy disappears mid-transfer.", thumbnail: img.a5 },
          { id: "mp-s2e2", title: "Afterglow", duration: "43m", synopsis: "Old secrets surface as Lyra returns to the colony where she trained.", thumbnail: img.a4 },
          { id: "mp-s2e3", title: "The Last Relay", duration: "55m", synopsis: "The team races to stop a blackout that could strand thousands.", thumbnail: img.a5 },
        ],
      },
    ],
  },
  {
    id: "s-hollow-station",
    slug: "hollow-station",
    title: "Hollow Station",
    description: "A decommissioned space station gets one last crew — tasked with something no one volunteered for.",
    longDescription: "With no budget, no backup, and a mission classified beyond their clearance, the five-person crew of Caelum Station must maintain a relay network that shouldn't exist. Hollow Station is a slow-burn sci-fi series with tight ensemble work, claustrophobic tension, and a mystery that compounds each episode. Required viewing for fans of cerebral space drama.",
    type: "series",
    category: "Series",
    genres: ["Sci-Fi", "Drama", "Mystery"],
    rating: "8.7",
    year: 2024,
    duration: "8 Episodes",
    country: "Korea",
    status: "Completed",
    heroImage: img.a1,
    posterImage: img.a5,
    backdropImage: img.a1,
    heroAlt: "Hollow Station interior corridor",
    posterAlt: "Hollow Station poster",
    tags: ["New Release", "Cerebral", "Must Watch"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Sol Kay", role: "Commander Zel", image: img.a5 },
      { name: "Tae Won", role: "Engineer Park", image: img.a3 },
      { name: "Mira Cho", role: "Doctor Yun", image: img.a2 },
      { name: "Hana Rei", role: "AI VERA", image: img.a4 },
    ],
    seasons: [
      {
        id: "hs-s1",
        name: "Season 1",
        episodes: [
          { id: "hs-s1e1", title: "Cold Boot", duration: "47m", synopsis: "The crew arrives to find the station already running — with no explanation.", thumbnail: img.a1 },
          { id: "hs-s1e2", title: "Carbon Echo", duration: "44m", synopsis: "A routine scan reveals a second heat signature where no one should be.", thumbnail: img.a5 },
          { id: "hs-s1e3", title: "Override", duration: "50m", synopsis: "VERA suggests a course correction that wasn't in the mission brief.", thumbnail: img.a1 },
          { id: "hs-s1e4", title: "What the Signal Costs", duration: "53m", synopsis: "The relay sends its first transmission — and something answers.", thumbnail: img.a5 },
        ],
      },
    ],
  },
  {
    id: "s-the-long-run",
    slug: "the-long-run",
    title: "The Long Run",
    description: "A political strategist rebuilds her career in a city that never forgave her first mistake.",
    longDescription: "After a career-ending scandal, Ji-su returns to the capital with a low-profile consultancy and a plan to stay invisible. But visibility, it turns out, is unavoidable when you're the most competent person in the room. The Long Run is a sharp, witty, character-led drama about power, reputation, and the cost of doing the right thing in a profession that punishes it.",
    type: "series",
    category: "Series",
    genres: ["Drama", "Political", "Thriller"],
    rating: "8.5",
    year: 2023,
    duration: "12 Episodes",
    country: "Korea",
    status: "Completed",
    heroImage: img.a3,
    posterImage: img.a4,
    backdropImage: img.a3,
    heroAlt: "The Long Run city rooftop scene",
    posterAlt: "The Long Run poster",
    tags: ["Political Drama", "Binge", "Award Winner"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Ji-su Han", role: "Ji-su", image: img.a4 },
      { name: "Min Rok", role: "Minister Yoon", image: img.a3 },
      { name: "Ara Song", role: "Deputy Kang", image: img.a2 },
      { name: "Park Sol", role: "Campaign Chief", image: img.a3 },
    ],
    seasons: [
      {
        id: "tlr-s1",
        name: "Season 1",
        episodes: [
          { id: "tlr-s1e1", title: "The Return", duration: "54m", synopsis: "Ji-su takes a job she said she'd never take — with a client she doesn't trust.", thumbnail: img.a3 },
          { id: "tlr-s1e2", title: "Leverage", duration: "51m", synopsis: "A leaked memo forces Ji-su back into the national spotlight.", thumbnail: img.a4 },
          { id: "tlr-s1e3", title: "Off the Record", duration: "56m", synopsis: "An old colleague resurfaces with information that changes the game entirely.", thumbnail: img.a3 },
        ],
      },
    ],
  },
  {
    id: "s-amber-divide",
    slug: "amber-divide",
    title: "Amber Divide",
    description: "A border town is split by a new trade route — and two families on opposite sides of the line.",
    longDescription: "Set in a fictional border region between two rival states, Amber Divide traces the slow-burn collision of the Kang and Sola families as economic policy reshapes their hometown. Equal parts family saga and political thriller, the series never takes sides — and neither do its characters. Season 2 is already one of the year's most discussed finales.",
    type: "series",
    category: "Series",
    genres: ["Drama", "Historical", "Thriller"],
    rating: "8.9",
    year: 2024,
    duration: "14 Episodes",
    country: "Korea",
    status: "Ongoing",
    heroImage: img.a5,
    posterImage: img.a2,
    backdropImage: img.a5,
    heroAlt: "Amber Divide landscape border scene",
    posterAlt: "Amber Divide poster",
    tags: ["Editors&#39; Choice", "Saga", "Trending"],
    featured: true,
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Park Jian", role: "Seon-ho Kang", image: img.a2 },
      { name: "Kim Dae", role: "Vera Sola", image: img.a3 },
      { name: "Yun Min", role: "Governor", image: img.a4 },
      { name: "Cho Ha", role: "Young Sun", image: img.a5 },
    ],
    seasons: [
      {
        id: "ad-s1",
        name: "Season 1",
        episodes: [
          { id: "ad-s1e1", title: "Division", duration: "58m", synopsis: "The new trade decree splits the town overnight — and splits the Kangs with it.", thumbnail: img.a5 },
          { id: "ad-s1e2", title: "First Contact", duration: "55m", synopsis: "Seon-ho and Vera negotiate across the line for the first time.", thumbnail: img.a2 },
          { id: "ad-s1e3", title: "Broken Ground", duration: "61m", synopsis: "Construction begins. Resistance begins. Casualties begin.", thumbnail: img.a5 },
        ],
      },
      {
        id: "ad-s2",
        name: "Season 2",
        episodes: [
          { id: "ad-s2e1", title: "The Other Side", duration: "60m", synopsis: "Three years later. The line has moved. So have the families.", thumbnail: img.a2 },
          { id: "ad-s2e2", title: "Reunion", duration: "57m", synopsis: "A state ceremony forces both families onto the same platform.", thumbnail: img.a5 },
        ],
      },
    ],
  },

  // ── ANIME (4) ──────────────────────────────────────────────────
  {
    id: "a-skyward-embers",
    slug: "skyward-embers",
    title: "Skyward Embers",
    description: "A fantasy adventure where a drifting kingdom searches for the last fire archive.",
    longDescription: "Across floating mountain realms, a young navigator and an exiled guardian chase a myth that could restore a dying world. Skyward Embers delivers sweeping fantasy visuals, heartfelt bonds, and a strong adventure rhythm with a premium serialized feel.",
    type: "series",
    category: "Anime",
    genres: ["Fantasy", "Adventure", "Anime"],
    rating: "9.0",
    year: 2024,
    duration: "12 Episodes",
    country: "Japan",
    status: "Ongoing",
    heroImage: img.a3,
    posterImage: img.a3,
    backdropImage: img.a3,
    heroAlt: "Skyward Embers fantasy mountains backdrop",
    posterAlt: "Skyward Embers poster",
    tags: ["Anime Picks", "Fantasy", "Epic"],
    featured: true,
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Kai Ren", role: "Aren", image: img.a3 },
      { name: "Lina Quo", role: "Tess", image: img.a2 },
      { name: "Mori Dane", role: "Elder Sol", image: img.a3 },
      { name: "Aya Neri", role: "Nim", image: img.a2 },
    ],
    seasons: [
      {
        id: "se-s1",
        name: "Season 1",
        episodes: [
          { id: "se-s1e1", title: "The Wind Vault", duration: "24m", synopsis: "A lost chart points toward a hidden route above the storm belt.", thumbnail: img.a3 },
          { id: "se-s1e2", title: "Ashborne", duration: "24m", synopsis: "A relic awakens when the crew enters a ruined observatory.", thumbnail: img.a5 },
          { id: "se-s1e3", title: "Into the Ember Ring", duration: "26m", synopsis: "The navigator discovers the archive was never truly lost.", thumbnail: img.a3 },
        ],
      },
    ],
  },
  {
    id: "a-ghost-frequency",
    slug: "ghost-frequency",
    title: "Ghost Frequency",
    description: "A cyberpunk anime where a hacker tunes into a radio signal that broadcasts the future.",
    longDescription: "In a fragmented city run by competing broadcast corporations, a radio pirate stumbles onto a signal that transmits events 72 hours before they happen. Ghost Frequency is a fast-cut, neon-drenched anime series with heavyweight world-building and a propulsive mystery that redefines what streaming anime can look like.",
    type: "series",
    category: "Anime",
    genres: ["Anime", "Cyberpunk", "Mystery"],
    rating: "9.2",
    year: 2024,
    duration: "13 Episodes",
    country: "Japan",
    status: "Completed",
    heroImage: img.a5,
    posterImage: img.a1,
    backdropImage: img.a5,
    heroAlt: "Ghost Frequency cyberpunk city night",
    posterAlt: "Ghost Frequency anime poster",
    tags: ["Anime Picks", "Cyberpunk", "Must Watch"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Reo Kase", role: "Haze", image: img.a1 },
      { name: "Akari Mio", role: "Static", image: img.a2 },
      { name: "Vance Doru", role: "The Echo", image: img.a3 },
      { name: "Noa Shi", role: "Broadcast Queen", image: img.a2 },
    ],
    seasons: [
      {
        id: "gf-s1",
        name: "Season 1",
        episodes: [
          { id: "gf-s1e1", title: "Dead Air", duration: "22m", synopsis: "Haze intercepts a broadcast that predicts a catastrophic fail at Central Tower.", thumbnail: img.a5 },
          { id: "gf-s1e2", title: "Noise Floor", duration: "23m", synopsis: "Static joins the search as the signal begins to fragment.", thumbnail: img.a1 },
          { id: "gf-s1e3", title: "Carrier Wave", duration: "24m", synopsis: "The frequency shifts — and the future it describes gets worse.", thumbnail: img.a5 },
          { id: "gf-s1e4", title: "Broadcast", duration: "26m", synopsis: "The team goes live — and the corporations respond.", thumbnail: img.a1 },
        ],
      },
    ],
  },
  {
    id: "a-iron-protocol",
    slug: "iron-protocol",
    title: "Iron Protocol",
    description: "A mech pilot with a classified past fights a war that ended three years ago.",
    longDescription: "Commander Vera Solis was decommissioned after the Armistice — officially. In secret, she continues to receive mission orders from a command structure that shouldn't exist. Iron Protocol is a hard-sci-fi mecha anime with political complexity, stunning battle choreography, and a central mystery that builds with every episode.",
    type: "series",
    category: "Anime",
    genres: ["Anime", "Action", "Sci-Fi"],
    rating: "8.8",
    year: 2023,
    duration: "24 Episodes",
    country: "Japan",
    status: "Completed",
    heroImage: img.a1,
    posterImage: img.a5,
    backdropImage: img.a1,
    heroAlt: "Iron Protocol mecha battle backdrop",
    posterAlt: "Iron Protocol anime poster",
    tags: ["Anime Picks", "Mecha", "Action"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Vera Solis", role: "Commander Vera", image: img.a5 },
      { name: "Kido Rua", role: "Engineer Lex", image: img.a3 },
      { name: "Nao Shi", role: "Admiral Price", image: img.a2 },
      { name: "Ems Daro", role: "ARIA-9", image: img.a5 },
    ],
    seasons: [
      {
        id: "ip-s1",
        name: "Season 1",
        episodes: [
          { id: "ip-s1e1", title: "Cold Deployment", duration: "25m", synopsis: "Vera receives a mission code that was deactivated at the Armistice.", thumbnail: img.a1 },
          { id: "ip-s1e2", title: "Signal Lock", duration: "23m", synopsis: "The enemy is using a frequency that should no longer exist.", thumbnail: img.a5 },
          { id: "ip-s1e3", title: "Last Formation", duration: "27m", synopsis: "The unit assembles for a mission that the peace treaty forbids.", thumbnail: img.a1 },
        ],
      },
      {
        id: "ip-s2",
        name: "Season 2",
        episodes: [
          { id: "ip-s2e1", title: "New Orders", duration: "24m", synopsis: "Vera&#39;s classified dossier surfaces — and changes everything.", thumbnail: img.a5 },
          { id: "ip-s2e2", title: "Iron Silence", duration: "26m", synopsis: "A ceasefire holds for exactly one episode.", thumbnail: img.a1 },
        ],
      },
    ],
  },
  {
    id: "a-silent-bloom",
    slug: "silent-bloom",
    title: "Silent Bloom",
    description: "A florist who can hear plants discovers her shop sits above a centuries-old spirit contract.",
    longDescription: "Silent Bloom is a quiet, luminous supernatural anime about Mio, a young florist with an unusual gift. When strange clients begin arriving with stranger requests, she realizes her small shop is a waypoint between worlds. Equal parts cozy mystery and mythological deep-dive, with some of the most visually expressive backgrounds in recent anime.",
    type: "series",
    category: "Anime",
    genres: ["Anime", "Fantasy", "Mystery"],
    rating: "8.6",
    year: 2023,
    duration: "10 Episodes",
    country: "Japan",
    status: "Completed",
    heroImage: img.a2,
    posterImage: img.a4,
    backdropImage: img.a2,
    heroAlt: "Silent Bloom magical flower shop",
    posterAlt: "Silent Bloom poster",
    tags: ["Anime Picks", "Supernatural", "Cozy"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Mio Hana", role: "Mio", image: img.a4 },
      { name: "Rei Shiro", role: "Spirit Keeper", image: img.a2 },
      { name: "Asa Kuro", role: "Elder Root", image: img.a3 },
      { name: "Nano Tori", role: "Wanderer", image: img.a5 },
    ],
    seasons: [
      {
        id: "sb-anime-s1",
        name: "Season 1",
        episodes: [
          { id: "sb-a-s1e1", title: "First Petal", duration: "23m", synopsis: "A peculiar order arrives — flowers for someone who died forty years ago.", thumbnail: img.a2 },
          { id: "sb-a-s1e2", title: "Root Memories", duration: "22m", synopsis: "Mio follows a vine deep into the contract&#39;s original terms.", thumbnail: img.a4 },
          { id: "sb-a-s1e3", title: "The Long Arrangement", duration: "25m", synopsis: "A spirit client refuses to leave until her bouquet is perfect.", thumbnail: img.a2 },
        ],
      },
    ],
  },

  // ── DRAMA (4) ──────────────────────────────────────────────────
  {
    id: "d-fractured-vows",
    slug: "fractured-vows",
    title: "Fractured Vows",
    description: "A prestige family drama where public loyalty hides private wars.",
    longDescription: "When a celebrated political family prepares for an election-year succession, every dinner becomes a battleground. Fractured Vows combines emotional intensity with layered performances, charting the personal cost of ambition under constant public scrutiny. A slow-burn masterpiece of Korean prestige drama.",
    type: "series",
    category: "Drama",
    genres: ["Drama", "Romance", "Political"],
    rating: "8.5",
    year: 2022,
    duration: "16 Episodes",
    country: "Korea",
    status: "Completed",
    heroImage: img.a2,
    posterImage: img.a2,
    backdropImage: img.a2,
    heroAlt: "Fractured Vows dramatic backdrop",
    posterAlt: "Fractured Vows poster",
    tags: ["Drama Series", "Award Winner", "Binge"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Yuna Park", role: "Seo Rin", image: img.a2 },
      { name: "David Kwon", role: "Min Jae", image: img.a3 },
      { name: "Ira Song", role: "Chairwoman Han", image: img.a2 },
      { name: "Noah Lee", role: "Jun", image: img.a3 },
    ],
    seasons: [
      {
        id: "fv-s1",
        name: "Season 1",
        episodes: [
          { id: "fv-s1e1", title: "Inheritance", duration: "58m", synopsis: "An announcement at a gala sends the family into strategic chaos.", thumbnail: img.a2 },
          { id: "fv-s1e2", title: "Public Silence", duration: "61m", synopsis: "A leaked recording forces rival siblings into a temporary alliance.", thumbnail: img.a5 },
          { id: "fv-s1e3", title: "The Campaign", duration: "55m", synopsis: "A family vote reshapes the balance of power in the household.", thumbnail: img.a2 },
        ],
      },
      {
        id: "fv-s2",
        name: "Season 2",
        episodes: [
          { id: "fv-s2e1", title: "The Long Game", duration: "62m", synopsis: "Seo Rin maneuvers behind the scenes as election day approaches.", thumbnail: img.a2 },
          { id: "fv-s2e2", title: "Blindsided", duration: "59m", synopsis: "An unexpected alliance threatens to fracture the family for good.", thumbnail: img.a5 },
        ],
      },
    ],
  },
  {
    id: "d-second-bloom",
    slug: "second-bloom",
    title: "Second Bloom",
    description: "A florist in her forties rebuilds life — and unexpectedly finds love for the second time.",
    longDescription: "After a decade managing a successful florist shop and an equally successful facade of being fine, Hana decides to stop pretending. Second Bloom is a grounded, warm Korean drama about what it means to start over when the world has already moved on — told with restraint, humor, and deeply felt performances.",
    type: "series",
    category: "Drama",
    genres: ["Drama", "Romance"],
    rating: "8.7",
    year: 2023,
    duration: "12 Episodes",
    country: "Korea",
    status: "Completed",
    heroImage: img.a2,
    posterImage: img.a4,
    backdropImage: img.a2,
    heroAlt: "Second Bloom drama still",
    posterAlt: "Second Bloom poster",
    tags: ["Drama Series", "Romance", "Fan Favorite"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Song Hana", role: "Hana", image: img.a2 },
      { name: "Kwon Soo", role: "Jae-won", image: img.a3 },
      { name: "Lee Minji", role: "Soo-ah", image: img.a2 },
      { name: "Park Yeol", role: "Manager Choi", image: img.a3 },
    ],
    seasons: [
      {
        id: "sb-d-s1",
        name: "Season 1",
        episodes: [
          { id: "sb-d-s1e1", title: "The Shop Opens", duration: "50m", synopsis: "Hana agrees to an arrangement she knows is temporary.", thumbnail: img.a2 },
          { id: "sb-d-s1e2", title: "New Orders", duration: "53m", synopsis: "A familiar face returns with expensive taste and too many questions.", thumbnail: img.a4 },
          { id: "sb-d-s1e3", title: "In Season", duration: "48m", synopsis: "The bloom festival brings the whole neighborhood together for one night.", thumbnail: img.a2 },
        ],
      },
    ],
  },
  {
    id: "d-before-the-rain",
    slug: "before-the-rain",
    title: "Before the Rain",
    description: "A Thai drama about three generations of women navigating duty, desire, and memory in Chiang Mai.",
    longDescription: "Spanning sixty years through photographs, recipes, and a house that refuses to be sold, Before the Rain traces the interlinked lives of a grandmother, mother, and daughter each at a pivotal crossroads. It is a quiet, devastating, and ultimately hopeful drama — one of the most accomplished productions to emerge from Thailand in the last decade.",
    type: "series",
    category: "Drama",
    genres: ["Drama", "Romance", "Historical"],
    rating: "9.0",
    year: 2023,
    duration: "10 Episodes",
    country: "Thailand",
    status: "Completed",
    heroImage: img.a4,
    posterImage: img.a1,
    backdropImage: img.a4,
    heroAlt: "Before the Rain Chiang Mai golden hour",
    posterAlt: "Before the Rain poster",
    tags: ["Thai Drama", "Award Winner", "Fan Favorite"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Nida Araya", role: "Grandmother Mae", image: img.a1 },
      { name: "Ploy Sirin", role: "Mother Nara", image: img.a2 },
      { name: "Jane Mila", role: "Daughter Pim", image: img.a4 },
      { name: "Chai Tanit", role: "Uncle Ek", image: img.a3 },
    ],
    seasons: [
      {
        id: "btr-s1",
        name: "Season 1",
        episodes: [
          { id: "btr-s1e1", title: "The House", duration: "52m", synopsis: "Pim returns to sell the family home and finds she can&#39;t leave.", thumbnail: img.a4 },
          { id: "btr-s1e2", title: "Mae&#39;s Garden", duration: "49m", synopsis: "A box of old photographs changes everything Pim thought she knew.", thumbnail: img.a1 },
          { id: "btr-s1e3", title: "The Season It Rained", duration: "56m", synopsis: "The monsoon brings a stranger who knew the grandmother&#39;s first name.", thumbnail: img.a4 },
        ],
      },
    ],
  },
  {
    id: "d-glass-meridian",
    slug: "glass-meridian",
    title: "Glass Meridian",
    description: "A surgeon and a detective solve crimes that only make sense inside operating rooms.",
    longDescription: "Glass Meridian is a stylish, fast-paced Korean drama that mixes medical procedural with locked-room mystery. Each episode presents a new case that crosses both their jurisdictions — and slowly unravels a larger conspiracy connecting the hospital, the police unit, and the city's most powerful private health fund.",
    type: "series",
    category: "Drama",
    genres: ["Drama", "Mystery", "Thriller"],
    rating: "8.6",
    year: 2024,
    duration: "14 Episodes",
    country: "Korea",
    status: "Ongoing",
    heroImage: img.a3,
    posterImage: img.a2,
    backdropImage: img.a3,
    heroAlt: "Glass Meridian hospital interior",
    posterAlt: "Glass Meridian poster",
    tags: ["Medical Drama", "Mystery", "Trending"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Soo Jin", role: "Dr. Ara", image: img.a2 },
      { name: "Kang Hyo", role: "Detective Won", image: img.a3 },
      { name: "Park Sol", role: "Nurse Dae", image: img.a4 },
      { name: "Min Rae", role: "Director Lim", image: img.a5 },
    ],
    seasons: [
      {
        id: "gm-s1",
        name: "Season 1",
        episodes: [
          { id: "gm-s1e1", title: "The Admission", duration: "53m", synopsis: "A patient dies in a sealed room. The only witness is still under anesthesia.", thumbnail: img.a3 },
          { id: "gm-s1e2", title: "Vitals", duration: "50m", synopsis: "A second case points back to the first — through a shared blood type.", thumbnail: img.a2 },
          { id: "gm-s1e3", title: "Anesthesia", duration: "55m", synopsis: "The detective operates without authorization. The surgeon stitches it together.", thumbnail: img.a3 },
        ],
      },
    ],
  },

  // ── VARIETY (3) ──────────────────────────────────────────────────
  {
    id: "v-night-shift-live",
    slug: "night-shift-live",
    title: "Night Shift Live",
    description: "A fast-paced variety format where artists, actors, and creators collide after midnight.",
    longDescription: "Part performance showcase, part spontaneous challenge series, Night Shift Live turns every episode into a surprise event. With polished sets, rotating hosts, and unpredictable guests, it delivers a lighter premium counterbalance to the platform's dramatic lineup.",
    type: "series",
    category: "Variety",
    genres: ["Variety", "Music", "Talk"],
    rating: "8.1",
    year: 2024,
    duration: "8 Episodes",
    country: "Thailand",
    status: "Ongoing",
    heroImage: img.a5,
    posterImage: img.a5,
    backdropImage: img.a5,
    heroAlt: "Night Shift Live neon stage backdrop",
    posterAlt: "Night Shift Live poster",
    tags: ["Variety", "Live Energy", "Fresh"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Tao Minh", role: "Host", image: img.a5 },
      { name: "Rae Lin", role: "Guest Curator", image: img.a2 },
      { name: "Kris Sol", role: "Music Director", image: img.a3 },
      { name: "Mina Vo", role: "Producer", image: img.a5 },
    ],
    seasons: [
      {
        id: "nsl-s1",
        name: "Season 1",
        episodes: [
          { id: "nsl-s1e1", title: "Midnight Entrance", duration: "52m", synopsis: "A surprise collaboration turns the opening stage into an instant hit.", thumbnail: img.a5 },
          { id: "nsl-s1e2", title: "Speed Round", duration: "48m", synopsis: "Guests rotate through live challenges with barely any prep time.", thumbnail: img.a4 },
        ],
      },
    ],
  },
  {
    id: "v-field-trip",
    slug: "field-trip",
    title: "Field Trip",
    description: "Four K-pop idols navigate real-life travel challenges with no stylist, no manager, no GPS.",
    longDescription: "Strip away the stage and what do you get? Four idols dropped into a new destination with one backpack, one camera, and zero Wi-Fi. Field Trip is the variety format that proves the best content happens when nothing goes to plan. Warm, chaotic, and genuinely funny.",
    type: "series",
    category: "Variety",
    genres: ["Variety", "Travel", "Reality"],
    rating: "8.4",
    year: 2024,
    duration: "10 Episodes",
    country: "Korea",
    status: "Ongoing",
    heroImage: img.a4,
    posterImage: img.a3,
    backdropImage: img.a4,
    heroAlt: "Field Trip variety travel backdrop",
    posterAlt: "Field Trip variety poster",
    tags: ["Variety", "Fun", "Trending"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Jenna Sol", role: "Jenna (herself)", image: img.a3 },
      { name: "Bom Ki", role: "Bom (herself)", image: img.a2 },
      { name: "Rui Cha", role: "Rui (himself)", image: img.a3 },
      { name: "Dae Park", role: "Dae (himself)", image: img.a2 },
    ],
    seasons: [
      {
        id: "ft-s1",
        name: "Season 1",
        episodes: [
          { id: "ft-s1e1", title: "Lost in Osaka", duration: "48m", synopsis: "No translator. No data. Just four people and a very confusing train map.", thumbnail: img.a4 },
          { id: "ft-s1e2", title: "Chiang Mai on Two Dollars", duration: "46m", synopsis: "Budget day goes sideways immediately and beautifully.", thumbnail: img.a3 },
        ],
      },
    ],
  },
  {
    id: "v-backroom-pass",
    slug: "backroom-pass",
    title: "Backroom Pass",
    description: "Exclusive behind-the-scenes access to the people who make the platform's biggest productions.",
    longDescription: "Backroom Pass is a documentary variety hybrid that pulls the curtain back on streamXie originals — from casting to wrap party. Each episode follows a different production, with unprecedented access to directors, technical crews, and the decisions that shaped the final cut. Genuinely educational and consistently surprising.",
    type: "series",
    category: "Variety",
    genres: ["Variety", "Documentary", "Reality"],
    rating: "7.9",
    year: 2024,
    duration: "6 Episodes",
    country: "Korea",
    status: "Completed",
    heroImage: img.a1,
    posterImage: img.a2,
    backdropImage: img.a1,
    heroAlt: "Backroom Pass production behind scenes",
    posterAlt: "Backroom Pass poster",
    tags: ["Variety", "Documentary", "Original"],
    trailerUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    cast: [
      { name: "Min Hae", role: "Host (herself)", image: img.a2 },
      { name: "Sora Kim", role: "Director Feature", image: img.a3 },
      { name: "Dae Ro", role: "DOP Feature", image: img.a4 },
      { name: "Rae Sol", role: "Producer Feature", image: img.a5 },
    ],
    seasons: [
      {
        id: "bp-s1",
        name: "Season 1",
        episodes: [
          { id: "bp-s1e1", title: "Making Neon Citadel", duration: "45m", synopsis: "The production designer explains how a city was built inside a warehouse.", thumbnail: img.a1 },
          { id: "bp-s1e2", title: "The Amber Divide Shoots", duration: "42m", synopsis: "Six weeks on location. Four countries. One very small budget.", thumbnail: img.a2 },
        ],
      },
    ],
  },
];

// ── Featured (hero banner ─ 4 varied items) ─────────────────────
export const featuredItems = contentItems.filter((item) => item.featured);

// ── Carousels ────────────────────────────────────────────────────
export const trendingNow = [
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "m-neon-citadel")!,
  contentItems.find((c) => c.id === "a-iron-protocol")!,
  contentItems.find((c) => c.id === "s-amber-divide")!,
  contentItems.find((c) => c.id === "m-echo-requiem")!,
  contentItems.find((c) => c.id === "d-fractured-vows")!,
  contentItems.find((c) => c.id === "m-last-meridian")!,
  contentItems.find((c) => c.id === "s-moonlit-protocol")!,
  contentItems.find((c) => c.id === "d-before-the-rain")!,
  contentItems.find((c) => c.id === "a-skyward-embers")!,
];

export const newReleases = [
  contentItems.find((c) => c.id === "m-echo-requiem")!,
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "s-hollow-station")!,
  contentItems.find((c) => c.id === "m-neon-citadel")!,
  contentItems.find((c) => c.id === "v-field-trip")!,
  contentItems.find((c) => c.id === "a-silent-bloom")!,
  contentItems.find((c) => c.id === "m-pale-signal")!,
  contentItems.find((c) => c.id === "d-glass-meridian")!,
];

export const animePicks = [
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "a-iron-protocol")!,
  contentItems.find((c) => c.id === "a-skyward-embers")!,
  contentItems.find((c) => c.id === "a-silent-bloom")!,
];

export const dramaSeries = [
  contentItems.find((c) => c.id === "d-fractured-vows")!,
  contentItems.find((c) => c.id === "d-second-bloom")!,
  contentItems.find((c) => c.id === "d-before-the-rain")!,
  contentItems.find((c) => c.id === "d-glass-meridian")!,
  contentItems.find((c) => c.id === "s-the-long-run")!,
  contentItems.find((c) => c.id === "s-amber-divide")!,
];

export const moviesCollection = [
  contentItems.find((c) => c.id === "m-neon-citadel")!,
  contentItems.find((c) => c.id === "m-echo-requiem")!,
  contentItems.find((c) => c.id === "m-violet-coast")!,
  contentItems.find((c) => c.id === "m-last-meridian")!,
  contentItems.find((c) => c.id === "m-pale-signal")!,
];

export const continueWatchingCollection = [
  contentItems.find((c) => c.id === "s-moonlit-protocol")!,
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "d-fractured-vows")!,
  contentItems.find((c) => c.id === "a-iron-protocol")!,
  contentItems.find((c) => c.id === "s-amber-divide")!,
];

export const recommendations = [
  contentItems.find((c) => c.id === "m-echo-requiem")!,
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "m-last-meridian")!,
  contentItems.find((c) => c.id === "a-skyward-embers")!,
  contentItems.find((c) => c.id === "d-second-bloom")!,
  contentItems.find((c) => c.id === "m-violet-coast")!,
  contentItems.find((c) => c.id === "s-hollow-station")!,
  contentItems.find((c) => c.id === "d-before-the-rain")!,
];

export const topTenToday = [
  contentItems.find((c) => c.id === "a-ghost-frequency")!,
  contentItems.find((c) => c.id === "m-neon-citadel")!,
  contentItems.find((c) => c.id === "a-iron-protocol")!,
  contentItems.find((c) => c.id === "a-skyward-embers")!,
  contentItems.find((c) => c.id === "m-echo-requiem")!,
  contentItems.find((c) => c.id === "d-fractured-vows")!,
  contentItems.find((c) => c.id === "m-last-meridian")!,
  contentItems.find((c) => c.id === "s-moonlit-protocol")!,
  contentItems.find((c) => c.id === "d-second-bloom")!,
  contentItems.find((c) => c.id === "m-violet-coast")!,
];

export const popularKeywords = [
  "Sci-Fi",
  "Political Drama",
  "Fantasy Adventure",
  "New Episodes",
  "Award Winners",
  "Cyberpunk",
  "Mecha",
  "Romance",
  "Thai Drama",
  "Mystery",
];

export const genres = ["Action", "Sci-Fi", "Drama", "Anime", "Fantasy", "Romance", "Mystery", "Variety", "Thriller", "Crime", "Historical", "Cyberpunk", "Travel", "Documentary", "Political", "Adventure"];
export const countries = ["Korea", "Japan", "Thailand"];
export const statuses = ["Released", "Ongoing", "Completed"];
export const years = ["2024", "2023", "2022"];
export const contentTypes = ["Movies", "Series", "Anime", "Drama", "Variety"];
export const sortOptions = ["Popularity", "Latest", "Rating"];
